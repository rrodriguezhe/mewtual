from django.urls import include, path
from rest_framework.routers import DefaultRouter
from . import views
from .views import CatViewSet

router = DefaultRouter()
router.register(r'', CatViewSet)

app_name = 'cats'

urlpatterns = [
    path('mis_gatos/', views.mis_gatos, name='mis_gatos'),
    path('nuevo/', views.crear_perfil, name='crear_perfil'),
    path('editar/', views.editar_perfil, name='editar_perfil'),
    path('', include(router.urls)),
]