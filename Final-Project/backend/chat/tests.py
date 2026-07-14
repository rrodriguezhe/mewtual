import datetime

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from cats.models import Cat
from matching.models import Match

from .models import Chat, Message

CHATS_URL = "/chat/chats/"
MESSAGES_URL = "/chat/messages/"


def _make_cat(owner, sexo="M", nombre="Gato"):
    return Cat.objects.create(
        owner=owner,
        nombre=nombre,
        raza="Criollo",
        sexo=sexo,
        fecha_nacimiento=datetime.date(2022, 1, 1),
        peso=3.5,
        color="Gris",
    )


class ChatTemplateViewTests(TestCase):

    def setUp(self):
        self.alice = User.objects.create_user(username="alice", password="pass12345")
        self.bob = User.objects.create_user(username="bob", password="pass12345")
        self.carol = User.objects.create_user(username="carol", password="pass12345")

        self.alice_cat = _make_cat(self.alice, "M", "Simba")
        self.bob_cat = _make_cat(self.bob, "F", "Luna")

        self.match = Match.objects.create(
            gato_emisor=self.alice_cat, gato_receptor=self.bob_cat, estado="ACEPTADO"
        )
        self.chat, _ = Chat.objects.get_or_create(match=self.match)
        self.message = Message.objects.create(chat=self.chat, remitente=self.alice, contenido="Hola!")

    def test_anonymous_redirected_to_login_on_lista_chats(self):
        response = self.client.get(reverse("chat:lista_chats"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("users:login"), response.url)

    def test_anonymous_redirected_to_login_on_chat_individual(self):
        response = self.client.get(reverse("chat:chat_individual", args=[self.chat.id]))
        self.assertEqual(response.status_code, 302)

    def test_lista_chats_only_includes_own_chats(self):
        self.client.login(username="carol", password="pass12345")
        response = self.client.get(reverse("chat:lista_chats"))
        self.assertEqual(response.context["chats_data"], [])

    def test_lista_chats_includes_participant_chat(self):
        self.client.login(username="alice", password="pass12345")
        response = self.client.get(reverse("chat:lista_chats"))
        chats_data = response.context["chats_data"]
        self.assertEqual(len(chats_data), 1)
        self.assertEqual(chats_data[0]["otro_gato"], self.bob_cat)
        self.assertEqual(chats_data[0]["otro_usuario"], self.bob)
        self.assertEqual(chats_data[0]["ultimo_mensaje"], self.message)

    def test_chat_individual_404_for_non_participant(self):
        self.client.login(username="carol", password="pass12345")
        response = self.client.get(reverse("chat:chat_individual", args=[self.chat.id]))
        self.assertEqual(response.status_code, 404)

    def test_chat_individual_shows_correct_context(self):
        self.client.login(username="bob", password="pass12345")
        response = self.client.get(reverse("chat:chat_individual", args=[self.chat.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["otro_gato"], self.alice_cat)
        self.assertEqual(response.context["otro_usuario"], self.alice)
        self.assertIn(self.message, list(response.context["mensajes"]))


class EnviarMensajeViewTests(TestCase):

    def setUp(self):
        self.alice = User.objects.create_user(username="alice", password="pass12345")
        self.bob = User.objects.create_user(username="bob", password="pass12345")
        self.carol = User.objects.create_user(username="carol", password="pass12345")
        self.alice_cat = _make_cat(self.alice, "M", "Simba")
        self.bob_cat = _make_cat(self.bob, "F", "Luna")
        self.match = Match.objects.create(
            gato_emisor=self.alice_cat, gato_receptor=self.bob_cat, estado="ACEPTADO"
        )
        self.chat, _ = Chat.objects.get_or_create(match=self.match)

    def _url(self):
        return reverse("chat:enviar_mensaje", args=[self.chat.id])

    def test_anonymous_blocked(self):
        response = self.client.post(self._url(), {"contenido": "Hola"})
        self.assertEqual(response.status_code, 302)

    def test_get_not_allowed(self):
        self.client.login(username="alice", password="pass12345")
        response = self.client.get(self._url())
        self.assertEqual(response.status_code, 405)

    def test_empty_contenido_returns_400(self):
        self.client.login(username="alice", password="pass12345")
        response = self.client.post(self._url(), {"contenido": "   "})
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Message.objects.filter(chat=self.chat).exists())

    def test_valid_post_creates_message(self):
        self.client.login(username="alice", password="pass12345")
        response = self.client.post(self._url(), {"contenido": "Hola Bob!"})
        self.assertEqual(response.status_code, 200)
        mensaje = Message.objects.get(chat=self.chat)
        self.assertEqual(mensaje.remitente, self.alice)
        self.assertEqual(mensaje.contenido, "Hola Bob!")
        data = response.json()
        self.assertEqual(data["contenido"], "Hola Bob!")
        self.assertEqual(data["remitente_id"], self.alice.id)

    def test_non_participant_404s(self):
        self.client.login(username="carol", password="pass12345")
        response = self.client.post(self._url(), {"contenido": "Intento"})
        self.assertEqual(response.status_code, 404)


class MensajesNuevosViewTests(TestCase):

    def setUp(self):
        self.alice = User.objects.create_user(username="alice", password="pass12345")
        self.bob = User.objects.create_user(username="bob", password="pass12345")
        self.carol = User.objects.create_user(username="carol", password="pass12345")
        self.alice_cat = _make_cat(self.alice, "M", "Simba")
        self.bob_cat = _make_cat(self.bob, "F", "Luna")
        self.match = Match.objects.create(
            gato_emisor=self.alice_cat, gato_receptor=self.bob_cat, estado="ACEPTADO"
        )
        self.chat, _ = Chat.objects.get_or_create(match=self.match)
        self.msg1 = Message.objects.create(chat=self.chat, remitente=self.alice, contenido="Uno")
        self.msg2 = Message.objects.create(chat=self.chat, remitente=self.bob, contenido="Dos")

    def _url(self, desde_id=0):
        return f"{reverse('chat:mensajes_nuevos', args=[self.chat.id])}?desde_id={desde_id}"

    def test_anonymous_blocked(self):
        response = self.client.get(self._url())
        self.assertEqual(response.status_code, 302)

    def test_only_returns_messages_after_desde_id(self):
        self.client.login(username="alice", password="pass12345")
        response = self.client.get(self._url(desde_id=self.msg1.id))
        data = response.json()
        self.assertEqual(len(data["mensajes"]), 1)
        self.assertEqual(data["mensajes"][0]["id"], self.msg2.id)

    def test_es_mio_flag_is_correct(self):
        self.client.login(username="bob", password="pass12345")
        response = self.client.get(self._url(desde_id=0))
        data = response.json()
        por_id = {m["id"]: m["es_mio"] for m in data["mensajes"]}
        self.assertFalse(por_id[self.msg1.id])
        self.assertTrue(por_id[self.msg2.id])

    def test_non_participant_404s(self):
        self.client.login(username="carol", password="pass12345")
        response = self.client.get(self._url())
        self.assertEqual(response.status_code, 404)


class ChatViewSetAPITests(APITestCase):

    def setUp(self):
        self.alice = User.objects.create_user(username="alice", password="pass12345")
        self.bob = User.objects.create_user(username="bob", password="pass12345")
        self.carol = User.objects.create_user(username="carol", password="pass12345")
        self.alice_cat = _make_cat(self.alice, "M", "Simba")
        self.bob_cat = _make_cat(self.bob, "F", "Luna")
        self.match = Match.objects.create(
            gato_emisor=self.alice_cat, gato_receptor=self.bob_cat, estado="ACEPTADO"
        )
        self.chat, _ = Chat.objects.get_or_create(match=self.match)

    def test_anonymous_cannot_list(self):
        response = self.client.get(CHATS_URL)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_only_sees_own_chats(self):
        self.client.force_authenticate(self.carol)
        response = self.client.get(CHATS_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_participant_sees_chat(self):
        self.client.force_authenticate(self.alice)
        response = self.client.get(CHATS_URL)
        self.assertEqual(len(response.data), 1)

    def test_non_participant_gets_404_on_detail(self):
        self.client.force_authenticate(self.carol)
        response = self.client.get(f"{CHATS_URL}{self.chat.id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class MessageViewSetAPITests(APITestCase):

    def setUp(self):
        self.alice = User.objects.create_user(username="alice", password="pass12345")
        self.bob = User.objects.create_user(username="bob", password="pass12345")
        self.carol = User.objects.create_user(username="carol", password="pass12345")
        self.alice_cat = _make_cat(self.alice, "M", "Simba")
        self.bob_cat = _make_cat(self.bob, "F", "Luna")
        self.match = Match.objects.create(
            gato_emisor=self.alice_cat, gato_receptor=self.bob_cat, estado="ACEPTADO"
        )
        self.chat, _ = Chat.objects.get_or_create(match=self.match)
        self.message = Message.objects.create(chat=self.chat, remitente=self.alice, contenido="Hola")

    def test_anonymous_cannot_list(self):
        response = self.client.get(MESSAGES_URL)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_only_sees_own_messages(self):
        self.client.force_authenticate(self.carol)
        response = self.client.get(MESSAGES_URL)
        self.assertEqual(len(response.data), 0)

    def test_create_assigns_remitente_automatically(self):
        self.client.force_authenticate(self.bob)
        response = self.client.post(MESSAGES_URL, {"chat": self.chat.id, "contenido": "Respuesta"})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        created = Message.objects.get(pk=response.data["id"])
        self.assertEqual(created.remitente, self.bob)

    def test_non_participant_cannot_create(self):
        self.client.force_authenticate(self.carol)
        response = self.client.post(MESSAGES_URL, {"chat": self.chat.id, "contenido": "Intento"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
