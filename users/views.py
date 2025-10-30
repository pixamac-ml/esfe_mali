# users/views.py
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.http import HttpRequest, HttpResponse
from django.contrib import messages
from django.db.models import Q

from .models import User
from .forms import (
    CustomUserCreationForm, CustomUserChangeForm,
    ProfileEditForm, AdminSetPasswordForm, PublicRegisterForm
)

# -------- Helpers --------
def is_superadmin(user: User) -> bool:
    return user.is_superuser or user.role == User.Role.ADMIN


# -------- Espace utilisateur --------
@login_required
def profile(request: HttpRequest) -> HttpResponse:
    return render(request, "users/profile.html", {"user_obj": request.user})


@login_required
def edit_profile(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = ProfileEditForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profil mis à jour.")
            return redirect("users:profile")
    else:
        form = ProfileEditForm(instance=request.user)
    return render(request, "users/edit_profile.html", {"form": form})


@login_required
def change_password(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # évite la déconnexion
            messages.success(request, "Votre mot de passe a été changé.")
            return redirect("users:profile")
    else:
        form = PasswordChangeForm(request.user)
    return render(request, "users/password_change.html", {"form": form})


# -------- Console Admin/Marketing Users Management --------
@user_passes_test(is_superadmin)
def user_list(request: HttpRequest) -> HttpResponse:
    q = request.GET.get("q", "").strip()
    qs = User.objects.all().order_by("-date_joined")
    if q:
        qs = qs.filter(
            Q(username__icontains=q) |
            Q(email__icontains=q) |
            Q(phone__icontains=q)
        )
    return render(request, "users/user_list.html", {"users": qs, "q": q})


@user_passes_test(is_superadmin)
def user_detail(request: HttpRequest, user_id: int) -> HttpResponse:
    user_obj = get_object_or_404(User, pk=user_id)
    return render(request, "users/user_detail.html", {"user_obj": user_obj})


@user_passes_test(is_superadmin)
def user_create(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, "Utilisateur créé.")
            return redirect("users:user_list")
    else:
        form = CustomUserCreationForm()
    return render(request, "users/user_form.html", {"form": form, "title": "Créer un utilisateur"})


@user_passes_test(is_superadmin)
def user_edit(request: HttpRequest, user_id: int) -> HttpResponse:
    user_obj = get_object_or_404(User, pk=user_id)
    if request.method == "POST":
        form = CustomUserChangeForm(request.POST, instance=user_obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Utilisateur mis à jour.")
            return redirect("users:user_detail", user_id=user_obj.id)
    else:
        form = CustomUserChangeForm(instance=user_obj)
    return render(request, "users/user_form.html", {"form": form, "title": "Modifier l'utilisateur"})


@user_passes_test(is_superadmin)
def user_set_password(request: HttpRequest, user_id: int) -> HttpResponse:
    user_obj = get_object_or_404(User, pk=user_id)
    if request.method == "POST":
        form = AdminSetPasswordForm(user_obj, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f"Mot de passe réinitialisé pour {user_obj.username}.")
            return redirect("users:user_detail", user_id=user_obj.id)
    else:
        form = AdminSetPasswordForm(user_obj)
    return render(request, "users/user_set_password.html", {"form": form, "user_obj": user_obj})


# -------- Inscription publique --------
def register(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = PublicRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False  # activation par admin
            user.save()
            messages.success(
                request,
                "Votre compte a été créé. Il doit être validé par l’administration avant activation."
            )
            return redirect("users:login")
    else:
        form = PublicRegisterForm()
    return render(request, "users/register.html", {"form": form})
