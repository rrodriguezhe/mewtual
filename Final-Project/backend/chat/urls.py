from django.urls import include, path
from rest_framework.routers import DefaultRouter
from . import views
from .views import (
    ChatViewSet,
    MessageViewSet
)

router = DefaultRouter()

router.register(
    r"chats",
    ChatViewSet,
    basename="chat"
)

router.register(
    r"messages",
    MessageViewSet,
    basename="message"
)

app_name = 'chat'

urlpatterns = [
    path("", include(router.urls)),
    path('mensajes/', views.lista_chats, name='lista_chats'),
    path('mensajes/<int:chat_id>/', views.chat_individual, name='chat_individual'),
    path('mensajes/<int:chat_id>/enviar/', views.enviar_mensaje, name='enviar_mensaje'),
    path('mensajes/<int:chat_id>/nuevos/', views.mensajes_nuevos, name='mensajes_nuevos'),
]
