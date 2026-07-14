from rest_framework import serializers

from .models import Chat, Message


class ChatSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chat
        fields = "__all__"


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = "__all__"
        read_only_fields = ["remitente"]

    def validate_chat(self, value):
        request = self.context.get("request")
        if request:
            user = request.user
            match = value.match
            if match.gato_emisor.owner_id != user.id and match.gato_receptor.owner_id != user.id:
                raise serializers.ValidationError(
                    "No puedes enviar mensajes a un chat en el que no participas."
                )
        return value
