import datetime
import tempfile
from unittest import mock

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from adoption.models import AdoptionPost

from .forms import CatForm, MedicalRecordForm, VaccineForm
from .models import Cat, MedicalRecord, Vaccine
from .views import calcular_edad, puede_cruce_responsable, vacunas_vigentes

CATS_API_URL = "/cats/api/"


def _make_cat(owner, sexo="M", nombre="Gato"):
    return Cat.objects.create(
        owner=owner,
        nombre=nombre,
        raza="Angora",
        sexo=sexo,
        fecha_nacimiento=datetime.date(2022, 1, 1),
        peso=3.5,
        color="Blanco",
    )


def _add_vigente_vaccine(cat):
    Vaccine.objects.create(
        gato=cat,
        nombre="Triple felina",
        fecha_aplicacion=datetime.date.today() - datetime.timedelta(days=30),
        fecha_vencimiento=datetime.date.today() + datetime.timedelta(days=300),
    )


def _add_certificado(cat, con_documento=True):
    registro = MedicalRecord(gato=cat, diagnostico_procedimiento="Chequeo general")
    if con_documento:
        registro.documento.save(
            "cert.txt", SimpleUploadedFile("cert.txt", b"contenido"), save=False
        )
    registro.save()
    return registro


def _make_apto_cat(owner, sexo="M", nombre="Gato"):
    cat = _make_cat(owner, sexo, nombre)
    _add_vigente_vaccine(cat)
    _add_certificado(cat)
    return cat


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class CatEligibilityHelperTests(TestCase):

    def setUp(self):
        self.owner = User.objects.create_user(username="alice", password="pass12345")

    @mock.patch("cats.views.date")
    def test_calcular_edad_before_birthday_this_year(self, mock_date):
        mock_date.today.return_value = datetime.date(2026, 6, 15)
        nacimiento = datetime.date(2020, 12, 31)
        self.assertEqual(calcular_edad(nacimiento), 5)

    @mock.patch("cats.views.date")
    def test_calcular_edad_after_birthday_this_year(self, mock_date):
        mock_date.today.return_value = datetime.date(2026, 6, 15)
        nacimiento = datetime.date(2020, 1, 1)
        self.assertEqual(calcular_edad(nacimiento), 6)

    @mock.patch("cats.views.date")
    def test_vacunas_vigentes_true_on_expiry_day(self, mock_date):
        mock_date.today.return_value = datetime.date(2026, 6, 15)
        cat = _make_cat(self.owner)
        Vaccine.objects.create(
            gato=cat,
            nombre="Rabia",
            fecha_aplicacion=datetime.date(2026, 1, 1),
            fecha_vencimiento=datetime.date(2026, 6, 15),
        )
        self.assertTrue(vacunas_vigentes(cat))

    @mock.patch("cats.views.date")
    def test_vacunas_vigentes_false_once_expired(self, mock_date):
        mock_date.today.return_value = datetime.date(2026, 6, 16)
        cat = _make_cat(self.owner)
        Vaccine.objects.create(
            gato=cat,
            nombre="Rabia",
            fecha_aplicacion=datetime.date(2026, 1, 1),
            fecha_vencimiento=datetime.date(2026, 6, 15),
        )
        self.assertFalse(vacunas_vigentes(cat))

    def test_vacunas_vigentes_false_without_vaccine(self):
        cat = _make_cat(self.owner)
        self.assertFalse(vacunas_vigentes(cat))

    def test_puede_cruce_responsable_true_with_all_requirements(self):
        cat = _make_apto_cat(self.owner)
        resultado = puede_cruce_responsable(cat)
        self.assertTrue(resultado["apto"])
        self.assertTrue(resultado["vacuna_vigente"])
        self.assertTrue(resultado["certificado_medico"])

    def test_puede_cruce_responsable_false_without_vaccine(self):
        cat = _make_cat(self.owner)
        _add_certificado(cat)
        self.assertFalse(puede_cruce_responsable(cat)["apto"])

    def test_puede_cruce_responsable_false_without_certificate(self):
        cat = _make_cat(self.owner)
        _add_vigente_vaccine(cat)
        self.assertFalse(puede_cruce_responsable(cat)["apto"])

    def test_medical_record_without_documento_does_not_count_as_certificate(self):
        cat = _make_cat(self.owner)
        _add_vigente_vaccine(cat)
        _add_certificado(cat, con_documento=False)
        resultado = puede_cruce_responsable(cat)
        self.assertFalse(resultado["certificado_medico"])
        self.assertFalse(resultado["apto"])

    def test_puede_cruce_responsable_false_when_esterilizado(self):
        cat = _make_apto_cat(self.owner)
        cat.esterilizado = True
        cat.save()
        self.assertFalse(puede_cruce_responsable(cat)["apto"])


class CatFormValidationTests(TestCase):

    def test_cat_form_valid_with_correct_data(self):
        form = CatForm(data={
            "nombre": "Simba", "raza": "Angora", "sexo": "M",
            "fecha_nacimiento": "2022-01-01", "peso": 3.5, "color": "Blanco",
        })
        self.assertTrue(form.is_valid(), form.errors)

    def test_cat_form_rejects_future_fecha_nacimiento(self):
        manana = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()
        form = CatForm(data={
            "nombre": "Simba", "raza": "Angora", "sexo": "M",
            "fecha_nacimiento": manana, "peso": 3.5, "color": "Blanco",
        })
        self.assertFalse(form.is_valid())
        self.assertIn("fecha_nacimiento", form.errors)

    def test_cat_form_rejects_non_positive_peso(self):
        form = CatForm(data={
            "nombre": "Simba", "raza": "Angora", "sexo": "M",
            "fecha_nacimiento": "2022-01-01", "peso": 0, "color": "Blanco",
        })
        self.assertFalse(form.is_valid())
        self.assertIn("peso", form.errors)

    def test_cat_form_rejects_esterilizado_and_modo_cruce_responsable_together(self):
        form = CatForm(data={
            "nombre": "Simba", "raza": "Angora", "sexo": "M",
            "fecha_nacimiento": "2022-01-01", "peso": 3.5, "color": "Blanco",
            "esterilizado": True, "modo_cruce_responsable": True,
        })
        self.assertFalse(form.is_valid())
        self.assertIn("modo_cruce_responsable", form.errors)

    def test_vaccine_form_empty_is_valid_and_has_no_data(self):
        form = VaccineForm(data={})
        self.assertTrue(form.is_valid())
        self.assertFalse(form.tiene_datos())

    def test_vaccine_form_requires_dates_once_nombre_filled(self):
        form = VaccineForm(data={"nombre": "Rabia"})
        self.assertFalse(form.is_valid())
        self.assertIn("fecha_aplicacion", form.errors)
        self.assertIn("fecha_vencimiento", form.errors)

    def test_vaccine_form_rejects_vencimiento_before_aplicacion(self):
        form = VaccineForm(data={
            "nombre": "Rabia",
            "fecha_aplicacion": "2024-06-01",
            "fecha_vencimiento": "2024-01-01",
        })
        self.assertFalse(form.is_valid())
        self.assertIn("fecha_vencimiento", form.errors)

    def test_medical_record_form_empty_is_valid_and_has_no_data(self):
        form = MedicalRecordForm(data={})
        self.assertTrue(form.is_valid())
        self.assertFalse(form.tiene_datos())

    def test_medical_record_form_requires_documento_once_diagnostico_filled(self):
        form = MedicalRecordForm(data={"diagnostico_procedimiento": "Chequeo"})
        self.assertFalse(form.is_valid())
        self.assertIn("documento", form.errors)


class CatTemplateViewOwnershipTests(TestCase):

    def setUp(self):
        self.alice = User.objects.create_user(username="alice", password="pass12345")
        self.bob = User.objects.create_user(username="bob", password="pass12345")
        self.alice_cat = _make_cat(self.alice, "M", "Simba")
        self.bob_cat = _make_cat(self.bob, "F", "Luna")

    def test_anonymous_redirected_to_login_on_mis_gatos(self):
        response = self.client.get(reverse("cats:mis_gatos"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("users:login"), response.url)

    def test_mis_gatos_only_lists_own_cats(self):
        self.client.login(username="alice", password="pass12345")
        response = self.client.get(reverse("cats:mis_gatos"))
        gatos = [item["obj"] for item in response.context["gatos"]]
        self.assertEqual(gatos, [self.alice_cat])

    def test_editar_perfil_404_for_others_cat(self):
        self.client.login(username="alice", password="pass12345")
        response = self.client.get(reverse("cats:editar_perfil", args=[self.bob_cat.pk]))
        self.assertEqual(response.status_code, 404)

    def test_eliminar_perfil_404_for_others_cat(self):
        self.client.login(username="alice", password="pass12345")
        response = self.client.post(reverse("cats:eliminar_perfil", args=[self.bob_cat.pk]))
        self.assertEqual(response.status_code, 404)

    def test_owner_can_delete_own_cat(self):
        self.client.login(username="alice", password="pass12345")
        response = self.client.post(reverse("cats:eliminar_perfil", args=[self.alice_cat.pk]))
        self.assertRedirects(response, reverse("cats:mis_gatos"))
        self.assertFalse(Cat.objects.filter(pk=self.alice_cat.pk).exists())

    def test_mis_gatos_list_row_has_no_editar_or_eliminar_link(self):
        self.client.login(username="alice", password="pass12345")
        response = self.client.get(reverse("cats:mis_gatos"))
        self.assertNotContains(response, reverse("cats:editar_perfil", args=[self.alice_cat.pk]))
        self.assertNotContains(response, reverse("cats:eliminar_perfil", args=[self.alice_cat.pk]))
        self.assertContains(response, reverse("cats:ver_perfil", args=[self.alice_cat.pk]))


class VerPerfilViewTests(TestCase):

    def setUp(self):
        self.alice = User.objects.create_user(username="alice", password="pass12345")
        self.bob = User.objects.create_user(username="bob", password="pass12345")
        self.bob_cat = _make_cat(self.bob, "F", "Luna")

    def detail_url(self):
        return reverse("cats:ver_perfil", args=[self.bob_cat.pk])

    def test_anonymous_redirected_to_login(self):
        response = self.client.get(self.detail_url())
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("users:login"), response.url)

    def test_nonexistent_cat_404s(self):
        self.client.login(username="alice", password="pass12345")
        response = self.client.get(reverse("cats:ver_perfil", args=[9999]))
        self.assertEqual(response.status_code, 404)

    def test_owner_sees_editar_and_eliminar_not_contactar_or_reportar(self):
        self.client.login(username="bob", password="pass12345")
        response = self.client.get(self.detail_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Editar")
        self.assertContains(response, reverse("cats:eliminar_perfil", args=[self.bob_cat.pk]))
        self.assertNotContains(response, "Contactar")
        self.assertNotContains(response, "Reportar")

    def test_non_owner_does_not_see_eliminar_link(self):
        self.client.login(username="alice", password="pass12345")
        response = self.client.get(self.detail_url())
        self.assertNotContains(response, reverse("cats:eliminar_perfil", args=[self.bob_cat.pk]))

    def test_non_owner_with_open_post_sees_contactar_and_reportar(self):
        AdoptionPost.objects.create(gato=self.bob_cat, descripcion="Luna en adopción")
        self.client.login(username="alice", password="pass12345")
        response = self.client.get(self.detail_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Contactar")
        self.assertContains(response, "Reportar")
        self.assertNotContains(response, "Editar")

    def test_non_owner_without_open_post_sees_only_reportar(self):
        self.client.login(username="alice", password="pass12345")
        response = self.client.get(self.detail_url())
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Contactar")
        self.assertContains(response, "Reportar")

    def test_non_disponible_post_hides_contactar(self):
        AdoptionPost.objects.create(gato=self.bob_cat, descripcion="Luna en adopción", estado="ADOPTADA")
        self.client.login(username="alice", password="pass12345")
        response = self.client.get(self.detail_url())
        self.assertNotContains(response, "Contactar")

    def test_non_owner_with_valid_gato_activo_sees_swipe_buttons(self):
        alice_cat = _make_cat(self.alice, "M", "Simba")
        self.client.login(username="alice", password="pass12345")
        response = self.client.get(self.detail_url(), {"gato_activo": alice_cat.pk})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse("matching:swipe_like", args=[self.bob_cat.pk]))
        self.assertContains(response, reverse("matching:swipe_rechazar", args=[self.bob_cat.pk]))
        self.assertContains(response, "Reportar")
        self.assertNotContains(response, "Contactar")

    def test_gato_activo_not_owned_by_viewer_is_ignored(self):
        carol = User.objects.create_user(username="carol", password="pass12345")
        carol_cat = _make_cat(carol, "M", "Milo")
        self.client.login(username="alice", password="pass12345")
        response = self.client.get(self.detail_url(), {"gato_activo": carol_cat.pk})
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, reverse("matching:swipe_like", args=[self.bob_cat.pk]))

    def test_invalid_gato_activo_param_does_not_crash(self):
        self.client.login(username="alice", password="pass12345")
        response = self.client.get(self.detail_url(), {"gato_activo": "abc"})
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, reverse("matching:swipe_like", args=[self.bob_cat.pk]))

    def test_owner_viewing_own_cat_ignores_gato_activo(self):
        bob_other_cat = _make_cat(self.bob, "M", "Toby")
        self.client.login(username="bob", password="pass12345")
        response = self.client.get(self.detail_url(), {"gato_activo": bob_other_cat.pk})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Editar")
        self.assertNotContains(response, reverse("matching:swipe_like", args=[self.bob_cat.pk]))


class CatViewSetAPITests(APITestCase):

    def setUp(self):
        self.alice = User.objects.create_user(username="alice", password="pass12345")
        self.bob = User.objects.create_user(username="bob", password="pass12345")
        self.alice_cat = _make_cat(self.alice, "M", "Simba")
        self.bob_cat = _make_cat(self.bob, "F", "Luna")

    def test_anonymous_cannot_list(self):
        response = self.client.get(CATS_API_URL)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_only_sees_own_cats_in_list(self):
        self.client.force_authenticate(self.bob)
        response = self.client.get(CATS_API_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        returned_ids = {item["id"] for item in response.data}
        self.assertEqual(returned_ids, {self.bob_cat.pk})

    def test_user_cannot_retrieve_others_cat(self):
        self.client.force_authenticate(self.bob)
        response = self.client.get(f"{CATS_API_URL}{self.alice_cat.pk}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_assigns_owner_automatically(self):
        self.client.force_authenticate(self.bob)
        response = self.client.post(CATS_API_URL, {
            "nombre": "Nuevo", "raza": "Criollo", "sexo": "M",
            "fecha_nacimiento": "2023-01-01", "peso": 3.2, "color": "Gris",
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        created = Cat.objects.get(pk=response.data["id"])
        self.assertEqual(created.owner, self.bob)
