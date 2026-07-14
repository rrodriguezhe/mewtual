from rest_framework import permissions, viewsets
from django.db.models import Q
from django.shortcuts import render
from .models import Chat, Message
from .serializers import (
    ChatSerializer,
    MessageSerializer
)
from django.contrib.auth.decorators import login_required


class ChatViewSet(viewsets.ModelViewSet):
    serializer_class = ChatSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Chat.objects.filter(
            Q(match__gato_emisor__owner=user) | Q(match__gato_receptor__owner=user)
        )


class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Message.objects.filter(
            Q(chat__match__gato_emisor__owner=user) | Q(chat__match__gato_receptor__owner=user)
        )

    def perform_create(self, serializer):
        serializer.save(remitente=self.request.user)


@login_required
def lista_chats(request):
    return render(request, 'chat/lista_chats.html')


@login_required
def chat_individual(request, chat_id):
    return render(request, 'chat/chat_individual.html')
