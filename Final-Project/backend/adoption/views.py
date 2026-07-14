from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from rest_framework import permissions, viewsets

from cats.models import Cat
from .forms import AdoptionPostEstadoForm, AdoptionPostForm
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


# ─────────────────────────────────────────────
#  Vistas de plantilla (Template Views)
# ─────────────────────────────────────────────

@login_required
def lista_publicaciones(request):
    """Publicaciones de adopción disponibles de otros usuarios."""
    publicaciones = AdoptionPost.objects.filter(
        estado="DISPONIBLE"
    ).exclude(
        gato__owner=request.user
    ).select_related("gato", "gato__owner").order_by("-publicado_en")

    return render(request, "adoption/lista_publicaciones.html", {"publicaciones": publicaciones})


@login_required
def mis_publicaciones(request):
    """Publicaciones de adopción propias del usuario autenticado."""
    publicaciones = AdoptionPost.objects.filter(
        gato__owner=request.user
    ).select_related("gato").order_by("-publicado_en")

    return render(request, "adoption/mis_publicaciones.html", {"publicaciones": publicaciones})


@login_required
def crear_publicacion(request):
    """Publica uno de los gatos propios en adopción."""
    if not Cat.objects.filter(owner=request.user).exists():
        messages.warning(request, "Necesitas registrar al menos un gato antes de publicarlo en adopción.")
        return redirect("cats:mis_gatos")

    if request.method == "POST":
        form = AdoptionPostForm(request.POST, user=request.user)
        if form.is_valid():
            post = form.save()
            messages.success(request, f"{post.gato.nombre} fue publicado en adopción.")
            return redirect("adoption:mis_publicaciones")
        messages.error(request, "Por favor corrige los errores del formulario.")
    else:
        form = AdoptionPostForm(user=request.user)

    return render(request, "adoption/crear_publicacion.html", {"form": form})


@login_required
def editar_publicacion(request, post_id):
    """Actualiza la descripción o el estado de una publicación propia."""
    post = get_object_or_404(AdoptionPost, pk=post_id, gato__owner=request.user)

    if request.method == "POST":
        form = AdoptionPostEstadoForm(request.POST, instance=post)
        if form.is_valid():
            form.save()
            messages.success(request, "Publicación actualizada.")
            return redirect("adoption:mis_publicaciones")
        messages.error(request, "Por favor corrige los errores del formulario.")
    else:
        form = AdoptionPostEstadoForm(instance=post)

    return render(request, "adoption/editar_publicacion.html", {"form": form, "post": post})


@login_required
def eliminar_publicacion(request, post_id):
    """Elimina una publicación propia. Solo el propietario del gato puede hacerlo."""
    post = get_object_or_404(AdoptionPost, pk=post_id, gato__owner=request.user)

    if request.method == "POST":
        nombre = post.gato.nombre
        post.delete()
        messages.success(request, f"La publicación de {nombre} fue eliminada.")
        return redirect("adoption:mis_publicaciones")

    return render(request, "adoption/confirmar_eliminar.html", {"post": post})
