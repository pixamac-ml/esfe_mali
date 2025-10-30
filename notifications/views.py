from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from django.http import JsonResponse
from .models import Notification


@login_required
def list_notifications(request):
    """Affiche toutes les notifications de l'utilisateur (vue classique)"""
    notifications = request.user.notifications.all()
    return render(request, "notifications/list.html", {"notifications": notifications})


@login_required
def notifications_partial(request):
    """Renvoie un fragment HTML avec les notifications (pour Dashboard AJAX)"""
    notifs = request.user.notifications.order_by("-created_at")[:10]
    return render(request, "dashboard/partials/notifications.html", {"notifs": notifs})


@login_required
def notifications_json(request):
    """Renvoie les notifications en JSON (si besoin côté JS)"""
    notifs = request.user.notifications.order_by("-created_at")[:10]
    data = [
        {
            "id": n.id,
            "message": n.message,
            "type": n.notif_type,
            "is_read": n.is_read,
            "created": n.created_at.strftime("%d/%m/%Y %H:%M"),
            "url": n.url or "",
        }
        for n in notifs
    ]
    return JsonResponse({"notifications": data})


@login_required
def mark_as_read(request, notif_id):
    """Marquer une notif comme lue (AJAX)"""
    if request.method == "POST":
        notif = get_object_or_404(Notification, id=notif_id, recipient=request.user)
        notif.is_read = True
        notif.save()
        return JsonResponse({"success": True, "notif_id": notif.id})
    return JsonResponse({"success": False}, status=400)


@login_required
def mark_all_as_read(request):
    """Marquer toutes les notifs comme lues (AJAX)"""
    if request.method == "POST":
        count = request.user.notifications.filter(is_read=False).update(is_read=True)
        return JsonResponse({"success": True, "updated": count})
    return JsonResponse({"success": False}, status=400)
