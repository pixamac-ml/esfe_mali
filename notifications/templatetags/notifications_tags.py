# notifications/templatetags/notifications_tags.py
from django import template

register = template.Library()

@register.simple_tag
def unread_notifications(user):
    """Retourne la liste des notifications non lues de l’utilisateur"""
    if user.is_authenticated:
        return user.notifications.filter(is_read=False).order_by("-created_at")
    return []
