from django.db import models
from cats.models import Cat

class Match(models.Model):

    ESTADOS = [
        ("PENDIENTE", "Pendiente"),
        ("ACEPTADO", "Aceptado"),
        ("RECHAZADO", "Rechazado"),
    ]

    gato_emisor = models.ForeignKey(
        Cat,
        on_delete=models.CASCADE,
        related_name="matches_enviados"
    )

    gato_receptor = models.ForeignKey(
        Cat,
        on_delete=models.CASCADE,
        related_name="matches_recibidos"
    )

    estado = models.CharField(
        max_length=20,
        choices=ESTADOS,
        default="PENDIENTE"
    )

    fecha_match = models.DateTimeField(
        auto_now_add=True
    )


def __str__(self):
    return f"{self.gato_emisor} -> {self.gato_receptor}"
