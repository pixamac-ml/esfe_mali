from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.contrib.auth.models import Group

from ..models import ModuleUE, Lesson, Chapter, InstructorAssignment
from ..utils.roles import user_role

# --- Rôle enseignant robuste (accepte plusieurs libellés/groupes) ---
def _is_instructor(user):
    if not user or not user.is_authenticated:
        return False
    if getattr(user, "is_superuser", False):
        return True  # superuser a tous les droits
    # 1) via helper si déjà en place
    try:
        from ..utils.roles import is_instructor as _is_inst
        if _is_inst(user):
            return True
    except Exception:
        pass
    # 2) via user_role() string
    try:
        role = user_role(user) or ""
    except Exception:
        role = ""
    role = str(role).lower()
    if role in {"instructor", "enseignant", "teacher", "prof", "professeur"}:
        return True
    # 3) via groupes
    try:
        names = set(g.name.lower() for g in user.groups.all())
        if names & {"instructor", "enseignant", "teacher", "prof", "professeur"}:
            return True
    except Exception:
        pass
    return False


@login_required
def api_teacher_modules(request):
    """
    Liste des modules assignés à l’enseignant connecté (JSON).
    Utilisée par courselist.html (AJAX).
    """
    if not _is_instructor(request.user):
        return JsonResponse({"ok": False, "error": "⛔ Accès refusé (rôle)"}, status=403)

    assignments = (
        InstructorAssignment.objects
        .filter(instructor=request.user, is_active=True)
        .select_related("module", "module__semester", "module__semester__program")
        .order_by("module__semester__order", "module__order")
    )

    modules = []
    for a in assignments:
        m = a.module
        chapters_count = Chapter.objects.filter(module=m).count()
        lessons_count = Lesson.objects.filter(chapter__module=m, is_published=True).count()
        modules.append({
            "id": m.id,
            "title": m.title,
            "semester": m.semester.name if getattr(m, "semester", None) else "",
            "program": (m.semester.program.title
                        if getattr(m, "semester", None) and getattr(m.semester, "program", None)
                        else ""),
            "chapters_count": chapters_count,
            "lessons_count": lessons_count,
        })

    # Toujours renvoyer ok:true + liste (même vide) pour simplifier le front
    return JsonResponse({"ok": True, "modules": modules})
