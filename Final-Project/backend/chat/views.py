from rest_framework import permissions, viewsets
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.db.models import Q, Max
from django.utils import timezone

from adoption.models import AdoptionPost

from .models import Chat, Message
from .serializers import (
    ChatSerializer,
    MessageSerializer
)


class ChatViewSet(viewsets.ModelViewSet):
    serializer_class = ChatSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return _chats_de_usuario(self.request.user)


class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Message.objects.filter(chat__in=_chats_de_usuario(self.request.user))

    def perform_create(self, serializer):
        serializer.save(remitente=self.request.user)


def _chats_de_usuario(user):
    """Chats en los que el usuario participa, ya sea via un match o una publicacion de adopcion."""
    return Chat.objects.filter(
        Q(match__gato_emisor__owner=user) | Q(match__gato_receptor__owner=user) |
        Q(publicacion_adopcion__gato__owner=user) | Q(iniciador=user)
    ).select_related(
        "match",
        "match__gato_emisor",
        "match__gato_receptor",
        "match__gato_emisor__owner",
        "match__gato_receptor__owner",
        "publicacion_adopcion__gato",
        "publicacion_adopcion__gato__owner",
        "iniciador",
    ).distinct()


def _otro_participante(chat, user):
    """Devuelve (otro_usuario, otro_gato) para la otra persona en este chat."""
    if chat.match_id:
        match = chat.match
        otro_gato = match.gato_receptor if match.gato_emisor.owner_id == user.id else match.gato_emisor
        return otro_gato.owner, otro_gato

    post = chat.publicacion_adopcion
    otro_gato = post.gato
    otro_usuario = otro_gato.owner if chat.iniciador_id == user.id else chat.iniciador
    return otro_usuario, otro_gato


@login_required
def lista_chats(request):
    chats = _chats_de_usuario(request.user).annotate(
        ultimo_mensaje_fecha=Max("message__fecha_envio")
    ).order_by("-ultimo_mensaje_fecha", "-creado_en")

    chats_data = []
    for chat in chats:
        otro_usuario, otro_gato = _otro_participante(chat, request.user)
        ultimo_mensaje = chat.message_set.order_by("-fecha_envio").first()
        chats_data.append({
            "chat": chat,
            "otro_gato": otro_gato,
            "otro_usuario": otro_usuario,
            "ultimo_mensaje": ultimo_mensaje,
        })

    return render(request, "chat/lista_chats.html", {"chats_data": chats_data})


@login_required
def chat_individual(request, chat_id):
    chat = get_object_or_404(_chats_de_usuario(request.user), id=chat_id)
    otro_usuario, otro_gato = _otro_participante(chat, request.user)
    mensajes = chat.message_set.select_related("remitente").order_by("fecha_envio")

    return render(request, "chat/chat_individual.html", {
        "chat": chat,
        "otro_gato": otro_gato,
        "otro_usuario": otro_usuario,
        "mensajes": mensajes,
    })


@login_required
@require_POST
def iniciar_chat_adopcion(request, post_id):
    post = get_object_or_404(AdoptionPost, pk=post_id, estado="DISPONIBLE")
    if post.gato.owner_id == request.user.id:
        messages.error(request, "No puedes contactarte a ti mismo.")
        return redirect('cats:ver_perfil', cat_id=post.gato_id)

    chat, _ = Chat.objects.get_or_create(
        publicacion_adopcion=post, iniciador=request.user
    )
    return redirect('chat:chat_individual', chat_id=chat.id)


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
    desde_id = int(request.GET.get("desde_id", 0))

    mensajes = chat.message_set.filter(id__gt=desde_id).order_by("fecha_envio")

    data = [{
        "id": m.id,
        "contenido": m.contenido,
        "remitente_id": m.remitente_id,
        "es_mio": m.remitente_id == request.user.id,
        "fecha_envio": timezone.localtime(m.fecha_envio).strftime("%H:%M"),
    } for m in mensajes]

    return JsonResponse({"mensajes": data})
