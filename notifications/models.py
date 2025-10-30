from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL

class Notification(models.Model):
    TYPE_CHOICES = [
        ("info", "Info"),
        ("success", "Succès"),
        ("warning", "Avertissement"),
        ("error", "Erreur"),
    ]

    recipient = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="notifications"
    )
    sender = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="sent_notifications"
    )
    notif_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default="info")
    message = models.TextField()
    url = models.CharField(max_length=255, blank=True, null=True)  # lien optionnel
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Notif {self.notif_type} pour {self.recipient} : {self.message[:30]}"
