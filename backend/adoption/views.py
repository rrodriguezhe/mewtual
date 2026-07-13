from rest_framework import permissions, viewsets

from .models import AdoptionPost
from .serializers import AdoptionPostSerializer


class IsGatoOwnerOrStaff(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_staff or obj.gato.owner_id == request.user.id


class AdoptionPostViewSet(viewsets.ModelViewSet):

    queryset = AdoptionPost.objects.all()

    serializer_class = AdoptionPostSerializer
    permission_classes = [permissions.IsAuthenticated, IsGatoOwnerOrStaff]