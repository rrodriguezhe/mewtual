from django.urls import path

from . import views

app_name = "adoption"

urlpatterns = [
    path("", views.lista_publicaciones, name="lista_publicaciones"),
    path("<int:post_id>/", views.detalle_publicacion, name="detalle_publicacion"),
    path("mis-publicaciones/", views.mis_publicaciones, name="mis_publicaciones"),
    path("nueva/", views.crear_publicacion, name="crear_publicacion"),
    path("<int:post_id>/editar/", views.editar_publicacion, name="editar_publicacion"),
    path("<int:post_id>/eliminar/", views.eliminar_publicacion, name="eliminar_publicacion"),
]
