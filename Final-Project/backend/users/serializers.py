from rest_framework import serializers
from django.contrib.auth.models import User

from .models import Profile, Block


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "email",
        ]


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = "__all__"
        read_only_fields = ["user"]


class BlockSerializer(serializers.ModelSerializer):
    class Meta:
        model = Block
        fields = "__all__"
        read_only_fields = ["usuario_bloqueador"]
