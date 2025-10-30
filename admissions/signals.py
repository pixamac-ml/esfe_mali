from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta

from .models import Admission
from masters.models import MasterEnrollment, Cohort
from programs.models import Program

User = get_user_model()


# ============================================================
# 🔁 UTILITAIRE : résolution automatique du programme MASTER
# ============================================================
def resolve_master_program(source_program):
    """
    Si l'admission concerne une formation non-MASTER,
    tente de trouver le programme MASTER équivalent par titre.
    Retourne le programme MASTER ou None si introuvable.
    """
    if not source_program:
        return None

    # Déjà MASTER → on renvoie tel quel
    if getattr(source_program, "cycle", "").upper() == "MASTER":
        return source_program

    # Recherche exacte ou partielle du programme MASTER équivalent
    exact = Program.objects.filter(title=source_program.title, cycle="MASTER").first()
    if exact:
        return exact

    return Program.objects.filter(title__icontains=source_program.title, cycle="MASTER").first()


# ============================================================
# 🧠 SIGNAL : Création automatique du compte étudiant MASTER
# ============================================================
@receiver(post_save, sender=Admission)
def auto_create_student_account(sender, instance: Admission, created, **kwargs):
    """
    Lorsqu’une Admission passe au statut PAIEMENT_OK :
      ✅ crée ou relie un compte étudiant existant
      ✅ mappe automatiquement le programme vers un cycle MASTER
      ✅ crée ou récupère la cohorte (année scolaire)
      ✅ crée l’inscription MasterEnrollment correspondante
      ✅ envoie le mail d’identifiants si nouvel utilisateur
    """

    # 1️⃣ On agit uniquement quand le paiement est validé
    if instance.status != "PAIEMENT_OK":
        return

    # 2️⃣ On récupère ou crée le compte étudiant
    student = None
    if instance.email:
        student = User.objects.filter(email__iexact=instance.email).first()

    if not student:
        # Essai via prénom+nom
        username_guess = (f"{instance.prenom}{instance.nom}".replace(" ", "").lower())[:30]
        student = User.objects.filter(username__iexact=username_guess).first()

    created_user = False
    temp_password = None

    if not student:
        username = instance.ref_code.lower()
        temp_password = get_random_string(8)

        student = User.objects.create_user(
            username=username,
            first_name=instance.prenom,
            last_name=instance.nom,
            email=instance.email or "",
            password=temp_password,
            role=User.Role.ETUDIANT,
        )
        created_user = True

        # Forcer le changement de mot de passe
        if hasattr(student, "userprofile"):
            student.userprofile.must_change_password = True
            student.userprofile.save(update_fields=["must_change_password"])

        print(f"[AUTO-STUDENT] Étudiant créé : {student.username}")

    # 3️⃣ Déterminer le programme MASTER correspondant
    program_master = resolve_master_program(instance.program)
    if not program_master:
        print(f"[⚠️ ERREUR] Aucun programme MASTER trouvé pour {instance.program.title}.")
        return

    # 4️⃣ Créer ou récupérer la cohorte
    submitted_at = instance.submitted_at or timezone.now()
    start_year = submitted_at.year
    label = f"{start_year}-{start_year + 1}"
    start_date = submitted_at.date()
    end_date = start_date + timedelta(days=365)

    cohort, _ = Cohort.objects.get_or_create(
        label=label,
        defaults={"start_date": start_date, "end_date": end_date},
    )

    # 5️⃣ Créer l’inscription MasterEnrollment (si absente)
    enrollment, created_enrollment = MasterEnrollment.objects.get_or_create(
        student=student,
        program=program_master,
        cohort=cohort,
        defaults={
            "admission": instance,
            "status": "ACTIVE",
        },
    )

    if created_enrollment:
        print(f"[AUTO-ENROLLMENT] {student.username} inscrit à {program_master.title} ({cohort.label})")
    else:
        print(f"[INFO] {student.username} déjà inscrit à {program_master.title} ({cohort.label})")

    # 6️⃣ Envoi du mail si nouvel utilisateur
    if created_user and instance.email:
        try:
            send_mail(
                subject="Votre compte étudiant Master ESFé a été créé",
                message=(
                    f"Bonjour {instance.prenom},\n\n"
                    f"Votre compte étudiant ESFé Master a été créé avec succès.\n"
                    f"Identifiant : {student.username}\n"
                    f"Mot de passe temporaire : {temp_password}\n\n"
                    "Merci de vous connecter et de changer immédiatement votre mot de passe.\n\n"
                    "Cordialement,\nÉquipe ESFé Mali"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[instance.email],
                fail_silently=True,
            )
            print(f"[MAIL] Identifiants envoyés à {instance.email}")
        except Exception as e:
            print(f"[⚠️ MAIL NON ENVOYÉ] {e}")
