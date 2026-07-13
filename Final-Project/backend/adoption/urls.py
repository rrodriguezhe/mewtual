from rest_framework.routers import DefaultRouter

from .views import AdoptionPostViewSet


router = DefaultRouter()

router.register(
    r"adoptions",
    AdoptionPostViewSet
)

urlpatterns = router.urls
