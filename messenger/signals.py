from django.dispatch import receiver
from django.db.models.signals import post_save
from django.contrib.auth import get_user_model
from notifications.signals import notify
from .models import Message, ConversationParticipant

User = get_user_model()


@receiver(post_save, sender=Message)
def notify_new_message(sender, instance: Message, created, **kwargs):
    """
    À chaque nouveau message :
    - on notifie les autres membres de la conversation
    - ça pourra être repris par ton consumer de notification
    """
    if not created:
        return

    conv = instance.conversation
    sender_user = instance.sender

    recipients = [
        p.user for p in ConversationParticipant.objects.filter(
            conversation=conv
        ).exclude(user=sender_user)
    ]

    if not recipients:
        return

    notify.send(
        sender_user,
        recipient_list=recipients,
        verb="a envoyé un message",
        description=instance.text[:120],
        target=conv,
    )
