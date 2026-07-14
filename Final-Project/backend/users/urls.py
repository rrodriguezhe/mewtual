from django.urls import include, path
from rest_framework.routers import DefaultRouter
from . import views

from .views import (
    UserViewSet,
    ProfileViewSet,
    BlockViewSet
)

router = DefaultRouter()

router.register(r'users', UserViewSet)
router.register(r'profiles', ProfileViewSet, basename='profile')
router.register(r'blocks', BlockViewSet, basename='block')

app_name = 'users'

urlpatterns = [
    path('', include(router.urls)),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
]
