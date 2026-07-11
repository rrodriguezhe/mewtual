from rest_framework import viewsets
from django.shortcuts import render, redirect
from .models import Cat
from .serializers import CatSerializer


class CatViewSet(viewsets.ModelViewSet):
    queryset = Cat.objects.all()
    serializer_class = CatSerializer

def mis_gatos(request):
    return render(request, 'cats/mis_gatos.html')

def crear_perfil(request):
    if request.method == 'POST':
        return redirect('cats:mis_gatos')
    return render(request, 'cats/crear_perfil.html')

def editar_perfil(request):
    if request.method == 'POST':
        return redirect('cats:mis_gatos')
    return render(request, 'cats/editar_perfil.html')