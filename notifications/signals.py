from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from admissions.models import Admission, PaymentTransaction
from .models import Notification

User = get_user_model()


@receiver(post_save, sender=Admission)
def notify_new_admission(sender, instance, created, **kwargs):
    """Notification quand une admission est créée ou validée"""
    if created:
        recipient = (
            instance.assigned_to
            or User.objects.filter(is_staff=True).first()
            or User.objects.filter(is_superuser=True).first()
        )
        if recipient:
            Notification.objects.create(
                recipient=recipient,
                message=f"Nouvelle candidature reçue : {instance.nom} {instance.prenom}",
                notif_type="info",
                url=f"/admin/admissions/admission/{instance.id}/change/",
            )

    elif instance.status == "PRET_PAIEMENT":
        recipient = (
            instance.assigned_to
            or User.objects.filter(is_staff=True).first()
            or User.objects.filter(is_superuser=True).first()
        )
        if recipient:
            Notification.objects.create(
                recipient=recipient,
                message=f"Candidature validée et prête pour paiement : {instance.nom} {instance.prenom}",
                notif_type="success",
                url=f"/admissions/{instance.id}/",
            )


@receiver(post_save, sender=PaymentTransaction)
def notify_payment(sender, instance, created, **kwargs):
    """Notification quand un paiement est confirmé"""
    if not created and instance.status == "SUCCES":
        recipient = (
            instance.admission.assigned_to
            or User.objects.filter(is_staff=True).first()
            or User.objects.filter(is_superuser=True).first()
        )
        if recipient:
            Notification.objects.create(
                recipient=recipient,
                message=f"Paiement confirmé ({instance.amount} {instance.currency}) "
                        f"pour {instance.admission.nom} {instance.admission.prenom}",
                notif_type="success",
                url=f"/admissions/{instance.admission.id}/",
            )
