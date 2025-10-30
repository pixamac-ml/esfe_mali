# users/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    class Role(models.TextChoices):
        AGENT_MARKETING = "AGENT_MARKETING", "Agent marketing"
        SECRETAIRE = "SECRETAIRE", "Secrétaire admission"
        GESTIONNAIRE = "GESTIONNAIRE", "Gestionnaire"
        DIRECTEUR = "DIRECTEUR", "Directeur"
        ENSEIGNANT = "ENSEIGNANT", "Enseignant"
        ETUDIANT = "ETUDIANT", "Étudiant"
        ADMIN = "ADMIN", "Administrateur"

    role = models.CharField(
        max_length=30,
        choices=Role.choices,
        blank=True,
        null=True,
        default=None,
        help_text="Rôle métier de l’utilisateur dans l’organisation"
    )
    annexe = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Annexe rattachée à cet utilisateur (si applicable)"
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="Numéro de téléphone"
    )

    def is_admin(self):
        return self.is_superuser or self.role == self.Role.ADMIN

    def __str__(self):
        return f"{self.username} ({self.get_role_display() if self.role else 'Sans rôle'})"


# ✅ Alias pour compatibilité avec les autres apps
User = CustomUser
