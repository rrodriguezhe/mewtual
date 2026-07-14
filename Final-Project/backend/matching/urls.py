from django.urls import include, path
from rest_framework.routers import DefaultRouter
from . import views
from .views import MatchViewSet

router = DefaultRouter()

router.register(
    r"matches",
    MatchViewSet,
    basename="match"
)

app_name = 'matching'

urlpatterns = [
    path("", include(router.urls)),
    path('home/', views.home_view, name='home'),
    path('swipe/', views.swipe_view, name='swipe'),
    path('swipe/<int:candidato_id>/like/', views.registrar_swipe, {'decision': 'like'}, name='swipe_like'),
    path('swipe/<int:candidato_id>/rechazar/', views.registrar_swipe, {'decision': 'rechazar'}, name='swipe_rechazar'),
]
