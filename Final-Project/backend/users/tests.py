import io
import os
import re

from django.contrib.auth.models import User
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from PIL import Image
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Block, Profile


def _make_valid_png(name="foto.png", content_type="image/png"):
    """Imagen PNG pequeña y válida (Pillow) para tests de subida."""
    buffer = io.BytesIO()
    Image.new("RGB", (10, 10), color="red").save(buffer, format="PNG")
    return SimpleUploadedFile(name, buffer.getvalue(), content_type=content_type)


def _make_oversized_png(name="foto_grande.png", content_type="image/png"):
    """
    PNG real (Pillow lo puede abrir) pero de ruido aleatorio sin comprimir,
    para garantizar que supere el límite de 5 MB sin depender de relleno
    de bytes que Pillow podría rechazar al parsear.
    """
    buffer = io.BytesIO()
    width, height = 1400, 1400
    img = Image.frombytes("RGB", (width, height), os.urandom(width * height * 3))
    img.save(buffer, format="PNG", compress_level=0)
    return SimpleUploadedFile(name, buffer.getvalue(), content_type=content_type)

USERS_API_URL = "/users/users/"
PROFILES_API_URL = "/users/profiles/"
BLOCKS_API_URL = "/users/blocks/"


class LoginViewTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="alice", email="alice@example.com", password="StrongPass123!"
        )

    def test_login_with_username_and_correct_password(self):
        response = self.client.post(reverse("users:login"), {
            "email": "alice", "password": "StrongPass123!",
        })
        # No assertRedirects here: swipe_view itself redirects again for a
        # cat-less user, so we only check login's own target, not that
        # target's response.
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("matching:swipe"))
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_login_with_email_and_correct_password(self):
        response = self.client.post(reverse("users:login"), {
            "email": "alice@example.com", "password": "StrongPass123!",
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("matching:swipe"))
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_login_with_incorrect_password(self):
        response = self.client.post(reverse("users:login"), {
            "email": "alice", "password": "wrong",
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_login_with_unknown_identifier(self):
        response = self.client.post(reverse("users:login"), {
            "email": "nadie", "password": "wrong",
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_login_with_missing_fields(self):
        response = self.client.post(reverse("users:login"), {"email": "", "password": ""})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_get_request_renders_login_page(self):
        response = self.client.get(reverse("users:login"))
        self.assertEqual(response.status_code, 200)


class RegisterViewTests(TestCase):

    def _valid_payload(self, **overrides):
        payload = {
            "username": "bob",
            "email": "bob@example.com",
            "password": "Sup3rStrongPass!9",
            "confirm_password": "Sup3rStrongPass!9",
        }
        payload.update(overrides)
        return payload

    def test_register_creates_user_and_profile(self):
        self.client.post(reverse("users:register"), self._valid_payload())
        user = User.objects.get(username="bob")
        self.assertTrue(Profile.objects.filter(user=user).exists())

    def test_register_logs_in_after_success(self):
        response = self.client.post(reverse("users:register"), self._valid_payload())
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("matching:swipe"))
        self.assertTrue(response.wsgi_request.user.is_authenticated)
        self.assertEqual(response.wsgi_request.user.username, "bob")

    def test_register_rejects_empty_fields(self):
        response = self.client.post(reverse("users:register"), self._valid_payload(username=""))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(email="bob@example.com").exists())

    def test_register_rejects_password_mismatch(self):
        response = self.client.post(
            reverse("users:register"), self._valid_payload(confirm_password="different")
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="bob").exists())

    def test_register_rejects_duplicate_username(self):
        User.objects.create_user(username="bob", email="other@example.com", password="whatever123")
        response = self.client.post(reverse("users:register"), self._valid_payload())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.filter(username="bob").count(), 1)

    def test_register_rejects_duplicate_email(self):
        User.objects.create_user(username="other", email="bob@example.com", password="whatever123")
        response = self.client.post(reverse("users:register"), self._valid_payload())
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="bob").exists())

    def test_register_rejects_weak_password(self):
        response = self.client.post(reverse("users:register"), self._valid_payload(
            password="password", confirm_password="password"
        ))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="bob").exists())

    def test_get_request_renders_register_page(self):
        response = self.client.get(reverse("users:register"))
        self.assertEqual(response.status_code, 200)


class LogoutViewTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username="alice", password="StrongPass123!")

    def test_logout_clears_session_and_redirects(self):
        self.client.login(username="alice", password="StrongPass123!")
        response = self.client.get(reverse("users:logout"))
        self.assertRedirects(response, reverse("users:login"))
        self.assertFalse(response.wsgi_request.user.is_authenticated)


class MiCuentaViewTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="alice", email="alice@example.com", password="StrongPass123!"
        )

    def test_anonymous_redirected_to_login(self):
        response = self.client.get(reverse("users:mi_cuenta"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("users:login"), response.url)

    def test_logged_in_user_sees_own_account_info(self):
        self.client.login(username="alice", password="StrongPass123!")
        response = self.client.get(reverse("users:mi_cuenta"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "alice")
        self.assertContains(response, "alice@example.com")

    def test_get_prefills_form_with_current_values(self):
        self.user.first_name = "Ana"
        self.user.last_name = "Perez"
        self.user.save()
        self.client.login(username="alice", password="StrongPass123!")
        response = self.client.get(reverse("users:mi_cuenta"))
        self.assertContains(response, 'value="Ana"')
        self.assertContains(response, 'value="Perez"')

    def test_post_updates_name(self):
        self.client.login(username="alice", password="StrongPass123!")
        response = self.client.post(reverse("users:mi_cuenta"), {
            "first_name": "Ana",
            "last_name": "Perez",
        })
        self.assertRedirects(response, reverse("users:mi_cuenta"))
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Ana")
        self.assertEqual(self.user.last_name, "Perez")

    def test_post_updates_profile_picture(self):
        self.client.login(username="alice", password="StrongPass123!")
        response = self.client.post(reverse("users:mi_cuenta"), {
            "first_name": "",
            "last_name": "",
            "foto_perfil": _make_valid_png(),
        })
        self.assertRedirects(response, reverse("users:mi_cuenta"))
        profile = Profile.objects.get(user=self.user)
        self.assertTrue(bool(profile.foto_perfil))

    def test_post_rejects_oversized_image(self):
        self.client.login(username="alice", password="StrongPass123!")
        response = self.client.post(reverse("users:mi_cuenta"), {
            "first_name": "",
            "last_name": "",
            "foto_perfil": _make_oversized_png(),
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "no puede superar 5 MB")
        profile = Profile.objects.get(user=self.user)
        self.assertFalse(bool(profile.foto_perfil))

    def test_post_rejects_invalid_content_type(self):
        self.client.login(username="alice", password="StrongPass123!")
        bad_file = SimpleUploadedFile(
            "foto.txt", b"no es una imagen", content_type="text/plain"
        )
        response = self.client.post(reverse("users:mi_cuenta"), {
            "first_name": "",
            "last_name": "",
            "foto_perfil": bad_file,
        })
        self.assertEqual(response.status_code, 200)
        profile = Profile.objects.get(user=self.user)
        self.assertFalse(bool(profile.foto_perfil))

    def test_staff_without_profile_can_load_mi_cuenta(self):
        staff_user = User.objects.create_user(
            username="staffer", email="staff@example.com",
            password="StrongPass123!", is_staff=True,
        )
        self.assertFalse(Profile.objects.filter(user=staff_user).exists())
        self.client.login(username="staffer", password="StrongPass123!")
        response = self.client.get(reverse("users:mi_cuenta"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Profile.objects.filter(user=staff_user).exists())


class PasswordResetFlowTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="alice", email="alice@example.com", password="OldPass123!"
        )

    def test_request_reset_for_real_email_sends_one_message(self):
        response = self.client.post(reverse("users:password_reset"), {"email": "alice@example.com"})
        self.assertRedirects(response, reverse("users:password_reset_done"))
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("alice@example.com", mail.outbox[0].to)

    def test_request_reset_for_unknown_email_sends_nothing_but_still_succeeds(self):
        # Django deliberately doesn't reveal whether an email is registered.
        response = self.client.post(reverse("users:password_reset"), {"email": "nadie@example.com"})
        self.assertRedirects(response, reverse("users:password_reset_done"))
        self.assertEqual(len(mail.outbox), 0)

    def test_following_emailed_link_and_setting_new_password_works(self):
        self.client.post(reverse("users:password_reset"), {"email": "alice@example.com"})
        body = mail.outbox[0].body
        match = re.search(r"(/users/password-reset/confirm/\S+/\S+/)", body)
        self.assertIsNotNone(match)
        confirm_url = match.group(1)

        response = self.client.get(confirm_url, follow=True)
        self.assertEqual(response.status_code, 200)
        set_password_url = response.redirect_chain[-1][0]

        response = self.client.post(set_password_url, {
            "new_password1": "BrandNewPass456!",
            "new_password2": "BrandNewPass456!",
        })
        self.assertRedirects(response, reverse("users:password_reset_complete"))

        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("BrandNewPass456!"))
        self.assertFalse(self.user.check_password("OldPass123!"))

    def test_invalid_token_shows_invalid_link_state(self):
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        response = self.client.get(
            reverse("users:password_reset_confirm", kwargs={"uidb64": uid, "token": "bogus-token"}),
            follow=True,
        )
        self.assertContains(response, "ya no es válido")


class UserViewSetAPITests(APITestCase):

    def setUp(self):
        self.alice = User.objects.create_user(username="alice", password="pass12345")
        self.bob = User.objects.create_user(username="bob", password="pass12345")

    def test_anonymous_cannot_list(self):
        response = self.client.get(USERS_API_URL)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_authenticated_user_can_list_all_users(self):
        self.client.force_authenticate(self.alice)
        response = self.client.get(USERS_API_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        returned_ids = {item["id"] for item in response.data}
        self.assertEqual(returned_ids, {self.alice.pk, self.bob.pk})

    def test_create_not_allowed(self):
        self.client.force_authenticate(self.alice)
        response = self.client.post(USERS_API_URL, {"username": "carol"})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_not_allowed(self):
        self.client.force_authenticate(self.alice)
        response = self.client.patch(f"{USERS_API_URL}{self.bob.pk}/", {"first_name": "X"})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_delete_not_allowed(self):
        self.client.force_authenticate(self.alice)
        response = self.client.delete(f"{USERS_API_URL}{self.bob.pk}/")
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class ProfileViewSetAPITests(APITestCase):

    def setUp(self):
        self.alice = User.objects.create_user(username="alice", password="pass12345")
        self.bob = User.objects.create_user(username="bob", password="pass12345")
        self.staff = User.objects.create_user(
            username="mod", password="pass12345", is_staff=True
        )
        self.alice_profile = Profile.objects.create(user=self.alice)
        self.bob_profile = Profile.objects.create(user=self.bob)

    def detail_url(self, profile):
        return f"{PROFILES_API_URL}{profile.pk}/"

    def test_anonymous_cannot_list(self):
        response = self.client.get(PROFILES_API_URL)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_only_sees_own_profile(self):
        self.client.force_authenticate(self.alice)
        response = self.client.get(PROFILES_API_URL)
        returned_ids = {item["id"] for item in response.data}
        self.assertEqual(returned_ids, {self.alice_profile.pk})

    def test_create_assigns_user_automatically(self):
        carol = User.objects.create_user(username="carol", password="pass12345")
        self.client.force_authenticate(carol)
        response = self.client.post(PROFILES_API_URL, {})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        created = Profile.objects.get(pk=response.data["id"])
        self.assertEqual(created.user, carol)

    def test_owner_can_update_own_profile(self):
        self.client.force_authenticate(self.alice)
        response = self.client.patch(
            self.detail_url(self.alice_profile), {"preferencia_interfaz": "oscuro"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.alice_profile.refresh_from_db()
        self.assertEqual(self.alice_profile.preferencia_interfaz, "oscuro")

    def test_non_owner_gets_404_updating_others_profile(self):
        # get_queryset ya scopa la visibilidad al propio perfil: si bob no es
        # el dueño, el perfil de alice ni siquiera aparece en su queryset, así
        # que el PATCH da 404, no 403 (nunca se evalúa el permiso de objeto).
        self.client.force_authenticate(self.bob)
        response = self.client.patch(
            self.detail_url(self.alice_profile), {"preferencia_interfaz": "oscuro"}
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_staff_sees_all_profiles(self):
        self.client.force_authenticate(self.staff)
        response = self.client.get(PROFILES_API_URL)
        self.assertEqual(len(response.data), 2)


class BlockViewSetAPITests(APITestCase):

    def setUp(self):
        self.alice = User.objects.create_user(username="alice", password="pass12345")
        self.bob = User.objects.create_user(username="bob", password="pass12345")
        self.carol = User.objects.create_user(username="carol", password="pass12345")
        self.block = Block.objects.create(usuario_bloqueador=self.alice, usuario_bloqueado=self.bob)

    def detail_url(self, block):
        return f"{BLOCKS_API_URL}{block.pk}/"

    def test_anonymous_cannot_list(self):
        response = self.client.get(BLOCKS_API_URL)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_only_sees_own_blocks(self):
        self.client.force_authenticate(self.alice)
        response = self.client.get(BLOCKS_API_URL)
        returned_ids = {item["id"] for item in response.data}
        self.assertEqual(returned_ids, {self.block.pk})

    def test_other_user_sees_no_blocks(self):
        self.client.force_authenticate(self.carol)
        response = self.client.get(BLOCKS_API_URL)
        self.assertEqual(len(response.data), 0)

    def test_create_assigns_blocker_automatically(self):
        self.client.force_authenticate(self.carol)
        response = self.client.post(BLOCKS_API_URL, {"usuario_bloqueado": self.bob.pk})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        created = Block.objects.get(pk=response.data["id"])
        self.assertEqual(created.usuario_bloqueador, self.carol)

    def test_non_owner_gets_404_accessing_others_block(self):
        # Igual que ProfileViewSet: get_queryset ya scopa por
        # usuario_bloqueador, así que un bloqueo ajeno no aparece en el
        # queryset de otro usuario y el intento de acceder da 404.
        self.client.force_authenticate(self.bob)
        response = self.client.get(self.detail_url(self.block))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
