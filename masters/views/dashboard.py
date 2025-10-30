# masters/views/dashboard.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.utils import timezone
from django.db.models import Count, Avg, Sum, Q
from ..utils.roles import user_role  # ✅ source unique pour le rôle

# ====== MODELS (Master) ======
from ..models import (
    MasterProgram, Cohort, Semester, ModuleUE,
    MasterEnrollment, InstructorAssignment,
    Assignment, Submission,
    Exam, ExamGrade,
    LessonProgress, ModuleProgress,
    SemesterResult,
)

# ====== MODELS (autres apps utilisées) ======
try:
    from programs.models import Program
except Exception:  # si l'app n'est pas chargée en migration
    Program = None


# ============================================================
# CONFIG SECTIONS PAR RÔLE
# ============================================================
SECTIONS_BY_ROLE = {
    "student": {
        "overview": ("Aperçu", {"student"}),
        "courses": ("Mes Cours", {"student"}),
        "assignments": ("Devoirs", {"student"}),
        "exams": ("Examens", {"student"}),
        "results": ("Résultats", {"student"}),
        "messages": ("Messagerie", {"student"}),
        "settings": ("Paramètres", {"student"}),
    },
    "instructor": {
        "overview": ("Aperçu", {"instructor"}),
        "teaching": ("Enseignements", {"instructor"}),
        "assignments": ("Devoirs", {"instructor"}),
        "exams": ("Examens", {"instructor"}),
        "results": ("Résultats", {"instructor"}),
        "messages": ("Messagerie", {"instructor"}),
        "settings": ("Paramètres", {"instructor"}),
    },
    "staff_admin": {
        "overview": ("Aperçu", {"staff_admin"}),
        "manage": ("Gestion (Staff)", {"staff_admin"}),
        "finance": ("Finances", {"staff_admin"}),  # ⚠️ placeholder (à brancher à ton app finance)
        "stats": ("Statistiques", {"staff_admin"}),
        "settings": ("Paramètres", {"staff_admin"}),
    },
    "master": {  # super-vision (fallback)
        "overview": ("Aperçu", {"student", "instructor", "staff_admin"}),
        "teaching": ("Enseignements", {"instructor"}),
        "manage": ("Gestion (Staff)", {"staff_admin"}),
        "exams": ("Examens", {"student", "instructor", "staff_admin"}),
        "results": ("Résultats", {"student", "staff_admin"}),
        "settings": ("Paramètres", {"student", "instructor", "staff_admin"}),
    },
}


def _default_section_for(role: str) -> str:
    return {
        "student": "overview",
        "instructor": "teaching",
        "staff_admin": "manage",
        "master": "overview",
    }.get(role, "overview")


# ============================================================
# HELPERS DE CONTEXTE
# ============================================================
def _active_enrollment_for(user):
    """Retourne la dernière inscription Master ACTIVE de l'étudiant, sinon None."""
    return (
        MasterEnrollment.objects
        .select_related("program", "cohort")
        .filter(student=user, status="ACTIVE")
        .order_by("-created_at")
        .first()
    )


def _student_context(user):
    """Construit un contexte riche pour l'étudiant connecté."""
    enrollment = _active_enrollment_for(user)
    if not enrollment:
        return {"enrollment": None}

    # Modules du programme
    modules = (
        ModuleUE.objects.filter(
            semester__program=enrollment.program,
            is_active=True
        )
        .select_related("semester")
        .order_by("semester__order", "order", "id")
    )

    # Progression
    module_progress_qs = ModuleProgress.objects.filter(enrollment=enrollment)
    progress_map = {p.module_id: float(p.percent) for p in module_progress_qs}
    progress_percent = round(
        sum(progress_map.values()) / len(progress_map), 2
    ) if progress_map else 0.0

    # Devoirs + soumissions
    assignments = (
        Assignment.objects.filter(
            module__in=modules,
            is_published=True
        )
        .order_by("-created_at")
    )
    submissions_map = {
        s.assignment_id: s
        for s in Submission.objects.filter(student=user, assignment__in=assignments)
    }

    # Examens + notes
    exams = (
        Exam.objects.filter(
            semester__program=enrollment.program,
            is_published=True
        )
        .select_related("semester")
        .order_by("-start_at")
    )
    grades_map = {
        g.exam_id: g
        for g in ExamGrade.objects.filter(student=user, exam__in=exams)
    }

    # Résultats consolidés
    results = (
        SemesterResult.objects
        .filter(enrollment=enrollment)
        .select_related("semester")
        .order_by("semester__order")
    )
    moyenne_generale = results.aggregate(avg=Avg("average_20"))["avg"] or 0.0
    credits_total = results.aggregate(total=Sum("credits_earned"))["total"] or 0.0

    # Prochains événements utiles
    now = timezone.now()
    assignments_open = assignments.filter(
        Q(open_at__isnull=True) | Q(open_at__lte=now),
        Q(close_at__isnull=True) | Q(close_at__gte=now)
    )[:10]
    upcoming_exams = exams.filter(start_at__gt=now).order_by("start_at")[:10]

    return {
        "enrollment": enrollment,
        "modules": modules,
        "progress_percent": progress_percent,
        "module_progress_map": progress_map,

        "assignments": assignments[:50],
        "assignments_open": assignments_open,
        "submissions_map": submissions_map,

        "exams": exams[:50],
        "upcoming_exams": upcoming_exams,
        "grades_map": grades_map,

        "results": results,
        "moyenne_generale": round(float(moyenne_generale), 2),
        "credits_total": round(float(credits_total), 2),
    }


def _instructor_context(user):
    """Construit un contexte riche pour l'enseignant connecté."""
    # Affectations ↔ modules
    teachings = (
        InstructorAssignment.objects
        .filter(instructor=user, is_active=True)
        .select_related("module", "module__semester", "module__semester__program")
        .order_by("module__semester__order", "module__order")
    )
    modules = [t.module for t in teachings]

    # Devoirs du prof
    assignments = (
        Assignment.objects
        .filter(module__in=modules)
        .order_by("-created_at")
    )

    # Soumissions à corriger
    pending_submissions = (
        Submission.objects
        .filter(assignment__in=assignments, status__in=["SUBMITTED", "LATE"])
        .select_related("assignment", "student")
        .order_by("-submitted_at")
    )

    # Examens du périmètre prof (semestres des modules)
    sem_ids = {m.semester_id for m in modules}
    exams = (
        Exam.objects.filter(semester_id__in=sem_ids, is_published=True)
        .select_related("semester")
        .order_by("-start_at")
    )

    # Stats rapides
    courses_count = len(modules)
    assignments_count = assignments.count()
    to_grade_count = pending_submissions.count()
    students_count = (
        MasterEnrollment.objects
        .filter(program__in=Program.objects.filter(cycle="MASTER"))  # périmètre master
        .values("student").distinct().count()
    ) if Program else 0

    return {
        "teachings": teachings,         # liste d'affectations (avec module)
        "modules": modules,             # liste de ModuleUE
        "assignments": assignments[:50],
        "pending_submissions": pending_submissions[:50],
        "exams": exams[:50],

        "courses_count": courses_count,
        "assignments_count": assignments_count,
        "to_grade_count": to_grade_count,
        "students_count": students_count,
    }


def _staff_context(user):
    """Contexte générique Staff Admin (hors Directeur)."""
    # KPIs généraux Master
    nb_programs_master = (
        Program.objects.filter(cycle="MASTER").count()
        if Program else 0
    )
    nb_semesters = Semester.objects.count()
    nb_modules = ModuleUE.objects.count()
    nb_students = MasterEnrollment.objects.values("student").distinct().count()
    nb_enrollments = MasterEnrollment.objects.count()
    nb_teachers = InstructorAssignment.objects.values("instructor").distinct().count()
    nb_exams = Exam.objects.count()

    last_exams = Exam.objects.order_by("-start_at")[:8]
    last_assignments = Assignment.objects.order_by("-created_at")[:8]

    # Résultats (récents)
    last_results = (
        SemesterResult.objects
        .select_related("enrollment__student", "semester__program")
        .order_by("-computed_at")[:12]
    )

    # Placeholders Finance/Stats (à relier à ton app finance)
    finance_summary = {
        "paid_total": None,
        "unpaid_total": None,
        "pending_salary": None,
    }

    return {
        "nb_programs_master": nb_programs_master,
        "nb_semesters": nb_semesters,
        "nb_modules": nb_modules,
        "nb_students": nb_students,
        "nb_enrollments": nb_enrollments,
        "nb_teachers": nb_teachers,
        "nb_exams": nb_exams,

        "last_exams": last_exams,
        "last_assignments": last_assignments,
        "last_results": last_results,

        "finance_summary": finance_summary,
    }


def _director_context(user):
    """Contexte pour Directeur des Études (vision globale Master)."""
    ctx = _staff_context(user)

    # + extras directeur : répartition par programme / cohortes / modules
    by_program = (
        Program.objects.filter(cycle="MASTER")
        .annotate(
            semesters_count=Count("master_semesters", distinct=True),
            modules_count=Count("master_semesters__modules", distinct=True),
            students_count=Count("master_enrollments", distinct=True),
        ).order_by("title")
        if Program else []
    )

    top_modules_by_assignments = (
        ModuleUE.objects
        .annotate(assignments_count=Count("assignments"))
        .order_by("-assignments_count", "code")[:10]
    )

    exam_load = (
        Exam.objects
        .values("semester__name")
        .annotate(cnt=Count("id"))
        .order_by("semester__name")
    )

    # Taux de réussite approximatif (si computed_at rempli + decision)
    total_results = SemesterResult.objects.exclude(decision__isnull=True).count()
    admitted = SemesterResult.objects.filter(decision="ADM").count()
    success_rate = round((admitted / total_results) * 100.0, 2) if total_results else 0.0

    ctx.update({
        "programs_breakdown": by_program,
        "top_modules_by_assignments": top_modules_by_assignments,
        "exam_load": exam_load,
        "success_rate": success_rate,
    })
    return ctx


# ============================================================
# ROUTER PRINCIPAL
# ============================================================
@login_required
def dashboard_router(request):
    """
    Redirige l'utilisateur vers le dashboard correspondant à son rôle.
    """
    role = user_role(request.user)
    view = request.GET.get("view", "")

    if role == "student" and view not in ("", "student"):
        return redirect("masters:student_dashboard")
    if role == "instructor" and view not in ("", "teacher"):
        return redirect("masters:teacher_dashboard")
    if role == "staff_admin" and view not in ("", "staff", "director"):
        return redirect("masters:staff_dashboard")

    if role == "student":
        return student_dashboard(request)
    if role == "instructor":
        return teacher_dashboard(request)
    if role == "staff_admin":
        # détection sous-rôle directeur
        staff_role = (getattr(request.user, "role", "") or "").upper().strip()
        group_names = {g.name.lower() for g in request.user.groups.all()}
        is_director = (
            staff_role in {
                "DIRECTEUR_ETUDES", "DIRECTEUR D'ÉTUDES",
                "DIRECTEUR DES ETUDES", "DIRECTEUR"
            } or "directeur" in group_names
        )
        return director_dashboard(request) if is_director else staff_dashboard(request)

    # fallback
    return render(request, "masters/dashboard.html", {"role": role})


dashboard_home = dashboard_router  # alias compatibilité


# ============================================================
# DASHBOARD ÉTUDIANT
# ============================================================
@login_required
def student_dashboard(request):
    role = user_role(request.user)
    if role != "student":
        return dashboard_router(request)

    sections = SECTIONS_BY_ROLE["student"]
    section = request.GET.get("section", _default_section_for("student"))
    if section not in sections:
        section = _default_section_for("student")

    student_ctx = _student_context(request.user)
    if not student_ctx.get("enrollment"):
        return render(request, "masters/dashboard_student.html", {
            "role": role,
            "sections": sections,
            "active_section": section,
            "error": "Aucune inscription Master active trouvée.",
        })

    context = {
        "role": role,
        "sections": sections,
        "active_section": section,
        **student_ctx,
    }
    return render(request, "masters/dashboard_student.html", context)


# ============================================================
# DASHBOARD ENSEIGNANT
# ============================================================
@login_required
def teacher_dashboard(request):
    role = user_role(request.user)
    if role != "instructor":
        return dashboard_router(request)

    sections = SECTIONS_BY_ROLE["instructor"]
    section = request.GET.get("section", _default_section_for("instructor"))
    if section not in sections:
        section = _default_section_for("instructor")

    teacher_ctx = _instructor_context(request.user)
    context = {
        "role": role,
        "sections": sections,
        "active_section": section,
        **teacher_ctx,
    }
    return render(request, "masters/dashboard_teacher.html", context)


# ============================================================
# DASHBOARD STAFF (générique)
# ============================================================
@login_required
def staff_dashboard(request):
    role = user_role(request.user)
    if role != "staff_admin":
        return dashboard_router(request)

    sections = SECTIONS_BY_ROLE["staff_admin"]
    section = request.GET.get("section", _default_section_for("staff_admin"))
    if section not in sections:
        section = _default_section_for("staff_admin")

    staff_ctx = _staff_context(request.user)
    context = {
        "role": role,
        "sections": sections,
        "active_section": section,
        **staff_ctx,
        "cards": [
            {"title": "Étudiants actifs", "value": staff_ctx.get("nb_students", "—")},
            {"title": "Programmes (Master)", "value": staff_ctx.get("nb_programs_master", "—")},
            {"title": "Examens à venir", "value": Exam.objects.filter(start_at__gt=timezone.now()).count()},
        ],
    }
    return render(request, "masters/dashboard.html", context)


# ============================================================
# DASHBOARD DIRECTEUR DES ÉTUDES
# ============================================================
@login_required
def director_dashboard(request):
    role = user_role(request.user)
    if role != "staff_admin":
        return dashboard_router(request)

    staff_role = (getattr(request.user, "role", "") or "").upper().strip()
    group_names = {g.name.lower() for g in request.user.groups.all()}
    is_director = (
        staff_role in {
            "DIRECTEUR_ETUDES", "DIRECTEUR D'ÉTUDES",
            "DIRECTEUR DES ETUDES", "DIRECTEUR"
        } or "directeur" in group_names
    )
    if not is_director:
        return redirect("masters:staff_dashboard")

    sections = {
        "overview": ("Aperçu", {"staff_admin"}),
        "teachers": ("Enseignants", {"staff_admin"}),
        "students": ("Étudiants", {"staff_admin"}),
        "programs": ("Programmes", {"staff_admin"}),
        "exams": ("Examens", {"staff_admin"}),
        "results": ("Résultats", {"staff_admin"}),
        "stats": ("Statistiques", {"staff_admin"}),
        "settings": ("Paramètres", {"staff_admin"}),
    }
    section = request.GET.get("section", "overview")
    if section not in sections:
        section = "overview"

    director_ctx = _director_context(request.user)
    context = {
        "role": role,
        "sections": sections,
        "active_section": section,
        **director_ctx,
    }
    return render(request, "masters/dashboard_director.html", context)
