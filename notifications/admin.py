from django.contrib import admin
from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("recipient", "message", "notif_type", "is_read", "created_at")
    list_filter = ("notif_type", "is_read", "created_at")
    search_fields = ("message", "recipient__username", "sender__username")
    ordering = ("-created_at",)

    # 👉 Actions groupées
    actions = ["mark_as_read", "mark_as_unread"]

    def mark_as_read(self, request, queryset):
        updated = queryset.update(is_read=True)
        self.message_user(request, f"{updated} notifications marquées comme lues ✅")

    mark_as_read.short_description = "Marquer comme lues"

    def mark_as_unread(self, request, queryset):
        updated = queryset.update(is_read=False)
        self.message_user(request, f"{updated} notifications marquées comme non lues 🔄")

    mark_as_unread.short_description = "Marquer comme non lues"
