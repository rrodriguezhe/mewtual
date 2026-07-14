from rest_framework import permissions, viewsets
from django.db.models import Q

from .models import Appointment
from .serializers import AppointmentSerializer


class AppointmentViewSet(viewsets.ModelViewSet):
    serializer_class = AppointmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Appointment.objects.filter(
            Q(match__gato_emisor__owner=user) | Q(match__gato_receptor__owner=user)
        )
