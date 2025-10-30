# masters/views/fragments.py
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.template.loader import render_to_string
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.db.models import Prefetch, Q, Count, Sum, Avg
from urllib.parse import unquote

from ..utils.roles import user_role
from ..models import (
    MasterEnrollment, Semester, ModuleUE, Chapter, Lesson,
    InstructorAssignment, Assignment, Submission, Exam, ExamGrade,
    ModuleProgress, SemesterResult
)

# --- App externe optionnelle ---
try:
    from programs.models import Program
except Exception:
    Program = None


# ==========================================================
# 🔧 UTILITAIRE GLOBAL — rendu d’un fragment HTML
# ==========================================================
def _render_fragment(request, template_path, ctx=None):
    """Rend un template partiel (fragment HTML) en réponse Http."""
    ctx = ctx or {}
    html = render_to_string(template_path, ctx, request=request)
    return HttpResponse(html)


# ==========================================================
# 🎓 DASHBOARD ÉTUDIANT — fragments principaux
# ==========================================================
@login_required
def student_fragment_switch(request, section: str):
    """Sert les fragments AJAX du dashboard étudiant."""
    if (user_role(request.user) or "").lower() != "student":
        return HttpResponseBadRequest("⛔ Accès refusé — réservé aux étudiants.")

    template_map = {
        "overview":    "masters/fragments/student/overview.html",
        "courses":     "masters/fragments/student/courses.html",
        "assignments": "masters/fragments/student/assignments.html",
        "exams":       "masters/fragments/student/exams.html",
        "results":     "masters/fragments/student/results.html",
        "messages":    "masters/fragments/student/messages.html",
        "settings":    "masters/fragments/student/settings.html",
    }
    tpl = template_map.get(section)
    if not tpl:
        return HttpResponseBadRequest("Section invalide")

    now = timezone.now()
    enrollment = (
        MasterEnrollment.objects
        .select_related("program", "cohort")
        .filter(student=request.user, status="ACTIVE")
        .order_by("-created_at")
        .first()
    )

    ctx = {"user": request.user, "now": now, "enrollment": enrollment}

    # Pas d'inscription active
    if not enrollment:
        return _render_fragment(request, tpl, ctx)

    semesters_qs = Semester.objects.filter(
        program=enrollment.program, cohort=enrollment.cohort
    )

    modules_qs = (
        ModuleUE.objects
        .filter(semester__in=semesters_qs, is_active=True)
        .select_related("semester")
        .prefetch_related(
            Prefetch("instructors", queryset=InstructorAssignment.objects.select_related("instructor"))
        )
        .order_by("semester__order", "order", "id")
    )

    # === MES COURS ===
    # === MES COURS ===
    if section == "courses":
        # 🧠 Si aucun module n’existe encore pour cet étudiant (cas rare après création auto)
        # on tente de relier automatiquement les modules disponibles à son programme/cohorte.
        from ..signals import link_modules_and_lessons

        modules_qs = (
            ModuleUE.objects
            .filter(semester__in=semesters_qs, is_active=True)
            .select_related("semester")
            .prefetch_related(
                Prefetch("instructors", queryset=InstructorAssignment.objects.select_related("instructor"))
            )
            .order_by("semester__order", "order", "id")
        )

        # 🧩 Si aucun module lié, mais que des modules existent en base, on relie automatiquement
        if not ModuleProgress.objects.filter(enrollment=enrollment).exists() and modules_qs.exists():
            print(f"[AUTO-LINK:Dashboard] Aucun ModuleProgress pour {enrollment.student.username}, initialisation...")
            link_modules_and_lessons(enrollment)

        # Recharger la progression après liaison
        progress_qs = ModuleProgress.objects.filter(enrollment=enrollment, module__in=modules_qs)
        progress_map = {p.module_id: float(p.percent or 0) for p in progress_qs}

        modules_with_progress = []
        for m in modules_qs:
            ia = m.instructors.first() if hasattr(m, "instructors") else None
            teacher = ia.instructor if ia else None
            modules_with_progress.append({
                "module": m,
                "percent": int(progress_map.get(m.id, 0)),
                "teacher": teacher,
            })

        # Cas : aucun module actif dans le programme
        if not modules_with_progress:
            ctx["no_modules_message"] = (
                "Aucun module actif trouvé pour votre programme. "
                "Veuillez contacter l'administration si le problème persiste."
            )

        ctx["modules_with_progress"] = modules_with_progress

    # === DEVOIRS ===
    elif section == "assignments":
        assignments = (
            Assignment.objects
            .filter(module__in=modules_qs, is_published=True)
            .select_related("module", "module__semester")
            .order_by("close_at", "id")
        )
        subs = Submission.objects.filter(
            assignment__in=assignments, student=request.user
        ).select_related("assignment")
        subs_map = {s.assignment_id: s for s in subs}
        ctx["assignments_rows"] = [{"assignment": a, "submission": subs_map.get(a.id)} for a in assignments]

    # === EXAMENS ===
    elif section == "exams":
        upcoming_exams = (
            Exam.objects.filter(semester__in=semesters_qs, start_at__gte=now)
            .select_related("semester", "semester__program").order_by("start_at")
        )
        past_exams = (
            Exam.objects.filter(semester__in=semesters_qs, end_at__lt=now)
            .select_related("semester", "semester__program").order_by("-start_at")
        )
        latest_grades = (
            ExamGrade.objects.filter(exam__in=past_exams, student=request.user)
            .order_by("exam_id", "-attempt_no")
        )
        grade_by_exam = {}
        for g in latest_grades:
            if g.exam_id not in grade_by_exam:
                grade_by_exam[g.exam_id] = g
        ctx.update({
            "upcoming_exams": upcoming_exams,
            "past_exams_rows": [{"exam": e, "grade": grade_by_exam.get(e.id)} for e in past_exams],
        })

    # === RÉSULTATS ===
    elif section == "results":
        results_qs = (
            SemesterResult.objects
            .filter(enrollment=enrollment)
            .select_related("semester__program", "semester__cohort")
            .order_by("semester__order", "semester__name")
        )
        avg_values = [float(sr.average_20) for sr in results_qs if sr.average_20 is not None]
        avg_global = round(sum(avg_values) / len(avg_values), 2) if avg_values else None
        credits_total = sum(float(sr.credits_earned or 0) for sr in results_qs)
        decision_finale = next((sr.get_decision_display() for sr in results_qs[::-1] if sr.decision), None)

        semester_blocks = []
        for sr in results_qs:
            mods = ModuleUE.objects.filter(semester=sr.semester)
            graded_subs = Submission.objects.filter(
                assignment__module__in=mods, student=request.user, status="GRADED"
            ).select_related("assignment", "assignment__module")

            subs_by_module = {}
            for s in graded_subs:
                subs_by_module.setdefault(s.assignment.module_id, []).append(s)

            rows = []
            for m in mods:
                notes = [float(s.note_20) for s in subs_by_module.get(m.id, []) if s.note_20]
                final_note = round(sum(notes) / len(notes), 2) if notes else None
                rows.append({"module": m, "final_note": final_note})

            semester_blocks.append({"sr": sr, "rows": rows})

        ctx.update({
            "semester_blocks": semester_blocks,
            "summary": {
                "avg_global": avg_global,
                "credits_total": credits_total,
                "decision_finale": decision_finale,
            },
        })

    return _render_fragment(request, tpl, ctx)


# ==========================================================
# 👨‍🏫 DASHBOARD ENSEIGNANT — fragments
# ==========================================================
def _is_instructor(user):
    """Vérifie si l’utilisateur est enseignant (rôle ou groupe)."""
    if not user or not user.is_authenticated:
        return False
    if getattr(user, "is_superuser", False):
        return True
    role = (user_role(user) or "").lower()
    if role in {"instructor", "enseignant", "teacher", "prof", "professeur"}:
        return True
    try:
        names = {g.name.lower() for g in user.groups.all()}
        if names & {"instructor", "enseignant", "teacher", "prof", "professeur"}:
            return True
    except Exception:
        pass
    return False


# ==========================================================
# 🔁 ROUTER ENSEIGNANT
# ==========================================================
@login_required
def teacher_fragment_switch(request, section: str):
    """Router AJAX enseignant (Tailwind + Alpine.js)."""
    if not _is_instructor(request.user):
        return HttpResponseBadRequest("⛔ Accès réservé aux enseignants.")

    templates = {
        "overview": "masters/fragments/teacher/overview.html",
        "teaching": "masters/fragments/teacher/course_list.html",
        "courses": "masters/fragments/teacher/course_view.html",
        "content": "masters/fragments/teacher/content_manager.html",
        "assignments": "masters/fragments/teacher/assignments.html",
        "exams": "masters/fragments/teacher/exams.html",
        "results": "masters/fragments/teacher/results.html",
        "messages": "masters/fragments/teacher/messages.html",
        "settings": "masters/fragments/teacher/settings.html",
    }

    tpl = templates.get(section)
    if not tpl:
        return HttpResponseBadRequest("Section invalide")

    ctx = {
        "module_id": request.GET.get("module_id") or "",
        "module_title": unquote(request.GET.get("title", "")),
        "video_src": unquote(request.GET.get("src", "")),
        "player": request.GET.get("player") or "",
        "section": section,
    }

    if ctx["player"] == "1":
        tpl = "masters/fragments/teacher/_course_player.html"

    return _render_fragment(request, tpl, ctx)


# ==========================================================
# 🎥 VUE DÉTAILLÉE D’UN COURS — étudiant (style Udemy)
# ==========================================================
@login_required
def student_course_view(request, course_id: int):
    """Vue détaillée du cours (chapitres + vidéos) — côté étudiant."""
    if (user_role(request.user) or "").lower() != "student":
        return HttpResponseBadRequest("⛔ Accès réservé aux étudiants.")

    module = get_object_or_404(ModuleUE, pk=course_id)

    # Vérification inscription
    enrollment = MasterEnrollment.objects.filter(student=request.user, status="ACTIVE").first()
    if not enrollment or module.semester.program != enrollment.program:
        return HttpResponseBadRequest("⛔ Vous n’êtes pas inscrit à ce cours.")

    chapters = (
        Chapter.objects.filter(module=module)
        .prefetch_related("lessons")
        .order_by("order", "id")
    )

    lessons_by_chapter = [
        {"chapter": ch, "lessons": ch.lessons.filter(is_published=True).order_by("order", "id")}
        for ch in chapters
    ]

    if not lessons_by_chapter:
        return HttpResponse(
            "<div class='p-6 text-center text-gray-500 dark:text-gray-400'>"
            "<i data-lucide='info' class='w-5 h-5 inline text-cyan-500'></i><br>"
            "Aucune leçon publiée pour ce cours pour le moment.</div>"
        )

    all_lessons = Lesson.objects.filter(
        chapter__module=module, is_published=True
    ).order_by("chapter__order", "order", "id")

    lesson_id = request.GET.get("lesson")
    current_lesson = all_lessons.filter(pk=lesson_id).first() if lesson_id else all_lessons.first()

    next_lesson = None
    if current_lesson:
        next_lesson = all_lessons.filter(
            Q(chapter__order__gt=current_lesson.chapter.order) |
            Q(chapter__order=current_lesson.chapter.order, order__gt=current_lesson.order)
        ).first()

    ctx = {
        "module": module,
        "lessons_by_chapter": lessons_by_chapter,
        "current_lesson": current_lesson,
        "next_lesson": next_lesson,
    }
    return _render_fragment(request, "masters/fragments/student/course_view.html", ctx)


# ==========================================================
# 📈 API JSON — progression leçon
# ==========================================================
@login_required
def mark_lesson_complete(request):
    """Marque une leçon comme complétée (API JSON)."""
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "Méthode non autorisée"}, status=405)

    import json
    try:
        data = json.loads(request.body.decode("utf-8"))
        lesson_id = data.get("lesson_id")
        enrollment_id = data.get("enrollment_id")
    except Exception:
        return JsonResponse({"ok": False, "error": "Requête invalide"}, status=400)

    if not lesson_id or not enrollment_id:
        return JsonResponse({"ok": False, "error": "Paramètres manquants"}, status=400)

    from ..models import LessonProgress
    try:
        lp, _ = LessonProgress.objects.get_or_create(
            enrollment_id=enrollment_id, lesson_id=lesson_id
        )
        lp.mark_completed()
        return JsonResponse({"ok": True, "completed_at": lp.completed_at.isoformat()})
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=500)
