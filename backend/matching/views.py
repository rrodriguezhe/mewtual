from rest_framework import viewsets
from django.shortcuts import render
from .models import Match
from .serializers import MatchSerializer


class MatchViewSet(viewsets.ModelViewSet):
    queryset = Match.objects.all()
    serializer_class = MatchSerializer

def home_view(request):
    return render(request, 'matching/home.html')

def swipe_view(request):
    return render(request, 'matching/swipe.html')