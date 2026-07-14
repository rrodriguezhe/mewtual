from rest_framework import serializers

from .models import Appointment


class AppointmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = "__all__"

    def validate_match(self, value):
        request = self.context.get("request")
        if request:
            user = request.user
            if value.gato_emisor.owner_id != user.id and value.gato_receptor.owner_id != user.id:
                raise serializers.ValidationError(
                    "No puedes agendar una cita para un match en el que no participas."
                )
        return value
