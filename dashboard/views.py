from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from users.models import User
from notifications.models import Notification
from admissions.models import Admission


@login_required
def dashboard_home(request):
    role = request.user.role
    notifs_unread = request.user.notifications.filter(is_read=False)

    context = {"notifs_unread": notifs_unread}

    if role == User.Role.ADMIN:
        return render(request, "dashboard/admin_dashboard.html", context)
    elif role == User.Role.DIRECTEUR:
        return render(request, "dashboard/director_dashboard.html", context)
    elif role == User.Role.GESTIONNAIRE:
        return render(request, "dashboard/manager_dashboard.html", context)
    elif role == User.Role.SECRETAIRE:
        return render(request, "dashboard/secretary_dashboard.html", context)
    else:
        return render(request, "dashboard/default_dashboard.html", context)


@login_required
def dashboard_admissions(request):
    """Liste des admissions pour l’admin dashboard"""
    admissions = Admission.objects.select_related("program", "campus").order_by("-submitted_at")[:50]

    return render(request, "dashboard/admissions.html", {
        "admissions": admissions
    })
