import datetime
import tempfile

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from cats.models import Cat, MedicalRecord, Vaccine

from .models import Match

SWIPE_URL = "/matching/swipe/"
MATCHES_URL = "/matching/matches/"


def _make_apto_cat(owner, sexo="M", nombre="Gato"):
    cat = Cat.objects.create(
        owner=owner,
        nombre=nombre,
        raza="Criollo",
        sexo=sexo,
        fecha_nacimiento=datetime.date(2022, 1, 1),
        peso=3.5,
        color="Gris",
    )
    Vaccine.objects.create(
        gato=cat,
        nombre="Triple felina",
        fecha_aplicacion=datetime.date.today() - datetime.timedelta(days=30),
        fecha_vencimiento=datetime.date.today() + datetime.timedelta(days=300),
    )
    registro = MedicalRecord(gato=cat, diagnostico_procedimiento="Chequeo general")
    registro.documento.save(
        "cert.txt", SimpleUploadedFile("cert.txt", b"contenido"), save=False
    )
    registro.save()
    return cat


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class SwipeViewCandidateTests(TestCase):

    def setUp(self):
        self.alice = User.objects.create_user(username="alice", password="pass12345")
        self.bob = User.objects.create_user(username="bob", password="pass12345")

    def test_anonymous_redirected_to_login(self):
        response = self.client.get(SWIPE_URL)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("users:login"), response.url)

    def test_user_without_eligible_cat_redirected_to_mis_gatos(self):
        Cat.objects.create(
            owner=self.alice, nombre="SinVacuna", raza="Criollo", sexo="M",
            fecha_nacimiento=datetime.date(2022, 1, 1), peso=3.0, color="Negro",
        )
        self.client.login(username="alice", password="pass12345")
        response = self.client.get(SWIPE_URL)
        self.assertRedirects(response, reverse("cats:mis_gatos"))

    def test_candidate_must_be_opposite_sex(self):
        _make_apto_cat(self.alice, "M", "Simba")
        _make_apto_cat(self.bob, "M", "Milo")
        self.client.login(username="alice", password="pass12345")
        response = self.client.get(SWIPE_URL)
        self.assertIsNone(response.context["candidato"])

    def test_candidate_excludes_ineligible_cats(self):
        _make_apto_cat(self.alice, "M", "Simba")
        Cat.objects.create(
            owner=self.bob, nombre="NoApta", raza="Criollo", sexo="F",
            fecha_nacimiento=datetime.date(2022, 1, 1), peso=3.0, color="Blanco",
        )
        self.client.login(username="alice", password="pass12345")
        response = self.client.get(SWIPE_URL)
        self.assertIsNone(response.context["candidato"])

    def test_candidate_excludes_own_other_cats(self):
        _make_apto_cat(self.alice, "M", "Simba")
        _make_apto_cat(self.alice, "F", "Luna")
        self.client.login(username="alice", password="pass12345")
        response = self.client.get(SWIPE_URL)
        self.assertIsNone(response.context["candidato"])

    def test_candidate_shown_when_eligible(self):
        _make_apto_cat(self.alice, "M", "Simba")
        bob_cat = _make_apto_cat(self.bob, "F", "Luna")
        self.client.login(username="alice", password="pass12345")
        response = self.client.get(SWIPE_URL)
        self.assertEqual(response.context["candidato"], bob_cat)

    def test_excludes_cat_already_swiped_as_emisor(self):
        alice_cat = _make_apto_cat(self.alice, "M", "Simba")
        bob_cat = _make_apto_cat(self.bob, "F", "Luna")
        Match.objects.create(gato_emisor=alice_cat, gato_receptor=bob_cat, estado="RECHAZADO")
        self.client.login(username="alice", password="pass12345")
        response = self.client.get(SWIPE_URL)
        self.assertIsNone(response.context["candidato"])

    def test_pending_incoming_match_does_not_exclude_candidate(self):
        # Regla asimétrica de swipe_view: un match entrante aún PENDIENTE
        # no oculta al candidato (se sigue mostrando para poder responder).
        alice_cat = _make_apto_cat(self.alice, "M", "Simba")
        bob_cat = _make_apto_cat(self.bob, "F", "Luna")
        Match.objects.create(gato_emisor=bob_cat, gato_receptor=alice_cat, estado="PENDIENTE")
        self.client.login(username="alice", password="pass12345")
        response = self.client.get(SWIPE_URL)
        self.assertEqual(response.context["candidato"], bob_cat)

    def test_accepted_incoming_match_excludes_candidate(self):
        alice_cat = _make_apto_cat(self.alice, "M", "Simba")
        bob_cat = _make_apto_cat(self.bob, "F", "Luna")
        Match.objects.create(gato_emisor=bob_cat, gato_receptor=alice_cat, estado="ACEPTADO")
        self.client.login(username="alice", password="pass12345")
        response = self.client.get(SWIPE_URL)
        self.assertIsNone(response.context["candidato"])

    def test_explicit_gato_id_selects_active_cat(self):
        _make_apto_cat(self.alice, "M", "Simba")
        milo = _make_apto_cat(self.alice, "M", "Milo")
        self.client.login(username="alice", password="pass12345")
        response = self.client.get(SWIPE_URL, {"gato_id": milo.pk})
        self.assertEqual(response.context["gato_activo"], milo)

    def test_explicit_gato_id_for_ineligible_cat_redirects_with_error(self):
        _make_apto_cat(self.alice, "M", "Simba")
        no_apto = Cat.objects.create(
            owner=self.alice, nombre="NoApto", raza="Criollo", sexo="M",
            fecha_nacimiento=datetime.date(2022, 1, 1), peso=3.0, color="Negro",
        )
        self.client.login(username="alice", password="pass12345")
        response = self.client.get(SWIPE_URL, {"gato_id": no_apto.pk})
        self.assertRedirects(response, reverse("cats:mis_gatos"))

    def test_explicit_gato_id_for_others_cat_404s(self):
        _make_apto_cat(self.alice, "M", "Simba")
        bob_cat = _make_apto_cat(self.bob, "F", "Luna")
        self.client.login(username="alice", password="pass12345")
        response = self.client.get(SWIPE_URL, {"gato_id": bob_cat.pk})
        self.assertEqual(response.status_code, 404)


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class MatchViewSetAPITests(APITestCase):

    def setUp(self):
        self.alice = User.objects.create_user(username="alice", password="pass12345")
        self.bob = User.objects.create_user(username="bob", password="pass12345")
        self.carol = User.objects.create_user(username="carol", password="pass12345")
        self.staff = User.objects.create_user(
            username="mod", password="pass12345", is_staff=True
        )

        self.alice_cat = _make_apto_cat(self.alice, "M", "Simba")
        self.bob_cat = _make_apto_cat(self.bob, "F", "Luna")
        self.carol_cat = _make_apto_cat(self.carol, "F", "Nala")

        self.match = Match.objects.create(
            gato_emisor=self.alice_cat, gato_receptor=self.bob_cat, estado="PENDIENTE"
        )

    def detail_url(self, match):
        return f"{MATCHES_URL}{match.pk}/"

    def test_anonymous_cannot_list(self):
        response = self.client.get(MATCHES_URL)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_only_sees_matches_involving_own_cats(self):
        self.client.force_authenticate(self.carol)
        response = self.client.get(MATCHES_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_participant_sees_their_match(self):
        self.client.force_authenticate(self.bob)
        response = self.client.get(MATCHES_URL)
        self.assertEqual(len(response.data), 1)

    def test_user_can_create_match_from_own_cat(self):
        self.client.force_authenticate(self.carol)
        response = self.client.post(MATCHES_URL, {
            "gato_emisor": self.carol_cat.pk,
            "gato_receptor": self.alice_cat.pk,
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_cannot_create_match_impersonating_others_cat_as_emisor(self):
        self.client.force_authenticate(self.carol)
        response = self.client.post(MATCHES_URL, {
            "gato_emisor": self.alice_cat.pk,
            "gato_receptor": self.bob_cat.pk,
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_non_participant_gets_404_updating_match(self):
        # get_queryset ya scopa la visibilidad por participante: si carol no
        # participa, el match no aparece en su queryset y el PATCH da 404,
        # no 403 (nunca llega a evaluarse el permiso a nivel de objeto).
        self.client.force_authenticate(self.carol)
        response = self.client.patch(self.detail_url(self.match), {"estado": "ACEPTADO"})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_participant_can_update_match_estado(self):
        self.client.force_authenticate(self.bob)
        response = self.client.patch(self.detail_url(self.match), {"estado": "ACEPTADO"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.match.refresh_from_db()
        self.assertEqual(self.match.estado, "ACEPTADO")

    def test_staff_sees_and_updates_any_match(self):
        self.client.force_authenticate(self.staff)
        response = self.client.get(MATCHES_URL)
        self.assertEqual(len(response.data), 1)
        response = self.client.patch(self.detail_url(self.match), {"estado": "RECHAZADO"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
