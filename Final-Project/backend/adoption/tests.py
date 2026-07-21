import datetime

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from cats.models import Cat

from .models import AdoptionPost

ADOPTIONS_URL = "/api/adoption/adoptions/"


class AdoptionPostPermissionTests(APITestCase):

    def setUp(self):
        self.alice = User.objects.create_user(username="alice", password="pass12345")
        self.bob = User.objects.create_user(username="bob", password="pass12345")
        self.staff = User.objects.create_user(
            username="mod", password="pass12345", is_staff=True
        )

        self.alice_cat = Cat.objects.create(
            owner=self.alice,
            nombre="Simba",
            raza="Angora",
            sexo="M",
            fecha_nacimiento=datetime.date(2024, 1, 1),
            peso=3.5,
            color="Blanco",
        )
        self.bob_cat = Cat.objects.create(
            owner=self.bob,
            nombre="Nala",
            raza="Bengalí",
            sexo="F",
            fecha_nacimiento=datetime.date(2024, 2, 1),
            peso=3.0,
            color="Naranja",
        )

        self.alice_post = AdoptionPost.objects.create(
            gato=self.alice_cat,
            descripcion="Cría de Simba en adopción",
        )

    def detail_url(self, post):
        return f"{ADOPTIONS_URL}{post.pk}/"

    def test_anonymous_cannot_list(self):
        response = self.client.get(ADOPTIONS_URL)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_authenticated_user_sees_all_posts(self):
        AdoptionPost.objects.create(
            gato=self.bob_cat,
            descripcion="Cría de Nala en adopción",
        )
        self.client.force_authenticate(self.bob)
        response = self.client.get(ADOPTIONS_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_user_can_create_post_for_own_cat(self):
        self.client.force_authenticate(self.bob)
        response = self.client.post(
            ADOPTIONS_URL,
            {"gato": self.bob_cat.pk, "descripcion": "Cría de Nala"},
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_user_cannot_create_post_for_others_cat(self):
        self.client.force_authenticate(self.bob)
        response = self.client.post(
            ADOPTIONS_URL,
            {"gato": self.alice_cat.pk, "descripcion": "Intento de publicar el gato de alice"},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_owner_can_update_own_post_estado(self):
        self.client.force_authenticate(self.alice)
        response = self.client.patch(
            self.detail_url(self.alice_post), {"estado": "RESERVADA"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.alice_post.refresh_from_db()
        self.assertEqual(self.alice_post.estado, "RESERVADA")

    def test_non_owner_cannot_update_post(self):
        self.client.force_authenticate(self.bob)
        response = self.client.patch(
            self.detail_url(self.alice_post), {"estado": "ADOPTADA"}
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_non_owner_cannot_delete_post(self):
        self.client.force_authenticate(self.bob)
        response = self.client.delete(self.detail_url(self.alice_post))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_staff_can_update_any_post(self):
        self.client.force_authenticate(self.staff)
        response = self.client.patch(
            self.detail_url(self.alice_post), {"estado": "ADOPTADA"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_staff_can_delete_any_post(self):
        self.client.force_authenticate(self.staff)
        response = self.client.delete(self.detail_url(self.alice_post))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class ListaPublicacionesViewTests(TestCase):

    def setUp(self):
        self.alice = User.objects.create_user(username="alice", password="pass12345")
        self.bob = User.objects.create_user(username="bob", password="pass12345")
        self.bob_cat = Cat.objects.create(
            owner=self.bob,
            nombre="Nala",
            raza="Bengalí",
            sexo="F",
            fecha_nacimiento=datetime.date(2024, 2, 1),
            peso=3.0,
            color="Naranja",
        )

    def test_post_from_active_owner_is_listed(self):
        AdoptionPost.objects.create(gato=self.bob_cat, descripcion="Cría de Nala en adopción")
        self.client.login(username="alice", password="pass12345")
        response = self.client.get(reverse("adoption:lista_publicaciones"))
        self.assertContains(response, "Nala")

    def test_post_from_inactive_owner_is_excluded(self):
        AdoptionPost.objects.create(gato=self.bob_cat, descripcion="Cría de Nala en adopción")
        self.bob.is_active = False
        self.bob.save()
        self.client.login(username="alice", password="pass12345")
        response = self.client.get(reverse("adoption:lista_publicaciones"))
        self.assertNotContains(response, "Nala")

    def test_card_links_to_cat_profile_page(self):
        post = AdoptionPost.objects.create(gato=self.bob_cat, descripcion="Cría de Nala en adopción")
        self.client.login(username="alice", password="pass12345")
        response = self.client.get(reverse("adoption:lista_publicaciones"))
        self.assertContains(response, reverse("cats:ver_perfil", args=[self.bob_cat.id]))
