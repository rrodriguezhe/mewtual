from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views
from .views import CatViewSet

router = DefaultRouter()
router.register(r"", CatViewSet, basename="cat-api")

app_name = "cats"

urlpatterns = [
    # Vistas de plantilla
    path("mis_gatos/", views.mis_gatos, name="mis_gatos"),
    path("nuevo/", views.crear_perfil, name="crear_perfil"),
    path("<int:cat_id>/", views.ver_perfil, name="ver_perfil"),
    path("<int:cat_id>/editar/", views.editar_perfil, name="editar_perfil"),
    path("<int:cat_id>/eliminar/", views.eliminar_perfil, name="eliminar_perfil"),
    path("<int:cat_id>/fotos/subir/", views.subir_foto, name="subir_foto"),
    path("<int:cat_id>/fotos/reordenar/", views.reordenar_fotos, name="reordenar_fotos"),
    path("foto/<int:foto_id>/eliminar/", views.eliminar_foto, name="eliminar_foto"),
    path("vacuna/<int:vacuna_id>/eliminar/", views.eliminar_vacuna, name="eliminar_vacuna"),
    path("registro/<int:registro_id>/eliminar/", views.eliminar_registro_medico, name="eliminar_registro_medico"),

    # API REST
    path("api/", include(router.urls)),
]
