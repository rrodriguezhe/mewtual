from django.db import models
from cats.models import Cat
# Create your models here.


class AdoptionPost(models.Model):

    ESTADOS = [
        ("DISPONIBLE", "Disponible"),
        ("ADOPTADO", "Adoptado"),
    ]

    gato = models.ForeignKey(
        Cat,
        on_delete=models.CASCADE
    )

    descripcion = models.TextField()

    estado = models.CharField(
        max_length=20,
        choices=ESTADOS,
        default="DISPONIBLE"
    )

    publicado_en = models.DateTimeField(
        auto_now_add=True
    )
