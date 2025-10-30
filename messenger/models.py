from __future__ import annotations
import uuid
from django.conf import settings
from django.db import models
from django.utils import timezone

User = settings.AUTH_USER_MODEL


class Conversation(models.Model):
    """
    Thread de discussion (1-to-1 ou groupe).
    Optionnellement rattaché à un contexte pédagogique (ex: ModuleUE Master).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=160, blank=True)
    is_group = models.BooleanField(default=False)
    # Lien optionnel vers un module (cours)
    module = models.ForeignKey(
        "masters.ModuleUE",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="conversations"
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_conversations"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        base = self.title or ("Groupe" if self.is_group else "Direct")
        return f"{base} — {self.id}"[:60]

    def last_message(self):
        return self.messages.order_by("-created_at").first()

    def display_for(self, user):
        """
        Si pas de titre, on essaie d'afficher l'autre participant.
        Utile dans ton dashboard.
        """
        if self.title:
            return self.title
        others = self.participants.exclude(user=user)
        if others.exists():
            u = others.first().user
            return u.get_full_name() or u.username
        return "Conversation"


class ConversationParticipant(models.Model):
    """Participants et métadonnées par utilisateur (rôle, lecture, statut)."""
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="participants"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="conversations"
    )
    role = models.CharField(max_length=24, blank=True)  # Ex: ENSEIGNANT, ETUDIANT, DIRECTEUR
    joined_at = models.DateTimeField(auto_now_add=True)
    last_read_at = models.DateTimeField(null=True, blank=True)
    is_pinned = models.BooleanField(default=False)
    is_muted = models.BooleanField(default=False)

    class Meta:
        unique_together = (("conversation", "user"),)
        indexes = [models.Index(fields=["user", "conversation"])]

    def __str__(self):
        return f"{self.user} ↔ {self.conversation_id}"


class Message(models.Model):
    """Messages échangés dans une conversation."""
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages"
    )
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="sent_messages"
    )
    text = models.TextField(blank=True)
    file = models.FileField(upload_to="messenger/files/", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    edited_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["created_at", "id"]

    def __str__(self):
        return f"{self.sender}: {self.text[:40]}"

    @property
    def has_file(self):
        return bool(self.file)


CALL_STATUS = (
    ("INIT", "Initialisé"),
    ("LIVE", "En cours"),
    ("ENDED", "Terminé"),
)


class CallSession(models.Model):
    """Session d'appel/visio WebRTC liée à une conversation."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="calls"
    )
    host = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="hosted_calls"
    )
    room_name = models.SlugField(max_length=80, unique=True)
    status = models.CharField(max_length=8, choices=CALL_STATUS, default="INIT")
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    # Enregistrement local + Google Drive (futur)
    local_file = models.FileField(upload_to="messenger/records/", blank=True)
    duration_sec = models.PositiveIntegerField(default=0)
    drive_file_id = models.CharField(max_length=128, blank=True)
    drive_file_url = models.URLField(blank=True)
    bytes_size = models.BigIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def start(self):
        self.status = "LIVE"
        self.started_at = timezone.now()
        self.save(update_fields=["status", "started_at"])

    def end(self):
        self.status = "ENDED"
        self.ended_at = timezone.now()
        self.save(update_fields=["status", "ended_at"])

    def __str__(self):
        return f"Call {self.room_name} ({self.get_status_display()})"
