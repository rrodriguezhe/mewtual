from rest_framework import viewsets
from django.shortcuts import render
from .models import Chat, Message
from .serializers import (
    ChatSerializer,
    MessageSerializer
)
from django.contrib.auth.decorators import login_required

class ChatViewSet(viewsets.ModelViewSet):
    queryset = Chat.objects.all()
    serializer_class = ChatSerializer


class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer

@login_required
def lista_chats(request):
    return render(request, 'chat/lista_chats.html')
@login_required
def chat_individual(request, chat_id):
    return render(request, 'chat/chat_individual.html')