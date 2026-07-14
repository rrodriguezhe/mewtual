from django.urls import path

from . import views

app_name = "reports"

urlpatterns = [
    path("nuevo/", views.crear_reporte, name="crear_reporte"),
    path("mis-reportes/", views.mis_reportes, name="mis_reportes"),
]
