from rest_framework import serializers
from .models import AdoptionPost


class AdoptionPostSerializer(serializers.ModelSerializer):

    class Meta:
        model = AdoptionPost
        fields = "__all__"