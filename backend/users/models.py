from django.db import models
from django.contrib.auth.models import User


class Profile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE
    )

    foto_perfil = models.ImageField(
        upload_to="profiles/",
        blank=True,
        null=True
    )

    latitud = models.FloatField(
        blank=True,
        null=True
    )

    longitud = models.FloatField(
        blank=True,
        null=True
    )

    ocultar_ubicacion = models.BooleanField(
        default=False
    )

    preferencia_interfaz = models.CharField(
        max_length=50,
        default="claro"
    )

    reputacion = models.FloatField(
        default=5.0
    )

    estado_cuenta = models.CharField(
        max_length=30,
        default="ACTIVA"
    )

    fecha_creacion = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.user.username


class Block(models.Model):
    usuario_bloqueador = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="bloqueos_realizados"
    )

    usuario_bloqueado = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="bloqueos_recibidos"
    )

    fecha_bloqueo = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.usuario_bloqueador} bloqueó a {self.usuario_bloqueado}"