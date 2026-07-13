from django.db import models
from django.contrib.auth.models import User
# Create your models here.


class Report(models.Model):

    ESTADOS = [
        ("PENDIENTE", "Pendiente"),
        ("REVISADO", "Revisado"),
        ("CERRADO", "Cerrado"),
    ]

    usuario_reportante = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="reportes_realizados"
    )

    usuario_reportado = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="reportes_recibidos"
    )

    motivo = models.TextField()

    estado = models.CharField(
        max_length=20,
        choices=ESTADOS,
        default="PENDIENTE"
    )

    fecha_reporte = models.DateTimeField(
        auto_now_add=True
    )
