from datetime import timedelta
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.mail import send_mail
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.crypto import get_random_string
from django.utils import timezone

from masters.models import (
    MasterEnrollment, Cohort, ModuleUE, ModuleProgress,
    Lesson, LessonProgress
)
from admissions.models import Admission
from programs.models import Program

User = get_user_model()


# ============================================================
# 1️⃣ AUTO-AFFECTATION DES RÔLES / GROUPES DU STAFF & ENSEIGNANTS
# ============================================================
@receiver(post_save, sender=User)
def auto_assign_role_and_group(sender, instance: User, created, **kwargs):
    """
    Lorsqu'un utilisateur (staff ou enseignant) est créé :
      - attribue automatiquement le bon groupe selon le rôle
      - envoie (optionnellement) un mail de bienvenue
    """
    if not created:
        return

    role_to_group = {
        User.Role.AGENT_MARKETING: "Agents Marketing",
        User.Role.SECRETAIRE: "Secrétaires",
        User.Role.GESTIONNAIRE: "Gestionnaires",
        User.Role.DIRECTEUR: "Direction",
        User.Role.ADMIN: "Administrateurs",
    }

    # 🔸 Rôle par défaut
    if not instance.role:
        instance.role = User.Role.SECRETAIRE
        instance.save(update_fields=["role"])

    # 🔸 Groupe principal
    group_name = role_to_group.get(instance.role)
    if group_name:
        group, _ = Group.objects.get_or_create(name=group_name)
        instance.groups.add(group)

    # 🔸 Enseignant : groupe spécifique
    if instance.role in [User.Role.ENSEIGNANT, "ENSEIGNANT"]:
        g, _ = Group.objects.get_or_create(name="Enseignants")
        instance.groups.add(g)

    print(f"[AUTO-ROLE] {instance.username} → {instance.role} ({[g.name for g in instance.groups.all()]})")

    # 🔸 Envoi de mail de bienvenue (optionnel)
    if instance.email:
        try:
            send_mail(
                subject="Bienvenue sur la plateforme Master ESFé",
                message=(
                    f"Bonjour {instance.first_name or instance.username},\n\n"
                    "Votre compte staff/enseignant a été créé sur la plateforme Master ESFé Mali.\n"
                    f"Rôle attribué : {instance.get_role_display() or '—'}\n"
                    f"Identifiant : {instance.username}\n\n"
                    "Veuillez vous connecter pour accéder à votre tableau de bord.\n\n"
                    "Cordialement,\nÉquipe ESFé Mali"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[instance.email],
                fail_silently=True,
            )
        except Exception as e:
            print(f"[⚠️ MAIL NON ENVOYÉ] {e}")


# ============================================================
# 2️⃣ AUTO-LIAISON DES MODULES + LEÇONS À UN ÉTUDIANT
# ============================================================
def link_modules_and_lessons(enrollment: MasterEnrollment):
    """
    Lie automatiquement les modules (UE) actifs du programme/cohorte
    à l'étudiant, puis initialise les LessonProgress sur les leçons publiées.
    Idempotent : utilise get_or_create → aucune duplication.
    """
    student = enrollment.student
    program = enrollment.program
    cohort = enrollment.cohort

    print(f"[LINK] Scan des modules pour {student.username} → {program.title} ({cohort.label})")

    # 🔹 Récupération des modules de la cohorte correspondante
    modules = (
        ModuleUE.objects.filter(
            semester__program=program,
            semester__cohort=cohort,
            is_active=True,
        )
        .select_related("semester")
        .prefetch_related("chapters__lessons")
    )

    if not modules.exists():
        print(f"[INFO] Aucun module trouvé pour {program.title} ({cohort.label})")
        return

    created_modules = 0
    created_lessons = 0

    for module in modules:
        # ModuleProgress (init à 0%)
        _, mp_created = ModuleProgress.objects.get_or_create(
            enrollment=enrollment,
            module=module,
            defaults={"percent": 0.0},
        )
        if mp_created:
            created_modules += 1

        # LessonsProgress sur les leçons publiées
        for chapter in module.chapters.all():
            for lesson in chapter.lessons.filter(is_published=True):
                _, lp_created = LessonProgress.objects.get_or_create(
                    enrollment=enrollment,
                    lesson=lesson,
                )
                if lp_created:
                    created_lessons += 1

    print(f"[AUTO-LINK] {student.username} → {created_modules} modules / {created_lessons} leçons liés.")


# ============================================================
# 3️⃣ FALLBACK : LIAISON AUTO APRÈS CRÉATION MANUELLE D’INSCRIPTION
# ============================================================
@receiver(post_save, sender=MasterEnrollment)
def on_enrollment_created_link_content(sender, instance: MasterEnrollment, created, **kwargs):
    """
    Si une inscription MasterEnrollment est créée manuellement
    (depuis l’admin, le shell ou une API), lie automatiquement les
    modules + leçons disponibles du programme/cohorte Master.
    """
    if created:
        link_modules_and_lessons(instance)


# ============================================================
# 4️⃣ SÉCURITÉ SUPPLÉMENTAIRE : SYNCHRO ADMISSION → MASTER UNIQUEMENT
# ============================================================
@receiver(post_save, sender=Admission)
def admission_to_master_sync(sender, instance: Admission, created, **kwargs):
    """
    Ce signal agit en double sécurité :
      - si une Admission PAIEMENT_OK concerne un programme non-MASTER,
        on ignore complètement.
      - sinon, on vérifie la cohérence et on relie les contenus Master.
    """
    if instance.status != "PAIEMENT_OK":
        return

    program = instance.program
    if getattr(program, "cycle", "").upper() != "MASTER":
        print(f"[SKIP] Admission {instance.id} ignorée — {program.title} n’est pas un programme MASTER.")
        return

    enrollment = MasterEnrollment.objects.filter(admission=instance).first()
    if not enrollment:
        print(f"[WARN] Admission {instance.id} PAIEMENT_OK sans inscription Master correspondante.")
        return

    # Lien des modules/leçons (idempotent)
    link_modules_and_lessons(enrollment)
