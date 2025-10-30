from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages

from ..forms import TeacherCreateForm

def is_staff_admin(user):
    return user.is_authenticated and (user.is_superuser or user.role in ["DIRECTEUR", "GESTIONNAIRE", "SECRETAIRE", "ADMIN"])

# masters/views/teacher_create.py
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect
from django.contrib import messages

from ..forms import TeacherCreateForm
from ..utils.roles import is_staff_admin

@login_required
@user_passes_test(is_staff_admin)
def create_teacher(request):
    """
    Vue pour créer un enseignant depuis le dashboard staff.
    """
    if request.method == "POST":
        form = TeacherCreateForm(request.POST)
        if form.is_valid():
            teacher, temp_password = form.save()
            messages.success(
                request,
                f"✅ Enseignant {teacher.get_full_name()} créé avec succès.\n"
                f"Identifiant : {teacher.username} — Mot de passe : {temp_password}"
            )
            return redirect("masters:dashboard")
    else:
        form = TeacherCreateForm()

    return render(request, "masters/create_teacher.html", {"form": form})


from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render
from ..models import MasterEnrollment, ModuleUE
from django.contrib.auth import get_user_model

User = get_user_model()

def is_staff_or_admin(user):
    return user.is_superuser or (user.groups.filter(name__icontains="staff").exists())

@login_required
@user_passes_test(is_staff_or_admin)
def list_student_enrollments(request):
    """
    Liste tous les étudiants et leurs inscriptions (programme + cohorte + modules).
    Accessible uniquement au staff/admin.
    """
    data = []
    for student in User.objects.filter(role="STUDENT").order_by("last_name", "first_name"):
        enrollments = MasterEnrollment.objects.filter(student=student).select_related("program", "cohort")
        if not enrollments.exists():
            data.append({
                "student": student,
                "enrollments": [],
                "modules": [],
                "has_enrollment": False,
            })
        else:
            for e in enrollments:
                modules = ModuleUE.objects.filter(semester__program=e.program).order_by("semester__order", "order")
                data.append({
                    "student": student,
                    "enrollments": [e],
                    "modules": modules,
                    "has_enrollment": True,
                })

    return render(request, "masters/admin/student_enrollments.html", {"data": data})
