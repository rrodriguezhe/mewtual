from rest_framework import serializers
from .models import AdoptionPost


class AdoptionPostSerializer(serializers.ModelSerializer):

    class Meta:
        model = AdoptionPost
        fields = "__all__"

    def validate_gato(self, value):
        request = self.context.get("request")
        if request and value.owner_id != request.user.id:
            raise serializers.ValidationError(
                "Solo puedes publicar en adopción gatos que te pertenecen."
            )
        return value
