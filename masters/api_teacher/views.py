from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from masters.models import ModuleUE, Chapter, Lesson, InstructorAssignment
from .serializers import ModuleSerializer, ChapterSerializer, LessonSerializer

def is_instructor(user):
    return user.groups.filter(name__iexact="Enseignants").exists() or user.role == "ENSEIGNANT"

# -------- MODULES --------
class ModuleListCreateView(generics.ListCreateAPIView):
    serializer_class = ModuleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if not is_instructor(self.request.user):
            return ModuleUE.objects.none()
        return ModuleUE.objects.filter(instructors__instructor=self.request.user)

    def create(self, request, *args, **kwargs):
        if not is_instructor(request.user):
            return Response({"error": "Accès refusé"}, status=403)
        title = request.data.get("title")
        semester_id = request.data.get("semester")
        if not title or not semester_id:
            return Response({"error": "Champs manquants"}, status=400)
        module = ModuleUE.objects.create(title=title, code=title[:5].upper(), semester_id=semester_id)
        InstructorAssignment.objects.create(instructor=request.user, module=module)
        return Response(ModuleSerializer(module).data, status=201)

class ModuleDeleteView(generics.DestroyAPIView):
    queryset = ModuleUE.objects.all()
    permission_classes = [IsAuthenticated]

# -------- CHAPITRES --------
class ChapterListCreateView(generics.ListCreateAPIView):
    serializer_class = ChapterSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        module_id = self.kwargs.get("module_id")
        return Chapter.objects.filter(module_id=module_id)

    def create(self, request, module_id):
        module = get_object_or_404(ModuleUE, id=module_id)
        title = request.data.get("title")
        if not title:
            return Response({"error": "Titre requis"}, status=400)
        chapter = Chapter.objects.create(module=module, title=title, order=module.chapters.count() + 1)
        return Response(ChapterSerializer(chapter).data, status=201)

class ChapterDeleteView(generics.DestroyAPIView):
    queryset = Chapter.objects.all()
    permission_classes = [IsAuthenticated]

# -------- LEÇONS --------
class LessonListCreateView(generics.ListCreateAPIView):
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        module_id = self.kwargs.get("module_id")
        return Lesson.objects.filter(chapter__module_id=module_id)

    def create(self, request, module_id):
        chapter_id = request.data.get("chapter_id")
        title = request.data.get("title")
        external_url = request.data.get("external_url", "")
        video_file = request.FILES.get("video_file")
        resource_file = request.FILES.get("resource_file")

        if not title:
            return Response({"error": "Titre requis"}, status=400)

        lesson = Lesson.objects.create(
            chapter_id=chapter_id,
            title=title,
            external_url=external_url,
            video_file=video_file,
            resource_file=resource_file,
            is_published=True,
        )
        return Response(LessonSerializer(lesson).data, status=201)

class LessonUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated]


# masters/api_teacher/views.py
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

class TeacherOverviewAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        data = {
            "courses": 6,
            "assignments": 14,
            "students": 128,
            "progress": 72,
            "notifications": [
                "📩 Soumaila Diarra a soumis son devoir de Biostatistique.",
                "🧾 Nouvel examen « Microbiologie » prévu le 28 octobre.",
                "📊 Vous avez reçu 2 nouveaux messages d’étudiants."
            ],
            "exams": [
                {"title": "Microbiologie", "date": "28/10/2025"},
                {"title": "Santé publique", "date": "05/11/2025"}
            ],
            "recent_assignments": [
                {"title": "Analyse statistique", "course": "Biostatistique"},
                {"title": "Rapport méthodologique", "course": "Méthodologie"}
            ]
        }
        return Response(data)
