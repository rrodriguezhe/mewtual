from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Report

REPORTS_URL = "/api/reports/reports/"


class ReportPermissionTests(APITestCase):

    def setUp(self):
        self.alice = User.objects.create_user(username="alice", password="pass12345")
        self.bob = User.objects.create_user(username="bob", password="pass12345")
        self.staff = User.objects.create_user(
            username="mod", password="pass12345", is_staff=True
        )
        self.report = Report.objects.create(
            usuario_reportante=self.alice,
            usuario_reportado=self.bob,
            motivo="Lenguaje ofensivo en el chat",
        )

    def detail_url(self, report):
        return f"{REPORTS_URL}{report.pk}/"

    def test_anonymous_cannot_list(self):
        # With only SessionAuthentication configured, an anonymous request
        # "succeeds" authentication as AnonymousUser, so IsAuthenticated
        # denies with 403 rather than 401 here.
        response = self.client.get(REPORTS_URL)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_anonymous_cannot_create(self):
        response = self.client.post(
            REPORTS_URL,
            {"usuario_reportado": self.bob.pk, "motivo": "Spam"},
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_authenticated_user_can_create_report(self):
        self.client.force_authenticate(self.bob)
        response = self.client.post(
            REPORTS_URL,
            {"usuario_reportado": self.alice.pk, "motivo": "Comportamiento inapropiado"},
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_usuario_reportante_is_forced_to_request_user(self):
        self.client.force_authenticate(self.bob)
        response = self.client.post(
            REPORTS_URL,
            {
                "usuario_reportado": self.alice.pk,
                "usuario_reportante": self.staff.pk,
                "motivo": "Intento de suplantar al reportante",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        created = Report.objects.get(pk=response.data["id"])
        self.assertEqual(created.usuario_reportante, self.bob)

    def test_cannot_report_self(self):
        self.client.force_authenticate(self.bob)
        response = self.client.post(
            REPORTS_URL,
            {"usuario_reportado": self.bob.pk, "motivo": "Auto-reporte"},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_non_staff_user_only_sees_reports_they_filed(self):
        Report.objects.create(
            usuario_reportante=self.bob,
            usuario_reportado=self.alice,
            motivo="Otro reporte, de bob hacia alice",
        )
        self.client.force_authenticate(self.alice)
        response = self.client.get(REPORTS_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        returned_ids = {item["id"] for item in response.data}
        self.assertEqual(returned_ids, {self.report.pk})

    def test_non_staff_user_cannot_update_report(self):
        self.client.force_authenticate(self.alice)
        response = self.client.patch(
            self.detail_url(self.report), {"estado": "REVISADO"}
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_non_staff_user_cannot_delete_report(self):
        self.client.force_authenticate(self.alice)
        response = self.client.delete(self.detail_url(self.report))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_non_staff_user_cannot_set_estado_on_create(self):
        self.client.force_authenticate(self.bob)
        response = self.client.post(
            REPORTS_URL,
            {
                "usuario_reportado": self.alice.pk,
                "motivo": "Intento de auto-cerrar el reporte",
                "estado": "CERRADO",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        created = Report.objects.get(pk=response.data["id"])
        self.assertEqual(created.estado, "PENDIENTE")

    def test_staff_sees_all_reports(self):
        Report.objects.create(
            usuario_reportante=self.bob,
            usuario_reportado=self.alice,
            motivo="Otro reporte, de bob hacia alice",
        )
        self.client.force_authenticate(self.staff)
        response = self.client.get(REPORTS_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_staff_can_update_estado(self):
        self.client.force_authenticate(self.staff)
        response = self.client.patch(
            self.detail_url(self.report), {"estado": "REVISADO"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.report.refresh_from_db()
        self.assertEqual(self.report.estado, "REVISADO")
