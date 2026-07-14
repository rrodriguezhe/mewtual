from django.contrib.auth import views as auth_views
from django.urls import include, path, reverse_lazy
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
    path('cuenta/', views.mi_cuenta_view, name='mi_cuenta'),
    path('cuenta/eliminar/', views.eliminar_cuenta_view, name='eliminar_cuenta'),

    path('password-reset/', auth_views.PasswordResetView.as_view(
        template_name='users/password_reset.html',
        email_template_name='users/password_reset_email.html',
        subject_template_name='users/password_reset_subject.txt',
        success_url=reverse_lazy('users:password_reset_done'),
    ), name='password_reset'),

    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='users/password_reset_done.html',
    ), name='password_reset_done'),

    path('password-reset/confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='users/password_reset_confirm.html',
        success_url=reverse_lazy('users:password_reset_complete'),
    ), name='password_reset_confirm'),

    path('password-reset/complete/', auth_views.PasswordResetCompleteView.as_view(
        template_name='users/password_reset_complete.html',
    ), name='password_reset_complete'),
]
