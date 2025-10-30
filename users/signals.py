# users/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

User = get_user_model()

@receiver(post_save, sender=User)
def assign_default_role_and_group(sender, instance, created, **kwargs):
    """
    À la création d'un utilisateur :
      - si aucun 'role' donné → rôle par défaut = ETUDIANT
      - ajoute l'utilisateur au groupe correspondant
      - si superuser → ADMIN
    """
    if not created:
        return

    # Superuser → ADMIN prioritaire
    if instance.is_superuser and (not instance.role or instance.role != User.Role.ADMIN):
        instance.role = User.Role.ADMIN
        instance.save(update_fields=["role"])

    # Rôle par défaut si vide
    if not instance.role:
        instance.role = User.Role.ETUDIANT
        instance.save(update_fields=["role"])

    # Groupes selon rôle
    role_to_group = {
        User.Role.AGENT_MARKETING: "Agents Marketing",
        User.Role.SECRETAIRE: "Secrétaires",
        User.Role.GESTIONNAIRE: "Gestionnaires",
        User.Role.DIRECTEUR: "Direction",
        User.Role.ENSEIGNANT: "Enseignants",
        User.Role.ETUDIANT: "Étudiants",
        User.Role.ADMIN: "Administrateurs",
    }
    group_name = role_to_group.get(instance.role)
    if group_name:
        group, _ = Group.objects.get_or_create(name=group_name)
        instance.groups.add(group)
