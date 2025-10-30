# masters/views/api_chapters.py
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from django.shortcuts import get_object_or_404
from django.http import JsonResponse, HttpResponseBadRequest
from django.utils.text import slugify
from django.utils import timezone
from ..models import Chapter, ModuleUE, InstructorAssignment
from ..utils.roles import user_role

import json


@method_decorator(login_required, name="dispatch")
class ChapterView(View):
    """
    API CRUD pour les chapitres d’un module.
    100% JSON – utilisée par le tableau de bord enseignant (Alpine.js / fetch)
    """

    def get(self, request, module_id, *args, **kwargs):
        """Liste les chapitres d’un module avec le nombre de leçons."""
        module = get_object_or_404(ModuleUE, id=module_id)
        if not self._has_access(request.user, module):
            return HttpResponseBadRequest("⛔ Accès refusé.")

        chapters = Chapter.objects.filter(module=module).order_by("order", "id")
        data = [
            {
                "id": ch.id,
                "title": ch.title,
                "order": ch.order,
                "is_locked": ch.is_locked,
                "lessons_count": ch.lessons.count(),
            }
            for ch in chapters
        ]
        return JsonResponse({"ok": True, "module": module.title, "chapters": data})

    # -----------------------------------------------------
    def post(self, request, module_id, *args, **kwargs):
        """Crée un nouveau chapitre dans le module."""
        module = get_object_or_404(ModuleUE, id=module_id)
        if not self._has_access(request.user, module):
            return HttpResponseBadRequest("⛔ Accès refusé.")

        try:
            data = json.loads(request.body.decode("utf-8"))
        except Exception:
            return HttpResponseBadRequest("⚠️ JSON invalide.")

        title = data.get("title", "").strip()
        if not title:
            return HttpResponseBadRequest("⚠️ Le titre est obligatoire.")

        chapter = Chapter.objects.create(
            module=module,
            title=title,
            slug=slugify(title)[:220],
            order=Chapter.objects.filter(module=module).count() + 1,
        )

        return JsonResponse({
            "ok": True,
            "chapter": {
                "id": chapter.id,
                "title": chapter.title,
                "order": chapter.order,
                "is_locked": chapter.is_locked,
            },
        })

    # -----------------------------------------------------
    def put(self, request, module_id, chapter_id=None, *args, **kwargs):
        """Modifie un chapitre existant."""
        if not chapter_id:
            return HttpResponseBadRequest("⚠️ ID de chapitre manquant.")

        chapter = get_object_or_404(Chapter, id=chapter_id)
        module = chapter.module
        if not self._has_access(request.user, module):
            return HttpResponseBadRequest("⛔ Accès refusé.")

        try:
            data = json.loads(request.body.decode("utf-8"))
        except Exception:
            return HttpResponseBadRequest("⚠️ JSON invalide.")

        chapter.title = data.get("title", chapter.title)
        chapter.is_locked = data.get("is_locked", chapter.is_locked)
        chapter.save()

        return JsonResponse({"ok": True})

    # -----------------------------------------------------
    def delete(self, request, module_id, chapter_id=None, *args, **kwargs):
        """Supprime un chapitre (et ses leçons)."""
        if not chapter_id:
            return HttpResponseBadRequest("⚠️ ID manquant.")

        chapter = get_object_or_404(Chapter, id=chapter_id)
        module = chapter.module
        if not self._has_access(request.user, module):
            return HttpResponseBadRequest("⛔ Accès refusé.")

        chapter.delete()
        return JsonResponse({"ok": True})

    # -----------------------------------------------------
    def _has_access(self, user, module):
        """Vérifie si l’utilisateur est enseignant et assigné à ce module."""
        role = user_role(user)
        return role in ("instructor", "enseignant") and InstructorAssignment.objects.filter(
            instructor=user, module=module, is_active=True
        ).exists()
