from rest_framework import viewsets
from django.shortcuts import render
from .models import Match
from .serializers import MatchSerializer
from django.contrib.auth.decorators import login_required

class MatchViewSet(viewsets.ModelViewSet):
    queryset = Match.objects.all()
    serializer_class = MatchSerializer
@login_required
def home_view(request):
    return render(request, 'matching/home.html')
@login_required
def swipe_view(request):
    return render(request, 'matching/swipe.html')