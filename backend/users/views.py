from rest_framework import viewsets
from django.contrib import messages
from django.db import transaction
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.contrib.auth import authenticate, login, logout
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
        email_or_username = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')

        if not email_or_username or not password:
            messages.error(request, "Por favor, ingresa tu correo y contraseña.")
            return render(request, 'users/login.html')

        try:
            user_obj = User.objects.get(email=email_or_username)
            username_to_auth = user_obj.username
        except User.DoesNotExist:
            username_to_auth = email_or_username

        user = authenticate(request, username=username_to_auth, password=password)

        if user is not None:
            login(request, user)
            return redirect('matching:home')
        else:
            messages.error(request, "Correo electrónico o contraseña incorrectos.")
            return render(request, 'users/login.html')

    return render(request, 'users/login.html')

def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')

        # Validar campos vacíos
        if not username or not email or not password or not confirm_password:
            messages.error(request, "Por favor, completa todos los campos.")
            return render(request, 'users/register.html')

        # Validar que las contraseñas coincidan
        if password != confirm_password:
            messages.error(request, "Las contraseñas no coinciden.")
            return render(request, 'users/register.html')

        # Validar que el nombre de usuario y email no existan
        if User.objects.filter(username=username).exists():
            messages.error(request, "Este nombre de usuario ya está en uso. Elige otro.")
            return render(request, 'users/register.html')

        if User.objects.filter(email=email).exists():
            messages.error(request, "Este correo electrónico ya está registrado.")
            return render(request, 'users/register.html')
 
        try:
            user_temp = User(username=username, email=email)
            validate_password(password, user=user_temp)
        except ValidationError as e:
            # Mostrar errores en pantalla
            for error in e.messages:
                messages.error(request, error)
            return render(request, 'users/register.html')
        
        #Crear el usuario en User y en Profile
        try:
            with transaction.atomic():
                new_user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password
                )
                Profile.objects.create(user=new_user)
            messages.success(request, "Cuenta creada exitosamente. Inicia sesión para continuar.")
            return redirect('users:login')   # ← en lugar de login() + redirect a home
            
        except Exception as e:
            messages.error(request, "Ocurrió un error inesperado al crear la cuenta.")
            return render(request, 'users/register.html')

    return render(request, 'users/register.html')

def logout_view(request):
    logout(request)
    messages.success(request, "Has cerrado sesión exitosamente. ¡Te esperamos pronto en Mewtual!")
    return redirect('users:login')