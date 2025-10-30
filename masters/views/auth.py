# masters/views/auth.py
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse
from django.shortcuts import redirect

def _role(user):
    names = {g.name.lower() for g in user.groups.all()}
    if {"directeur","conseiller","informaticien"} & names:
        return "staff_admin"
    if "enseignant" in names:
        return "instructor"
    return "student"

class MasterLoginView(LoginView):
    template_name = "masters/login.html"  # ton template Master
    redirect_authenticated_user = True

    def get_success_url(self):
        # Priorité au ?next= si présent
        next_url = self.request.GET.get("next") or self.request.POST.get("next")
        if next_url:
            return next_url
        # Sinon, on route par rôle vers le dashboard Master
        role = _role(self.request.user)
        return reverse("masters:dashboard")

from django.contrib.auth.views import LogoutView
from django.urls import reverse_lazy

from django.contrib.auth import logout
from django.shortcuts import redirect
from django.urls import reverse_lazy

def master_logout(request):
    """
    Déconnexion simplifiée (GET ou POST autorisés)
    pour les dashboards du portail Master.
    """
    if request.user.is_authenticated:
        logout(request)
    return redirect(reverse_lazy("masters:login"))

from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.shortcuts import render, redirect

@login_required
def change_password(request):
    if request.method == "POST":
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            user.userprofile.must_change_password = False
            user.userprofile.save()
            update_session_auth_hash(request, user)
            return redirect("masters:dashboard")
    else:
        form = PasswordChangeForm(request.user)
    return render(request, "masters/change_password.html", {"form": form})


# masters/views/auth.py
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.shortcuts import render, redirect
from django.contrib.auth.forms import PasswordChangeForm

@login_required
def force_password_change(request):
    """
    Page imposée aux utilisateurs marqués must_change_password=True
    """
    user_profile = getattr(request.user, "userprofile", None)
    if user_profile and not user_profile.must_change_password:
        return redirect("masters:dashboard")

    if request.method == "POST":
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, form.user)
            if user_profile:
                user_profile.must_change_password = False
                user_profile.save(update_fields=["must_change_password"])
            messages.success(request, "✅ Mot de passe modifié avec succès.")
            return redirect("masters:dashboard")
    else:
        form = PasswordChangeForm(user=request.user)

    return render(request, "masters/force_password_change.html", {"form": form})
