from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import MatchViewSet

router = DefaultRouter()

router.register(
    r"matches",
    MatchViewSet
)

urlpatterns = [
    path("", include(router.urls)),
]