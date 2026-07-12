from rest_framework import serializers
from .models import Cat, Vaccine


class VaccineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vaccine
        fields = ["id", "nombre", "fecha_aplicacion", "fecha_vencimiento", "soporte"]


class CatSerializer(serializers.ModelSerializer):
    vacunas = VaccineSerializer(many=True, read_only=True, source="vaccine_set")
    edad = serializers.SerializerMethodField()

    class Meta:
        model = Cat
        fields = [
            "id",
            "nombre",
            "raza",
            "sexo",
            "fecha_nacimiento",
            "edad",
            "peso",
            "color",
            "foto",
            "gustos_preferencias",
            "esterilizado",
            "modo_cruce_responsable",
            "fecha_registro",
            "vacunas",
        ]
        read_only_fields = ["fecha_registro"]

    def get_edad(self, obj):
        from datetime import date
        hoy = date.today()
        anios = hoy.year - obj.fecha_nacimiento.year
        if (hoy.month, hoy.day) < (obj.fecha_nacimiento.month, obj.fecha_nacimiento.day):
            anios -= 1
        return anios