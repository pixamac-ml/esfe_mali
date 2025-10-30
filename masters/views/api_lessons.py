# masters/views/api_lessons.py
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from django.shortcuts import get_object_or_404
from django.http import JsonResponse, HttpResponseBadRequest
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.utils import timezone

from ..models import Lesson, Chapter, ModuleUE, InstructorAssignment
from ..utils.roles import user_role

import json


@method_decorator(login_required, name="dispatch")
class LessonView(View):
    """
    CRUD des leçons — version allégée, 100% JSON (pour fetch + Alpine.js)
    """

    def get(self, request, module_id, *args, **kwargs):
        """Retourne les chapitres et leçons d’un module (JSON)"""
        module = get_object_or_404(ModuleUE, id=module_id)
        if not self._has_access(request.user, module):
            return HttpResponseBadRequest("⛔ Accès refusé.")

        chapters = Chapter.objects.filter(module=module).prefetch_related("lessons").order_by("order")

        data = []
        for ch in chapters:
            data.append({
                "id": ch.id,
                "title": ch.title,
                "order": ch.order,
                "lessons": [
                    {
                        "id": l.id,
                        "title": l.title,
                        "order": l.order,
                        "external_url": l.external_url,
                        "video_file": l.video_file.url if l.video_file else "",
                        "resource_file": l.resource_file.url if l.resource_file else "",
                        "is_published": l.is_published,
                    }
                    for l in ch.lessons.order_by("order")
                ]
            })
        return JsonResponse({"module": module.title, "chapters": data})

    # ----------------------------------------------------------
    def post(self, request, module_id, *args, **kwargs):
        """Ajoute une leçon (upload local ou URL externe)."""
        module = get_object_or_404(ModuleUE, id=module_id)
        if not self._has_access(request.user, module):
            return HttpResponseBadRequest("⛔ Accès refusé.")

        title = request.POST.get("title", "").strip()
        chapter_id = request.POST.get("chapter_id")
        external_url = request.POST.get("external_url", "")
        video_file = request.FILES.get("video_file")
        resource_file = request.FILES.get("resource_file")

        if not title:
            return HttpResponseBadRequest("⚠️ Le titre est obligatoire.")

        chapter = Chapter.objects.filter(id=chapter_id, module=module).first()
        if not chapter:
            chapter, _ = Chapter.objects.get_or_create(module=module, order=1, defaults={"title": "Chapitre 1"})

        lesson = Lesson.objects.create(
            chapter=chapter,
            title=title,
            order=chapter.lessons.count() + 1,
            external_url=external_url or "",
            video_file=video_file,
            resource_file=resource_file,
            is_published=True,
        )

        return JsonResponse({"ok": True, "lesson_id": lesson.id})

    # ----------------------------------------------------------
    def put(self, request, module_id, lesson_id=None, *args, **kwargs):
        """Met à jour une leçon existante"""
        if not lesson_id:
            return HttpResponseBadRequest("⚠️ ID manquant.")

        lesson = get_object_or_404(Lesson, id=lesson_id)
        if not self._has_access(request.user, lesson.chapter.module):
            return HttpResponseBadRequest("⛔ Accès refusé.")

        try:
            data = json.loads(request.body.decode("utf-8"))
        except Exception:
            return HttpResponseBadRequest("⚠️ JSON invalide.")

        lesson.title = data.get("title", lesson.title)
        lesson.external_url = data.get("external_url", lesson.external_url)
        lesson.is_published = data.get("is_published", lesson.is_published)
        lesson.save()

        return JsonResponse({"ok": True})

    # ----------------------------------------------------------
    def delete(self, request, module_id, lesson_id=None, *args, **kwargs):
        """Supprime une leçon"""
        if not lesson_id:
            return HttpResponseBadRequest("⚠️ ID manquant.")
        lesson = get_object_or_404(Lesson, id=lesson_id)

        if not self._has_access(request.user, lesson.chapter.module):
            return HttpResponseBadRequest("⛔ Accès refusé.")

        lesson.delete()
        return JsonResponse({"ok": True})

    # ----------------------------------------------------------
    def _has_access(self, user, module):
        """Vérifie que l’utilisateur est enseignant et assigné."""
        role = user_role(user)
        return role in ("instructor", "enseignant") and InstructorAssignment.objects.filter(
            instructor=user, module=module, is_active=True
        ).exists()
