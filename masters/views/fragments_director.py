# masters/views/fragments_director.py
from __future__ import annotations
from typing import Dict, Any, Optional, Tuple, Iterable, List

import logging

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseBadRequest
from django.template.loader import render_to_string
from django.utils import timezone
from django.db.models import (
    Count, Avg, Sum, Q, Prefetch
)
from django.shortcuts import get_object_or_404

from ..utils.roles import user_role
from ..models import (
    MasterProgram, Cohort, Semester, ModuleUE,
    Chapter, Lesson,
    MasterEnrollment, InstructorAssignment,
    Assignment, Submission,
    Exam, ExamGrade,
    LessonProgress, ModuleProgress,
    SemesterResult,
)

# ===== Logger ================================================================
logger = logging.getLogger(__name__)

# --- App externe optionnelle (comme dans ton code) ---
try:
    from programs.models import Program
except Exception:
    Program = None


# ============================================================================
# 🔧 UTILITAIRES GÉNÉRAUX (Pagination, rendu, parsing)
# ============================================================================
def _render_fragment(request, template_path: str, ctx: Optional[Dict[str, Any]] = None) -> HttpResponse:
    """
    Rend un template partiel (fragment HTML) en réponse Http.
    Compatible avec ta mécanique JS (fetch + innerHTML + Preline/Alpine).
    """
    try:
        html = render_to_string(template_path, ctx or {}, request=request)
        return HttpResponse(html)
    except Exception as e:
        logger.exception(f"[DirectorFragment] Erreur de rendu pour '{template_path}': {e}")
        return HttpResponseBadRequest(f"Erreur de chargement du fragment.")

def _is_director(user) -> bool:
    """
    Vérifie que l’utilisateur est Directeur des Études / staff_admin (comme ton routeur).
    - Rôle explicite,
    - ou appartenance à un groupe.
    """
    if not user or not user.is_authenticated:
        return False
    if getattr(user, "is_superuser", False):
        return True

    role = (user_role(user) or "").lower().strip()
    if role in {"directeur", "directeur_etudes", "staff_admin"}:
        return True

    try:
        names = {g.name.lower() for g in user.groups.all()}
        if "directeur" in names or "staff_admin" in names:
            return True
    except Exception:
        pass
    return False

def _get_int(request, name: str, default: Optional[int] = None) -> Optional[int]:
    val = request.GET.get(name)
    if val is None or val == "":
        return default
    try:
        return int(str(val).strip())
    except Exception:
        return default

def _get_str(request, name: str, default: str = "") -> str:
    val = (request.GET.get(name) or "").strip()
    return val if val else default

def _paginate(qs, page: int, page_size: int) -> Tuple[Iterable, Dict[str, Any]]:
    """
    Pagination simple, côté serveur, sans dépendance externe.
    Renvoie (items, meta)
    meta: {page, page_size, total, pages, has_next, has_prev}
    """
    # Supporte QuerySet et list
    total = qs.count() if hasattr(qs, "count") else len(qs)  # type: ignore
    page = max(1, page or 1)
    page_size = max(1, min(page_size or 20, 100))

    start = (page - 1) * page_size
    end = start + page_size
    # Slicing marche sur QuerySet et list
    items = qs[start:end]

    pages = (total // page_size) + (1 if total % page_size else 0)
    meta = {
        "page": page,
        "page_size": page_size,
        "total": total,
        "pages": pages,
        "has_next": page < pages,
        "has_prev": page > 1,
    }
    return items, meta


# ============================================================================
# 🧠 BLOCS DE CONTEXTE (Overview, Teachers, Students, …)
# ============================================================================
def _overview_context() -> Dict[str, Any]:
    """
    Statistiques globales pour le DDE.
    Compatible avec un composant Preline (cards KPI + chart).
    """
    nb_programs = Program.objects.filter(cycle="MASTER").count() if Program else 0
    nb_semesters = Semester.objects.count()
    nb_modules = ModuleUE.objects.count()
    nb_students = MasterEnrollment.objects.values("student").distinct().count()
    nb_teachers = InstructorAssignment.objects.values("instructor").distinct().count()
    nb_exams = Exam.objects.count()

    # Taux réussite approximatif (moyenne des moyennes, en attendant un calcul métier final)
    avg_success = SemesterResult.objects.aggregate(avg=Avg("average_20"))["avg"] or 0.0
    avg_success = round(float(avg_success), 2)

    # Top 8 modules par volume de devoirs (utile pour une table)
    # ⚠️ nécessite related_name="assignments" dans Assignment(module=...)
    top_modules = (
        ModuleUE.objects
        .annotate(assignments_count=Count("assignments"))
        .order_by("-assignments_count", "code")[:8]
    )

    # Charge d’examens par semestre (pour graph bar/pie)
    exam_load_qs = (
        Exam.objects
        .values("semester__name")
        .annotate(total=Count("id"))
        .order_by("semester__name")
    )
    exam_load = list(exam_load_qs)

    # Activité récente (exams & assignments & résultats)
    last_assignments = Assignment.objects.select_related("module").order_by("-created_at")[:6]
    last_exams = Exam.objects.select_related("semester").order_by("-start_at")[:6]
    last_results = (
        SemesterResult.objects
        .select_related("enrollment__student", "semester__program")
        .order_by("-computed_at")[:6]
    )

    return {
        "kpis": {
            "nb_programs": nb_programs,
            "nb_semesters": nb_semesters,
            "nb_modules": nb_modules,
            "nb_students": nb_students,
            "nb_teachers": nb_teachers,
            "nb_exams": nb_exams,
            "avg_success": avg_success,
        },
        "top_modules_by_assignments": top_modules,
        "exam_load": exam_load,
        "last_assignments": last_assignments,
        "last_exams": last_exams,
        "last_results": last_results,
    }

def _teachers_context(request) -> Dict[str, Any]:
    """
    Liste des enseignants (affectations), filtrable : search, program, cohort.
    Paginé.
    """
    search = _get_str(request, "q")
    program_id = _get_int(request, "program_id")
    cohort_id = _get_int(request, "cohort_id")
    page = _get_int(request, "page", 1)
    page_size = _get_int(request, "page_size", 20)

    qs = (
        InstructorAssignment.objects
        .select_related("instructor", "module", "module__semester", "module__semester__program")
        .filter(is_active=True)
    )

    if program_id:
        qs = qs.filter(module__semester__program_id=program_id)
    if cohort_id:
        qs = qs.filter(module__semester__cohort_id=cohort_id)

    if search:
        qs = qs.filter(
            Q(instructor__first_name__icontains=search) |
            Q(instructor__last_name__icontains=search) |
            Q(instructor__email__icontains=search) |
            Q(module__title__icontains=search) |
            Q(module__code__icontains=search)
        )

    qs = qs.order_by("instructor__last_name", "instructor__first_name", "module__code")
    items, meta = _paginate(qs, page, page_size)

    # programmes & cohortes (pour filtres dropdown)
    programs = Program.objects.filter(cycle="MASTER").order_by("title") if Program else []
    cohorts = Cohort.objects.order_by("-start_date")

    return {
        "assignments": items,
        "meta": meta,
        "programs": programs,
        "cohorts": cohorts,
        "filters": {"q": search, "program_id": program_id, "cohort_id": cohort_id},
    }

def _students_context(request) -> Dict[str, Any]:
    """
    Liste des étudiants Master (via MasterEnrollment), filtrable & paginé.
    """
    search = _get_str(request, "q")
    program_id = _get_int(request, "program_id")
    cohort_id = _get_int(request, "cohort_id")
    status = _get_str(request, "status")  # ACTIVE / SUSPENDED / WITHDRAWN / COMPLETED
    page = _get_int(request, "page", 1)
    page_size = _get_int(request, "page_size", 20)

    qs = (
        MasterEnrollment.objects
        .select_related("student", "program", "cohort")
        .order_by("student__last_name", "student__first_name")
    )
    if program_id:
        qs = qs.filter(program_id=program_id)
    if cohort_id:
        qs = qs.filter(cohort_id=cohort_id)
    if status:
        qs = qs.filter(status=status)

    if search:
        qs = qs.filter(
            Q(student__first_name__icontains=search) |
            Q(student__last_name__icontains=search) |
            Q(student__email__icontains=search)
        )

    items, meta = _paginate(qs, page, page_size)

    programs = Program.objects.filter(cycle="MASTER").order_by("title") if Program else []
    cohorts = Cohort.objects.order_by("-start_date")
    statuses = [("ACTIVE", "Actif"), ("SUSPENDED", "Suspendu"), ("WITHDRAWN", "Abandonné"), ("COMPLETED", "Terminé")]

    return {
        "enrollments": items,
        "meta": meta,
        "programs": programs,
        "cohorts": cohorts,
        "statuses": statuses,
        "filters": {"q": search, "program_id": program_id, "cohort_id": cohort_id, "status": status},
    }

def _programs_context(request) -> Dict[str, Any]:
    """
    Vue Programmes Master + Semestres (avec compteurs).
    """
    search = _get_str(request, "q")
    page = _get_int(request, "page", 1)
    page_size = _get_int(request, "page_size", 20)

    if Program:
        qs = (
            Program.objects.filter(cycle="MASTER")
            .annotate(
                semesters_count=Count("master_semesters", distinct=True),
                modules_count=Count("master_semesters__modules", distinct=True),
                students_count=Count("master_enrollments", distinct=True),
            )
            .order_by("title")
        )
        if search:
            qs = qs.filter(Q(title__icontains=search) | Q(code__icontains=search))
        items, meta = _paginate(qs, page, page_size)
    else:
        items, meta = [], {"page": 1, "page_size": 20, "total": 0, "pages": 0, "has_next": False, "has_prev": False}

    return {"programs": items, "meta": meta, "filters": {"q": search}}

def _modules_context(request) -> Dict[str, Any]:
    """
    Liste Modules UE (avec enseignants, semestre, programme), filtrable.
    """
    search = _get_str(request, "q")
    program_id = _get_int(request, "program_id")
    cohort_id = _get_int(request, "cohort_id")
    semester_id = _get_int(request, "semester_id")
    page = _get_int(request, "page", 1)
    page_size = _get_int(request, "page_size", 20)

    qs = (
        ModuleUE.objects
        .select_related("semester", "semester__program", "semester__cohort")
        .prefetch_related(
            Prefetch("instructors", queryset=InstructorAssignment.objects.select_related("instructor"))
        )
        .order_by("semester__order", "order", "id")
    )

    if program_id:
        qs = qs.filter(semester__program_id=program_id)
    if cohort_id:
        qs = qs.filter(semester__cohort_id=cohort_id)
    if semester_id:
        qs = qs.filter(semester_id=semester_id)

    if search:
        qs = qs.filter(
            Q(title__icontains=search) | Q(code__icontains=search) |
            Q(semester__name__icontains=search) | Q(semester__program__title__icontains=search)
        )

    items, meta = _paginate(qs, page, page_size)

    # Filtres
    programs = Program.objects.filter(cycle="MASTER").order_by("title") if Program else []
    cohorts = Cohort.objects.order_by("-start_date")
    semesters = Semester.objects.order_by("program_id", "order")

    return {
        "modules": items,
        "meta": meta,
        "programs": programs,
        "cohorts": cohorts,
        "semesters": semesters,
        "filters": {"q": search, "program_id": program_id, "cohort_id": cohort_id, "semester_id": semester_id},
    }

def _exams_context(request) -> Dict[str, Any]:
    """
    Examens (passés / à venir) + stats simples + filtres.
    """
    search = _get_str(request, "q")
    program_id = _get_int(request, "program_id")
    cohort_id = _get_int(request, "cohort_id")
    page = _get_int(request, "page", 1)
    page_size = _get_int(request, "page_size", 20)

    now = timezone.now()

    qs = (
        Exam.objects
        .select_related("semester", "semester__program", "semester__cohort")
        .order_by("-start_at")
    )

    if program_id:
        qs = qs.filter(semester__program_id=program_id)
    if cohort_id:
        qs = qs.filter(semester__cohort_id=cohort_id)
    if search:
        qs = qs.filter(Q(title__icontains=search) | Q(semester__name__icontains=search))

    items, meta = _paginate(qs, page, page_size)

    upcoming = [e for e in items if (e.start_at and e.start_at >= now)]
    past = [e for e in items if (not e.start_at) or (e.start_at < now)]

    programs = Program.objects.filter(cycle="MASTER").order_by("title") if Program else []
    cohorts = Cohort.objects.order_by("-start_date")

    return {
        "exams": items,
        "meta": meta,
        "upcoming": upcoming,
        "past": past,
        "programs": programs,
        "cohorts": cohorts,
        "filters": {"q": search, "program_id": program_id, "cohort_id": cohort_id},
    }

def _results_context(request) -> Dict[str, Any]:
    """
    Résultats par semestre, avec agrégations.
    Filtrable par programme, cohorte, décision.
    """
    program_id = _get_int(request, "program_id")
    cohort_id = _get_int(request, "cohort_id")
    decision = _get_str(request, "decision")  # ADM / AJ / RAT / EXC
    page = _get_int(request, "page", 1)
    page_size = _get_int(request, "page_size", 20)

    qs = (
        SemesterResult.objects
        .select_related("enrollment__student", "enrollment__program", "enrollment__cohort", "semester__program")
        .order_by("-computed_at", "semester__order")
    )

    if program_id:
        qs = qs.filter(enrollment__program_id=program_id)
    if cohort_id:
        qs = qs.filter(enrollment__cohort_id=cohort_id)
    if decision:
        qs = qs.filter(decision=decision)

    items, meta = _paginate(qs, page, page_size)

    # KPIs rapides
    total = qs.count()
    admitted = qs.filter(decision="ADM").count()
    success_rate = round((admitted / total) * 100.0, 2) if total else 0.0
    avg_global = qs.aggregate(avg=Avg("average_20"))["avg"] or 0.0

    programs = Program.objects.filter(cycle="MASTER").order_by("title") if Program else []
    cohorts = Cohort.objects.order_by("-start_date")
    decisions = [("ADM", "Admis"), ("AJ", "Ajourné"), ("RAT", "Rattrapage"), ("EXC", "Exclu")]

    return {
        "results": items,
        "meta": meta,
        "kpis": {"success_rate": success_rate, "avg_global": round(float(avg_global), 2)},
        "programs": programs,
        "cohorts": cohorts,
        "decisions": decisions,
        "filters": {"program_id": program_id, "cohort_id": cohort_id, "decision": decision},
    }

def _reports_context(request) -> Dict[str, Any]:
    """
    Espace Rapports (préparé pour lancer des exports via l’API que tu feras ensuite).
    On liste quelques rapports typiques + paramètres retenus.
    """
    program_id = _get_int(request, "program_id")
    cohort_id = _get_int(request, "cohort_id")
    semester_id = _get_int(request, "semester_id")

    programs = Program.objects.filter(cycle="MASTER").order_by("title") if Program else []
    cohorts = Cohort.objects.order_by("-start_date")
    semesters = Semester.objects.order_by("program_id", "order")

    reports = [
        {"key": "students_roster", "title": "Liste des étudiants (roster)", "desc": "par Programme/Cohorte"},
        {"key": "teachers_load", "title": "Charge des enseignants", "desc": "par Programme/Semestre"},
        {"key": "modules_matrix", "title": "Matrice Modules/UE", "desc": "avec coefficients & crédits"},
        {"key": "exams_schedule", "title": "Emploi du temps examens", "desc": "par Semestre"},
        {"key": "results_summary", "title": "Synthèse résultats", "desc": "moyennes, décisions, taux de réussite"},
    ]

    return {
        "reports": reports,
        "programs": programs,
        "cohorts": cohorts,
        "semesters": semesters,
        "filters": {"program_id": program_id, "cohort_id": cohort_id, "semester_id": semester_id},
    }

def _settings_context(request) -> Dict[str, Any]:
    """
    Paramètres avancés (placeholders) : année académique, coefficients, options rattrapage, etc.
    À brancher à tes modèles/flags quand tu veux.
    """
    options = {
        "default_ects_per_semester": 30,
        "rattrapage_take_max": True,
        "lock_policy": "manual",  # manual / auto-on-compute
        "grading_scale": "20",    # /100 /20, etc.
    }
    return {"options": options}


# ============================================================================
# 🔎 VUES DÉTAILLÉES (fiche prof, fiche étudiant, fiche module, fiche examen)
# ============================================================================
def _teacher_detail_context(assignment_id: Optional[int], instructor_id: Optional[int]) -> Dict[str, Any]:
    """
    Fiche enseignant (depuis une affectation ou directement l’utilisateur).
    Affiche ses modules, devoirs récents, examens liés.
    """
    ia = None
    teacher = None
    if assignment_id:
        ia = get_object_or_404(
            InstructorAssignment.objects.select_related("instructor", "module", "module__semester", "module__semester__program"),
            pk=assignment_id
        )
        teacher = ia.instructor
    elif instructor_id:
        ia = (
            InstructorAssignment.objects
            .select_related("instructor", "module", "module__semester", "module__semester__program")
            .filter(instructor_id=instructor_id, is_active=True)
            .order_by("module__semester__order", "module__order")
            .first()
        )
        teacher = ia.instructor if ia else None

    if not teacher:
        return {"teacher": None}

    teachings = (
        InstructorAssignment.objects
        .filter(instructor=teacher, is_active=True)
        .select_related("module", "module__semester", "module__semester__program")
        .order_by("module__semester__order", "module__order")
    )
    modules = [t.module for t in teachings]
    assignments = Assignment.objects.filter(module__in=modules).order_by("-created_at")[:20]
    sem_ids = {m.semester_id for m in modules}
    exams = Exam.objects.filter(semester_id__in=sem_ids).order_by("-start_at")[:20]

    return {"teacher": teacher, "teachings": teachings, "assignments": assignments, "exams": exams}

def _student_detail_context(enrollment_id: int) -> Dict[str, Any]:
    """
    Fiche étudiant : informations d’inscription + progression + derniers résultats.
    """
    enrollment = get_object_or_404(
        MasterEnrollment.objects.select_related("student", "program", "cohort"),
        pk=enrollment_id
    )
    # Progression modules
    progress_qs = ModuleProgress.objects.filter(enrollment=enrollment)
    progress_map = {p.module_id: float(p.percent or 0) for p in progress_qs}
    avg_progress = round(sum(progress_map.values()) / len(progress_map), 2) if progress_map else 0.0

    # Résultats
    results = (
        SemesterResult.objects
        .filter(enrollment=enrollment)
        .select_related("semester__program")
        .order_by("semester__order")
    )
    avg_values = [float(r.average_20) for r in results if r.average_20 is not None]
    moyenne_generale = round(sum(avg_values) / len(avg_values), 2) if avg_values else 0.0
    credits_total = sum(float(r.credits_earned or 0) for r in results)

    # Soumissions récentes
    submissions = (
        Submission.objects
        .filter(student=enrollment.student)
        .select_related("assignment", "assignment__module")
        .order_by("-submitted_at")[:20]
    )

    return {
        "enrollment": enrollment,
        "avg_progress": avg_progress,
        "moyenne_generale": moyenne_generale,
        "credits_total": credits_total,
        "results": results,
        "submissions": submissions,
    }

def _module_detail_context(module_id: int) -> Dict[str, Any]:
    """
    Fiche module : enseignants, chapitres/leçons, devoirs, examens liés au semestre.
    """
    module = get_object_or_404(
        ModuleUE.objects.select_related("semester", "semester__program", "semester__cohort"),
        pk=module_id
    )
    instructors = (
        InstructorAssignment.objects
        .filter(module=module, is_active=True)
        .select_related("instructor")
    )
    chapters = (
        Chapter.objects
        .filter(module=module)
        .prefetch_related("lessons")
        .order_by("order", "id")
    )
    assignments = Assignment.objects.filter(module=module).order_by("-created_at")[:20]
    exams = Exam.objects.filter(semester=module.semester).order_by("-start_at")[:20]

    return {
        "module": module,
        "instructors": instructors,
        "chapters": chapters,
        "assignments": assignments,
        "exams": exams,
    }

def _exam_detail_context(exam_id: int) -> Dict[str, Any]:
    """
    Fiche examen : métadonnées + dernières notes + distribution simple.
    """
    exam = get_object_or_404(
        Exam.objects.select_related("semester", "semester__program", "semester__cohort"),
        pk=exam_id
    )
    grades = (
        ExamGrade.objects
        .filter(exam=exam)
        .select_related("student")
        .order_by("-graded_at")[:200]
    )
    # Distribution simple (classes de 5 points)
    buckets = {"0-5": 0, "5-10": 0, "10-15": 0, "15-20": 0}
    for g in grades:
        n = float(g.note_20 or 0)
        if n < 5: buckets["0-5"] += 1
        elif n < 10: buckets["5-10"] += 1
        elif n < 15: buckets["10-15"] += 1
        else: buckets["15-20"] += 1

    return {"exam": exam, "grades": grades, "buckets": buckets}


# ============================================================================
# 🔁 ROUTER FRAGMENTS — Directeur des Études
# ============================================================================
@login_required
def director_fragment_switch(request, section: str) -> HttpResponse:
    """
    Router des fragments du Directeur des Études.
    Compatible Alpine + Preline + Tailwind, sans HTMX.
    Utilisation front :
      fetch(`/master/director/fragment/overview/`).then(html => ...)
    """
    if not _is_director(request.user):
        return HttpResponseBadRequest("⛔ Accès réservé au Directeur des Études.")

    templates = {
        "overview":  "masters/fragments/director/overview.html",
        "teachers":  "masters/fragments/director/teachers.html",
        "students":  "masters/fragments/director/students.html",
        "programs":  "masters/fragments/director/programs.html",
        "modules":   "masters/fragments/director/modules.html",
        "exams":     "masters/fragments/director/exams.html",
        "results":   "masters/fragments/director/results.html",
        "stats":   "masters/fragments/director/stats.html",
        "reports":   "masters/fragments/director/reports.html",
        "settings":  "masters/fragments/director/settings.html",

        # vues détaillées (fiches)
        "teacher_detail": "masters/fragments/director/teacher_detail.html",
        "student_detail": "masters/fragments/director/student_detail.html",
        "module_detail":  "masters/fragments/director/module_detail.html",
        "exam_detail":    "masters/fragments/director/exam_detail.html",
    }

    tpl = templates.get(section)
    if not tpl:
        return HttpResponseBadRequest("Section invalide")

    now = timezone.now()
    ctx: Dict[str, Any] = {"user": request.user, "now": now, "section": section}
    logger.debug(f"[DirectorFragment] Chargement section='{section}' par user='{request.user}'")

    # --- Sections principales ---
    if section == "overview":
        ctx.update(_overview_context())

    elif section == "teachers":
        ctx.update(_teachers_context(request))

    elif section == "students":
        ctx.update(_students_context(request))

    elif section == "programs":
        ctx.update(_programs_context(request))

    elif section == "modules":
        ctx.update(_modules_context(request))

    elif section == "exams":
        ctx.update(_exams_context(request))

    elif section == "results":
        ctx.update(_results_context(request))

    elif section == "reports":
        ctx.update(_reports_context(request))

    elif section == "settings":
        ctx.update(_settings_context(request))

    # --- Vues détaillées (fiches) ---
    elif section == "teacher_detail":
        assignment_id = _get_int(request, "assignment_id")
        instructor_id = _get_int(request, "instructor_id")
        ctx.update(_teacher_detail_context(assignment_id, instructor_id))

    elif section == "student_detail":
        enrollment_id = _get_int(request, "enrollment_id")
        if not enrollment_id:
            return HttpResponseBadRequest("Paramètre 'enrollment_id' manquant.")
        ctx.update(_student_detail_context(enrollment_id))

    elif section == "module_detail":
        module_id = _get_int(request, "module_id")
        if not module_id:
            return HttpResponseBadRequest("Paramètre 'module_id' manquant.")
        ctx.update(_module_detail_context(module_id))

    elif section == "exam_detail":
        exam_id = _get_int(request, "exam_id")
        if not exam_id:
            return HttpResponseBadRequest("Paramètre 'exam_id' manquant.")
        ctx.update(_exam_detail_context(exam_id))

    elif section == "stats":
        """
        Section Statistiques — Vue métier Directeur des Études.
        Affiche les indicateurs clés : étudiants, enseignants, examens, taux de réussite, etc.
        """
        from django.db.models import Count, Avg

        # Indicateurs principaux
        nb_students = MasterEnrollment.objects.count()
        nb_teachers = InstructorAssignment.objects.values("instructor").distinct().count()
        nb_modules = ModuleUE.objects.count()
        nb_exams = Exam.objects.count()

        # Moyenne de réussite (basée sur les résultats de semestre)
        avg_success = SemesterResult.objects.aggregate(avg=Avg("average_20"))["avg"] or 0
        avg_success = round(float(avg_success), 2)

        # Répartition des examens par semestre
        exams_by_semester = (
            Exam.objects.values("semester__name")
            .annotate(total=Count("id"))
            .order_by("semester__order")
        )

        # Top 5 modules les plus enseignés
        top_modules = (
            ModuleUE.objects.annotate(nb_assignments=Count("assignments"))
            .order_by("-nb_assignments")[:5]
        )

        ctx.update({
            "nb_students": nb_students,
            "nb_teachers": nb_teachers,
            "nb_modules": nb_modules,
            "nb_exams": nb_exams,
            "avg_success": avg_success,
            "exams_by_semester": exams_by_semester,
            "top_modules": top_modules,
        })
    elif section == "reports":
        """
        Section Rapports — Vue métier Directeur des Études.
        Permet d’exporter les statistiques ou données académiques.
        """
        from django.db.models import Count, Avg

        # Récapitulatif général pour le rapport
        programs = (
            ModuleUE.objects.values("semester__program__title")
            .annotate(nb_modules=Count("id"))
            .order_by("semester__program__title")
        )

        avg_per_program = (
            SemesterResult.objects.values("semester__program__title")
            .annotate(avg_result=Avg("average_20"))
            .order_by("semester__program__title")
        )

        recent_exams = Exam.objects.order_by("-start_at")[:10]

        ctx.update({
            "programs": programs,
            "avg_per_program": avg_per_program,
            "recent_exams": recent_exams,
        })


    return _render_fragment(request, tpl, ctx)
