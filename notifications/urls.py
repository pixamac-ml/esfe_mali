from django.urls import path
from . import views

app_name = "notifications"

urlpatterns = [
    path("", views.list_notifications, name="list"),
    path("partial/", views.notifications_partial, name="notifications_partial"),
    path("json/", views.notifications_json, name="notifications_json"),
    path("mark/<int:notif_id>/", views.mark_as_read, name="mark_as_read"),
    path("mark-all/", views.mark_all_as_read, name="mark_all_as_read"),
]
