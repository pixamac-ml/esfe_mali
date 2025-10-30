from django.contrib import admin
from .models import Conversation, ConversationParticipant, Message, CallSession


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "is_group", "created_by", "created_at")
    search_fields = ("title", "id", "created_by__username", "created_by__first_name", "created_by__last_name")
    list_filter = ("is_group", "created_at")


@admin.register(ConversationParticipant)
class ConversationParticipantAdmin(admin.ModelAdmin):
    list_display = ("conversation", "user", "role", "joined_at", "last_read_at", "is_pinned", "is_muted")
    search_fields = ("conversation__title", "user__username", "user__first_name", "user__last_name")
    list_filter = ("role", "is_pinned", "is_muted")


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("conversation", "sender", "short_text", "created_at")
    search_fields = ("text", "sender__username", "conversation__title")

    def short_text(self, obj):
        return (obj.text or "")[:80]


@admin.register(CallSession)
class CallSessionAdmin(admin.ModelAdmin):
    list_display = ("room_name", "conversation", "host", "status", "created_at", "started_at", "ended_at")
    search_fields = ("room_name", "conversation__title", "host__username")
    list_filter = ("status",)
