from rest_framework import viewsets
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.db.models import Q, Max
from django.utils import timezone

from .models import Chat, Message
from .serializers import (
    ChatSerializer,
    MessageSerializer
)


class ChatViewSet(viewsets.ModelViewSet):
    queryset = Chat.objects.all()
    serializer_class = ChatSerializer


class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer


def _chats_de_usuario(user):
    """Chats en los que el usuario participa a traves de alguno de sus gatos."""
    return Chat.objects.filter(
        Q(match__gato_emisor__owner=user) | Q(match__gato_receptor__owner=user)
    ).select_related(
        "match",
        "match__gato_emisor",
        "match__gato_receptor",
        "match__gato_emisor__owner",
        "match__gato_receptor__owner",
    ).distinct()


def _otro_gato(chat, user):
    """Devuelve el gato de la otra persona dentro del match de este chat."""
    match = chat.match
    if match.gato_emisor.owner_id == user.id:
        return match.gato_receptor
    return match.gato_emisor


@login_required
def lista_chats(request):
    chats = _chats_de_usuario(request.user).annotate(
        ultimo_mensaje_fecha=Max("message__fecha_envio")
    ).order_by("-ultimo_mensaje_fecha", "-creado_en")

    chats_data = []
    for chat in chats:
        otro_gato = _otro_gato(chat, request.user)
        ultimo_mensaje = chat.message_set.order_by("-fecha_envio").first()
        chats_data.append({
            "chat": chat,
            "otro_gato": otro_gato,
            "otro_usuario": otro_gato.owner,
            "ultimo_mensaje": ultimo_mensaje,
        })

    return render(request, "chat/lista_chats.html", {"chats_data": chats_data})


@login_required
def chat_individual(request, chat_id):
    chat = get_object_or_404(_chats_de_usuario(request.user), id=chat_id)
    otro_gato = _otro_gato(chat, request.user)
    mensajes = chat.message_set.select_related("remitente").order_by("fecha_envio")

    return render(request, "chat/chat_individual.html", {
        "chat": chat,
        "otro_gato": otro_gato,
        "otro_usuario": otro_gato.owner,
        "mensajes": mensajes,
    })


@login_required
@require_POST
def enviar_mensaje(request, chat_id):
    chat = get_object_or_404(_chats_de_usuario(request.user), id=chat_id)
    contenido = request.POST.get("contenido", "").strip()

    if not contenido:
        return JsonResponse({"error": "El mensaje no puede estar vacio"}, status=400)

    mensaje = Message.objects.create(
        chat=chat,
        remitente=request.user,
        contenido=contenido,
    )

    return JsonResponse({
        "id": mensaje.id,
        "contenido": mensaje.contenido,
        "remitente_id": mensaje.remitente_id,
        "fecha_envio": timezone.localtime(mensaje.fecha_envio).strftime("%H:%M"),
    })


@login_required
def mensajes_nuevos(request, chat_id):
    """Usado por polling en el front para traer mensajes despues de cierto id."""
    chat = get_object_or_404(_chats_de_usuario(request.user), id=chat_id)
    desde_id = request.GET.get("desde_id", 0)

    mensajes = chat.message_set.filter(id__gt=desde_id).order_by("fecha_envio")

    data = [{
        "id": m.id,
        "contenido": m.contenido,
        "remitente_id": m.remitente_id,
        "es_mio": m.remitente_id == request.user.id,
        "fecha_envio": timezone.localtime(m.fecha_envio).strftime("%H:%M"),
    } for m in mensajes]

    return JsonResponse({"mensajes": data})
