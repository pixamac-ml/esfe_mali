# masters/views/api.py
import json
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Prefetch, Avg
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST

from ..models import (
    CYCLE_MASTER,
    LessonProgress, Submission, Assignment, MasterEnrollment,
    ModuleUE, Chapter, Lesson, Semester, InstructorAssignment,
    Exam, ExamGrade, SemesterResult,
)
from ..utils.roles import user_role


# ==========================================================
# 🔧 UTILS GLOBAUX
# ==========================================================
def _json(request):
    """Convertit le corps JSON d'une requête en dict Python."""
    try:
        return json.loads(request.body.decode("utf-8"))
    except Exception:
        return {}


def _is_student(user):
    return (user_role(user) or "").lower() == "student"


def _is_instructor(user):
    role = (user_role(user) or "").lower()
    return role in {"instructor", "enseignant", "teacher", "prof", "professeur"}


def _is_director(user):
    role = (user_role(user) or "").lower()
    return role in {"directeur", "directeur_etudes", "staff_admin"}


# ==========================================================
# 🎓 API ÉTUDIANT — progression & cours
# ==========================================================
@login_required
@require_POST
@transaction.atomic
def mark_lesson_complete(request):
    """Marque une leçon comme terminée (progression étudiante)."""
    if not _is_student(request.user):
        return JsonResponse({"ok": False, "error": "⛔ Accès réservé aux étudiants."}, status=403)

    data = _json(request)
    lesson_id = data.get("lesson_id")
    enrollment_id = data.get("enrollment_id")

    if not (lesson_id and enrollment_id):
        return HttpResponseBadRequest("Paramètres manquants")

    lp, _ = LessonProgress.objects.select_for_update().get_or_create(
        enrollment_id=enrollment_id, lesson_id=lesson_id
    )

    # Compatibilité: si le modèle n'a pas mark_completed(), on pose completed_at manuellement
    if hasattr(lp, "mark_completed") and callable(lp.mark_completed):
        lp.mark_completed()
    else:
        lp.completed_at = timezone.now()
        lp.save(update_fields=["completed_at"])

    return JsonResponse({
        "ok": True,
        "completed_at": lp.completed_at.isoformat() if lp.completed_at else None,
    })


@login_required
def api_student_modules(request):
    """Liste des modules (UE) accessibles à l’étudiant connecté (cohorte & cycle MASTER pris en compte)."""
    if not _is_student(request.user):
        return JsonResponse({"ok": False, "error": "⛔ Accès réservé aux étudiants."}, status=403)

    # Inscription MASTER active la plus récente
    enrollment = (
        MasterEnrollment.objects
        .select_related("program", "cohort")
        .filter(student=request.user, status="ACTIVE", program__cycle=CYCLE_MASTER)
        .order_by("-created_at")
        .first()
    )
    if not enrollment:
        return JsonResponse({"ok": True, "modules": []})

    # Semestres du même programme ET de la même cohorte
    semesters = Semester.objects.filter(program=enrollment.program, cohort=enrollment.cohort)

    modules = (
        ModuleUE.objects
        .filter(semester__in=semesters, is_active=True)
        .select_related("semester", "semester__program")
        .prefetch_related(
            Prefetch("instructors", queryset=InstructorAssignment.objects.select_related("instructor"))
        )
        .order_by("semester__order", "order", "id")
    )

    # Optionnel: retrouver le pourcentage si ModuleProgress est utilisé
    progress_map = {}
    try:
        from ..models import ModuleProgress
        progress_qs = ModuleProgress.objects.filter(enrollment=enrollment, module__in=modules)
        progress_map = {p.module_id: float(p.percent) for p in progress_qs}
    except Exception:
        pass

    data = []
    for m in modules:
        ia = m.instructors.first() if hasattr(m, "instructors") else None
        teacher = getattr(ia, "instructor", None)

        # Nom enseignant (si dispo)
        teacher_name = None
        if teacher:
            try:
                # get_full_name peut être vide selon le modèle
                teacher_name = teacher.get_full_name() or str(teacher)
            except Exception:
                teacher_name = str(teacher)

        data.append({
            "id": m.id,
            "title": m.title,
            "semester": getattr(m.semester, "name", ""),
            "program": getattr(getattr(m.semester, "program", None), "title", ""),
            "teacher": teacher_name,
            "percent": int(progress_map.get(m.id, 0)),
        })

    return JsonResponse({"ok": True, "modules": data})


@login_required
def api_student_lessons(request, module_id: int):
    """Retourne les chapitres + leçons publiées d’un module (compat champs réels)."""
    if not _is_student(request.user):
        return JsonResponse({"ok": False, "error": "⛔ Accès réservé aux étudiants."}, status=403)

    module = get_object_or_404(ModuleUE.objects.select_related("semester", "semester__program"), pk=module_id)

    # Sécurité: vérifier que l’étudiant est inscrit au même programme & cohorte
    enrollment = (
        MasterEnrollment.objects
        .select_related("program", "cohort")
        .filter(student=request.user, status="ACTIVE", program=module.semester.program)
        .order_by("-created_at")
        .first()
    )
    if not enrollment or module.semester.cohort_id != enrollment.cohort_id:
        return JsonResponse({"ok": False, "error": "⛔ Vous n’êtes pas inscrit à ce cours."}, status=403)

    chapters = (
        Chapter.objects.filter(module=module)
        .prefetch_related("lessons")
        .order_by("order", "id")
    )

    data = []
    for ch in chapters:
        lessons_list = []
        for l in ch.lessons.filter(is_published=True).order_by("order", "id"):
            # Champs réels dans models: duration_seconds, external_url, video_file
            video_url = l.external_url or (l.video_file.url if getattr(l, "video_file", None) else None)
            lessons_list.append({
                "id": l.id,
                "title": l.title,
                "duration_seconds": getattr(l, "duration_seconds", 0) or 0,
                "video_url": video_url,
            })

        data.append({
            "chapter_id": ch.id,
            "chapter_title": ch.title,
            "lessons": lessons_list,
        })

    return JsonResponse({"ok": True, "module_id": module.id, "chapters": data})


# ==========================================================
# 👨‍🏫 API ENSEIGNANT — gestion devoirs et notes
# ==========================================================
@login_required
@require_POST
@transaction.atomic
def save_note(request):
    """Permet à un enseignant de noter une soumission."""
    if not _is_instructor(request.user):
        return JsonResponse({"ok": False, "error": "⛔ Accès réservé aux enseignants."}, status=403)

    data = _json(request)
    submission_id = data.get("submission_id")
    score_raw = data.get("score_raw")

    if not submission_id:
        return HttpResponseBadRequest("submission_id manquant")

    try:
        submission = Submission.objects.select_for_update().get(pk=submission_id)
    except Submission.DoesNotExist:
        return HttpResponseBadRequest("Soumission introuvable")

    submission.grade(
        score_raw=Decimal(str(score_raw or 0)),
        grader=request.user,
        feedback=data.get("feedback", "")
    )

    return JsonResponse({
        "ok": True,
        "note_20": float(submission.note_20 or 0),
        "feedback": submission.feedback,
    })


@login_required
@require_POST
@transaction.atomic
def create_assignment(request):
    """Crée un nouveau devoir pour un module."""
    if not _is_instructor(request.user):
        return JsonResponse({"ok": False, "error": "⛔ Accès réservé aux enseignants."}, status=403)

    data = _json(request)
    title = data.get("title")
    module_id = data.get("module_id")
    kind = data.get("kind", "QCM")

    if not (title and module_id):
        return HttpResponseBadRequest("Paramètres insuffisants")

    # TODO : vérifier que le module appartient bien à l’enseignant connecté
    a = Assignment.objects.create(
        module_id=module_id,
        title=title,
        kind=kind,
        created_by=request.user,
        is_published=False,
    )

    return JsonResponse({
        "ok": True,
        "assignment_id": a.id,
        "message": f"Devoir '{a.title}' créé avec succès.",
    })


# ==========================================================
# 🧠 API DIRECTEUR — statistiques globales (ESFÉ Master)
# ==========================================================
@login_required
def api_director_overview(request):
    """Fournit des statistiques générales sur les Masters (Directeur des Études)."""
    if not _is_director(request.user):
        return JsonResponse({"ok": False, "error": "⛔ Accès réservé au Directeur des Études."}, status=403)

    total_students = MasterEnrollment.objects.values("student").distinct().count()
    total_teachers = InstructorAssignment.objects.values("instructor").distinct().count()
    total_exams = Exam.objects.count()
    avg_success_rate = SemesterResult.objects.aggregate(avg=Avg("average_20"))["avg"]

    stats = {
        "students": total_students,
        "teachers": total_teachers,
        "exams": total_exams,
        "average": round(float(avg_success_rate or 0.0), 2),
    }

    return JsonResponse({"ok": True, "stats": stats})


# ==========================================================
# 🎓 API ÉTUDIANT — OVERVIEW (APERÇU DASHBOARD)
# ==========================================================
@login_required
def api_student_overview(request):
    """
    Donne les statistiques globales pour l’étudiant connecté :
      - progression moyenne
      - moyenne générale
      - crédits validés
      - dernières activités (devoirs, examens, notes)
    """
    if not _is_student(request.user):
        return JsonResponse({"ok": False, "error": "⛔ Accès réservé aux étudiants."}, status=403)

    # 🔹 Inscription MASTER active
    enrollment = (
        MasterEnrollment.objects
        .select_related("program", "cohort")
        .filter(student=request.user, status="ACTIVE", program__cycle=CYCLE_MASTER)
        .order_by("-created_at")
        .first()
    )

    if not enrollment:
        return JsonResponse({"ok": True, "progress": 0, "average": 0, "credits": 0, "activities": []})

    # =====================================================
    # 1️⃣ Progression moyenne (ModuleProgress)
    # =====================================================
    avg_progress = 0
    try:
        from ..models import ModuleProgress
        progresses = ModuleProgress.objects.filter(enrollment=enrollment)
        if progresses.exists():
            avg_progress = round(sum(float(p.percent or 0) for p in progresses) / progresses.count(), 2)
    except Exception:
        avg_progress = 0

    # =====================================================
    # 2️⃣ Moyenne générale & crédits validés
    # =====================================================
    results = SemesterResult.objects.filter(enrollment=enrollment)
    avg_values = [float(r.average_20) for r in results if r.average_20 is not None]
    moyenne_generale = round(sum(avg_values) / len(avg_values), 2) if avg_values else 0
    credits_total = sum(float(r.credits_earned or 0) for r in results)

    # =====================================================
    # 3️⃣ Dernières activités (3 plus récentes)
    # =====================================================
    recent_acts = []

    # Nouveaux devoirs publiés
    new_assignments = (
        Assignment.objects
        .filter(module__semester__program=enrollment.program, is_published=True)
        .select_related("module")
        .order_by("-created_at")[:3]
    )
    for a in new_assignments:
        recent_acts.append({
            "id": f"a{a.id}",
            "icon": "📘",
            "title": "Nouveau devoir",
            "detail": f"{a.title} ({a.module.title})",
            "date": a.created_at.strftime("%d/%m/%Y") if a.created_at else "",
        })

    # Examens à venir
    upcoming_exams = (
        Exam.objects
        .filter(semester__program=enrollment.program, start_at__gte=timezone.now())
        .select_related("semester")
        .order_by("start_at")[:3]
    )
    for e in upcoming_exams:
        recent_acts.append({
            "id": f"e{e.id}",
            "icon": "🧪",
            "title": "Examen à venir",
            "detail": e.title,
            "date": e.start_at.strftime("%d/%m/%Y") if e.start_at else "",
        })

    # Derniers résultats publiés
    latest_results = results.order_by("-computed_at")[:3]
    for r in latest_results:
        recent_acts.append({
            "id": f"r{r.id}",
            "icon": "📊",
            "title": "Note publiée",
            "detail": f"{r.semester.name} — {r.average_20 or '—'}/20",
            "date": r.computed_at.strftime("%d/%m/%Y") if r.computed_at else "",
        })

    # Limiter à 5 activités récentes max
    activities = sorted(recent_acts, key=lambda x: x["date"], reverse=True)[:5]

    # =====================================================
    # 4️⃣ Réponse JSON structurée
    # =====================================================
    data = {
        "ok": True,
        "progress": avg_progress,
        "average": moyenne_generale,
        "credits": credits_total,
        "activities": activities,
    }

    return JsonResponse(data)
