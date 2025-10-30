# masters/views/api_lessons_json.py
from django.http import JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404

from ..models import Lesson, Chapter, ModuleUE, InstructorAssignment
from ..utils.roles import user_role
from ..services.drive_service import drive_delete

# ============================================================
# 🔐 Vérifications de rôle et d’accès
# ============================================================

def _is_instructor(user):
    if not user or not user.is_authenticated:
        return False
    if getattr(user, "is_superuser", False):
        return True
    try:
        role = (user_role(user) or "").lower()
    except Exception:
        role = ""
    if role in {"instructor", "enseignant", "teacher", "prof", "professeur"}:
        return True
    try:
        names = set(g.name.lower() for g in user.groups.all())
        if names & {"instructor", "enseignant", "teacher", "prof", "professeur"}:
            return True
    except Exception:
        pass
    return False


def _has_access(user, module):
    """Accès = superuser OU (enseignant ET affectation active au module)."""
    if getattr(user, "is_superuser", False):
        return True
    if not _is_instructor(user):
        return False
    return InstructorAssignment.objects.filter(
        instructor=user, module=module, is_active=True
    ).exists()

# ============================================================
# 🧩 API de gestion des leçons
# ============================================================

@method_decorator(csrf_exempt, name="dispatch")  # ⚠️ utile pour fetch multipart
@method_decorator(login_required, name="dispatch")
class LessonAPIView(View):
    """
    API JSON fluide pour la gestion des leçons (AJAX / fetch).
    Gère aussi bien les FormData (fichiers) que JSON.
    """

    # ================================
    # GET : Liste des leçons d’un module
    # ================================
    def get(self, request, module_id):
        module = get_object_or_404(ModuleUE, pk=module_id)

        if not _has_access(request.user, module):
            return JsonResponse({"ok": False, "error": "⛔ Accès refusé au module"}, status=403)

        lessons = (
            Lesson.objects.filter(chapter__module=module, is_published=True)
            .select_related("chapter")
            .order_by("chapter__order", "order")
        )

        data = [
            {
                "id": l.id,
                "title": l.title,
                "chapter": l.chapter.title if l.chapter else "",
                "order": l.order,
                "external_url": l.external_url,
                "video_file": l.video_file.url if l.video_file else None,
                "resource_file": l.resource_file.url if getattr(l, "resource_file", None) else None,
            }
            for l in lessons
        ]

        return JsonResponse({
            "ok": True,
            "module": module.title,
            "count": len(data),
            "lessons": data,
        })

    # ================================
    # POST : Création d’une leçon
    # ================================
    def post(self, request, module_id):
        module = get_object_or_404(ModuleUE, pk=module_id)
        if not _has_access(request.user, module):
            return JsonResponse({"ok": False, "error": "⛔ Accès refusé au module"}, status=403)

        # ⚙️ Gestion des deux formats (FormData ou JSON)
        title = ""
        external_url = ""
        chapter_id = None
        video_file = None
        resource_file = None

        if request.content_type.startswith("multipart/"):
            title = (request.POST.get("title") or "").strip()
            external_url = (request.POST.get("external_url") or "").strip()
            chapter_id = request.POST.get("chapter")
            video_file = request.FILES.get("video_file")
            resource_file = request.FILES.get("resource_file")
        else:
            import json
            try:
                data = json.loads(request.body.decode("utf-8"))
                title = (data.get("title") or "").strip()
                external_url = (data.get("external_url") or "").strip()
                chapter_id = data.get("chapter")
            except Exception:
                return JsonResponse({"ok": False, "error": "⚠️ JSON invalide"}, status=400)

        if not title:
            return JsonResponse({"ok": False, "error": "⚠️ Le titre est obligatoire"}, status=400)

        chapter = Chapter.objects.filter(id=chapter_id, module=module).first()
        if not chapter:
            chapter, _ = Chapter.objects.get_or_create(
                module=module, order=1, defaults={"title": "Chapitre 1"}
            )

        lesson = Lesson.objects.create(
            chapter=chapter,
            title=title,
            external_url=external_url,
            video_file=video_file or None,
            resource_file=resource_file or None,
            order=(chapter.lessons.count() + 1),
            is_published=True,
        )

        return JsonResponse({"ok": True, "id": lesson.id, "message": "✅ Leçon créée avec succès."})

    # ================================
    # PUT : Mise à jour d’une leçon
    # ================================
    def put(self, request, module_id, lesson_id=None):
        if not lesson_id:
            return JsonResponse({"ok": False, "error": "ID de leçon manquant"}, status=400)

        lesson = get_object_or_404(Lesson, id=lesson_id)
        module = lesson.chapter.module

        if not _has_access(request.user, module):
            return JsonResponse({"ok": False, "error": "⛔ Accès refusé au module"}, status=403)

        try:
            import json
            data = json.loads(request.body.decode("utf-8"))
        except Exception:
            return JsonResponse({"ok": False, "error": "⚠️ JSON invalide"}, status=400)

        new_title = data.get("title")
        new_url = data.get("external_url")

        if new_title:
            lesson.title = new_title.strip()
        if new_url is not None:
            lesson.external_url = new_url.strip()

        lesson.save()
        return JsonResponse({"ok": True, "message": "✅ Leçon mise à jour."})

    # ================================
    # DELETE : Suppression d’une leçon
    # ================================
    def delete(self, request, module_id, lesson_id=None):
        if not lesson_id:
            return JsonResponse({"ok": False, "error": "ID manquant"}, status=400)

        lesson = get_object_or_404(Lesson, id=lesson_id)
        module = lesson.chapter.module

        if not _has_access(request.user, module):
            return JsonResponse({"ok": False, "error": "⛔ Accès refusé au module"}, status=403)

        if lesson.external_url:
            try:
                drive_delete(lesson.external_url)
            except Exception:
                pass

        lesson.delete()
        return JsonResponse({"ok": True, "message": "🗑️ Leçon supprimée avec succès."})
