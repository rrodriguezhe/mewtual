from django.db.models.signals import post_save
from django.dispatch import receiver

from matching.models import Match

from .models import Chat


@receiver(post_save, sender=Match)
def crear_chat_al_aceptar(sender, instance, **kwargs):
    if instance.estado == "ACEPTADO":
        Chat.objects.get_or_create(match=instance)
