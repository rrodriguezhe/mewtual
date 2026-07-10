from django.db import models
from django.contrib.auth.models import User
from matching.models import Match
# Create your models here.


class Chat(models.Model):

    match = models.OneToOneField(
        Match,
        on_delete=models.CASCADE
    )

    creado_en = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"Chat {self.id}"

class Message(models.Model):

    chat = models.ForeignKey(
        Chat,
        on_delete=models.CASCADE
    )

    remitente = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    contenido = models.TextField()

    fecha_envio = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.remitente}: {self.contenido[:30]}"

