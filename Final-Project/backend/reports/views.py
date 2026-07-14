from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect, render
from rest_framework import permissions, viewsets

from .forms import ReportForm
from .models import Report
from .serializers import ReportSerializer


class ReportViewSet(viewsets.ModelViewSet):

    serializer_class = ReportSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        if self.action in ("update", "partial_update", "destroy"):
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Report.objects.all()
        return Report.objects.filter(usuario_reportante=user)

    def perform_create(self, serializer):
        serializer.save(usuario_reportante=self.request.user)


# ─────────────────────────────────────────────
#  Vistas de plantilla (Template Views)
# ─────────────────────────────────────────────

@login_required
def crear_reporte(request):
    """
    Reporta a otro usuario por comportamiento indebido.
    Siempre se invoca con un objetivo concreto (?usuario=<id>) desde el
    chat, una publicación de adopción o el flujo de match; no existe un
    selector libre de usuario.
    """
    if request.method == "POST":
        form = ReportForm(request.POST, user=request.user)
        target_user = User.objects.filter(pk=request.POST.get("usuario_reportado")).first()
        if form.is_valid():
            reporte = form.save(commit=False)
            reporte.usuario_reportante = request.user
            reporte.save()
            messages.success(request, "Reporte enviado. Nuestro equipo lo revisará pronto.")
            return redirect("reports:mis_reportes")
        messages.error(request, "Por favor corrige los errores del formulario.")
    else:
        usuario_id = request.GET.get("usuario")
        target_user = get_object_or_404(User, pk=usuario_id) if usuario_id else None
        if target_user is None or target_user == request.user:
            messages.error(request, "Selecciona un usuario válido para reportar.")
            return redirect("matching:home")
        form = ReportForm(user=request.user, initial={"usuario_reportado": target_user.pk})

    return render(request, "reports/crear_reporte.html", {"form": form, "target_user": target_user})


@login_required
def mis_reportes(request):
    """Lista los reportes presentados por el usuario autenticado."""
    reportes = Report.objects.filter(
        usuario_reportante=request.user
    ).select_related("usuario_reportado").order_by("-fecha_reporte")

    return render(request, "reports/mis_reportes.html", {"reportes": reportes})
