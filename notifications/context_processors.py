# notifications/context_processors.py
from .models import Notification

def unread_notifications_count(request):
    if request.user.is_authenticated:
        return {
            "notif_unread_count": Notification.objects.filter(
                recipient=request.user, is_read=False
            ).count()
        }
    return {}
