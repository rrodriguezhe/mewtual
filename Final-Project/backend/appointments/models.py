from django.db import models
from cats.models import Cat
from matching.models import Match


class Appointment(models.Model):

    ESTADOS = [
        ("PENDIENTE", "Pendiente"),
        ("ACEPTADA", "Aceptada"),
        ("CANCELADA", "Cancelada"),
    ]

    match = models.ForeignKey(
        Match,
        on_delete=models.CASCADE
    )

    fecha = models.DateTimeField()

    ubicacion = models.CharField(
        max_length=200
    )

    estado = models.CharField(
        max_length=20,
        choices=ESTADOS,
        default="PENDIENTE"
    )


def __str__(self):
    return f"{self.ubicacion} - {self.fecha}"
