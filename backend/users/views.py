from rest_framework import viewsets
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from .models import Profile, Block
from .serializers import (
    UserSerializer,
    ProfileSerializer,
    BlockSerializer
)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class ProfileViewSet(viewsets.ModelViewSet):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer


class BlockViewSet(viewsets.ModelViewSet):
    queryset = Block.objects.all()
    serializer_class = BlockSerializer

def login_view(request):
    if request.method == 'POST':
        return redirect('matching:home') # Simulación de inicio de sesión exitoso
    return render(request, 'users/login.html')

def register_view(request):
    if request.method == 'POST':
        return redirect('users:login')
    return render(request, 'users/register.html')