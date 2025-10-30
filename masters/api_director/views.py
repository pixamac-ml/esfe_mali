# masters/api_director/views.py
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Count, Avg, Sum, Q
from programs.models import Program
from ..models import (
    ModuleUE, InstructorAssignment, MasterEnrollment, Exam, SemesterResult, Cohort
)
from .serializers import (
    ProgramSerializer, ModuleSerializer, InstructorSerializer,
    StudentSerializer, ExamSerializer, SemesterResultSerializer
)


# ----------------------------------------------------------
# Vérifie que l’utilisateur est un Directeur des Études
# ----------------------------------------------------------
def is_director(user):
    if not user.is_authenticated:
        return False
    role = (getattr(user, "role", "") or "").upper()
    if role in ["DIRECTEUR_ETUDES", "DIRECTEUR D'ÉTUDES", "DIRECTEUR DES ETUDES", "DIRECTEUR"]:
        return True
    groups = {g.name.lower() for g in user.groups.all()}
    return "directeur" in groups or "staff_admin" in groups


# ----------------------------------------------------------
# 🧭 1️⃣ Aperçu général (Overview)
# ----------------------------------------------------------
class DirectorOverviewAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not is_director(request.user):
            return Response({"error": "⛔ Accès refusé"}, status=403)

        nb_programs = Program.objects.filter(cycle="MASTER").count()
        nb_modules = ModuleUE.objects.count()
        nb_students = MasterEnrollment.objects.values("student").distinct().count()
        nb_teachers = InstructorAssignment.objects.values("instructor").distinct().count()
        nb_exams = Exam.objects.count()

        avg_success = SemesterResult.objects.aggregate(avg=Avg("average_20"))["avg"] or 0
        avg_success = round(float(avg_success), 2)

        data = {
            "programs": nb_programs,
            "modules": nb_modules,
            "students": nb_students,
            "teachers": nb_teachers,
            "exams": nb_exams,
            "avg_success": avg_success,
            "recent_exams": list(
                Exam.objects.order_by("-start_at").values("title", "start_at")[:5]
            ),
            "recent_results": list(
                SemesterResult.objects.order_by("-computed_at").values("average_20", "decision")[:5]
            )
        }
        return Response(data)


# ----------------------------------------------------------
# 👨‍🏫 2️⃣ Liste des enseignants affectés
# ----------------------------------------------------------
class DirectorTeacherListAPI(generics.ListAPIView):
    serializer_class = InstructorSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if not is_director(self.request.user):
            return InstructorAssignment.objects.none()
        search = self.request.query_params.get("q", "")
        qs = InstructorAssignment.objects.select_related("instructor", "module", "module__semester")
        if search:
            qs = qs.filter(
                Q(instructor__first_name__icontains=search) |
                Q(instructor__last_name__icontains=search) |
                Q(module__title__icontains=search)
            )
        return qs.order_by("instructor__last_name", "module__code")


# ----------------------------------------------------------
# 🎓 3️⃣ Liste des étudiants inscrits
# ----------------------------------------------------------
class DirectorStudentListAPI(generics.ListAPIView):
    serializer_class = StudentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if not is_director(self.request.user):
            return MasterEnrollment.objects.none()
        program = self.request.query_params.get("program")
        cohort = self.request.query_params.get("cohort")
        search = self.request.query_params.get("q", "")
        qs = MasterEnrollment.objects.select_related("student", "program", "cohort")
        if program:
            qs = qs.filter(program_id=program)
        if cohort:
            qs = qs.filter(cohort_id=cohort)
        if search:
            qs = qs.filter(
                Q(student__first_name__icontains=search) |
                Q(student__last_name__icontains=search)
            )
        return qs.order_by("student__last_name")


# ----------------------------------------------------------
# 📘 4️⃣ Liste des modules (UE)
# ----------------------------------------------------------
class DirectorModuleListAPI(generics.ListAPIView):
    serializer_class = ModuleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if not is_director(self.request.user):
            return ModuleUE.objects.none()
        program = self.request.query_params.get("program")
        search = self.request.query_params.get("q", "")
        qs = ModuleUE.objects.select_related("semester", "semester__program")
        if program:
            qs = qs.filter(semester__program_id=program)
        if search:
            qs = qs.filter(Q(title__icontains=search) | Q(code__icontains=search))
        return qs.order_by("semester__order", "order")


# ----------------------------------------------------------
# 🧪 5️⃣ Liste des examens
# ----------------------------------------------------------
class DirectorExamListAPI(generics.ListAPIView):
    serializer_class = ExamSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if not is_director(self.request.user):
            return Exam.objects.none()
        program = self.request.query_params.get("program")
        search = self.request.query_params.get("q", "")
        qs = Exam.objects.select_related("semester", "semester__program")
        if program:
            qs = qs.filter(semester__program_id=program)
        if search:
            qs = qs.filter(Q(title__icontains=search))
        return qs.order_by("-start_at")


# ----------------------------------------------------------
# 📊 6️⃣ Liste des résultats par semestre
# ----------------------------------------------------------
class DirectorResultsAPI(generics.ListAPIView):
    serializer_class = SemesterResultSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if not is_director(self.request.user):
            return SemesterResult.objects.none()
        program = self.request.query_params.get("program")
        decision = self.request.query_params.get("decision")
        qs = SemesterResult.objects.select_related("semester__program", "enrollment__student")
        if program:
            qs = qs.filter(semester__program_id=program)
        if decision:
            qs = qs.filter(decision=decision)
        return qs.order_by("-computed_at")
