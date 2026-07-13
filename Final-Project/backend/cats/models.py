from django.db import models
from django.contrib.auth.models import User


class Cat(models.Model):

    SEXO_CHOICES = [
        ("M", "Macho"),
        ("F", "Hembra"),
    ]

    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    nombre = models.CharField(
        max_length=100
    )

    raza = models.CharField(
        max_length=100
    )

    sexo = models.CharField(
        max_length=1,
        choices=SEXO_CHOICES
    )

    fecha_nacimiento = models.DateField()

    peso = models.FloatField()

    color = models.CharField(
        max_length=100
    )

    foto = models.ImageField(
        upload_to="cats/",
        blank=True,
        null=True
    )

    gustos_preferencias = models.TextField(
        blank=True
    )

    esterilizado = models.BooleanField(
        default=False
    )

    modo_cruce_responsable = models.BooleanField(
        default=True
    )

    fecha_registro = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.nombre


class Vaccine(models.Model):

    gato = models.ForeignKey(
        Cat,
        on_delete=models.CASCADE
    )

    nombre = models.CharField(
        max_length=100
    )

    fecha_aplicacion = models.DateField()

    fecha_vencimiento = models.DateField()

    soporte = models.FileField(
        upload_to="vaccines/",
        blank=True,
        null=True
    )

    def __str__(self):
        return self.nombre


class MedicalRecord(models.Model):

    gato = models.ForeignKey(
        Cat,
        on_delete=models.CASCADE
    )

    diagnostico_procedimiento = models.CharField(
        max_length=255
    )

    notas = models.TextField(
        blank=True
    )

    documento = models.FileField(
        upload_to="medical_records/",
        blank=True,
        null=True
    )

    fecha_registro = models.DateTimeField(
        auto_now_add=True
    )


class Favorite(models.Model):

    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    gato = models.ForeignKey(
        Cat,
        on_delete=models.CASCADE
    )

    fecha_guardado = models.DateTimeField(
        auto_now_add=True
    )
