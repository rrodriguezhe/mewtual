from rest_framework import viewsets

from .models import AdoptionPost
from .serializers import AdoptionPostSerializer


class AdoptionPostViewSet(viewsets.ModelViewSet):

    queryset = AdoptionPost.objects.all()

    serializer_class = AdoptionPostSerializer