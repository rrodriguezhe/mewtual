from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CatViewSet

router = DefaultRouter()
router.register(r'', CatViewSet)

urlpatterns = [
    path('', include(router.urls)),
]