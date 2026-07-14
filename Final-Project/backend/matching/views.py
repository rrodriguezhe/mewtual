from rest_framework import permissions, viewsets
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.views.decorators.http import require_POST
from datetime import date
from cats.models import Cat, Vaccine, MedicalRecord
from cats.views import puede_cruce_responsable, calcular_edad
from .models import Match
from .serializers import MatchSerializer


class IsGatoOwnerOrStaff(permissions.BasePermission):
    """Solo el dueño de alguno de los gatos del match (o un miembro del staff) puede modificarlo."""

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return (
            request.user.is_staff
            or obj.gato_emisor.owner_id == request.user.id
            or obj.gato_receptor.owner_id == request.user.id
        )


class MatchViewSet(viewsets.ModelViewSet):
    serializer_class = MatchSerializer
    permission_classes = [permissions.IsAuthenticated, IsGatoOwnerOrStaff]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Match.objects.all()
        return Match.objects.filter(
            Q(gato_emisor__owner=user) | Q(gato_receptor__owner=user)
        )


@login_required
def home_view(request):
    return render(request, 'matching/home.html')


@login_required
def swipe_view(request):
    # 1. Obtener los gatos del usuario que son aptos para cruce responsable
    gatos_propios = Cat.objects.filter(owner=request.user)
    gatos_aptos = []
    for g in gatos_propios:
        res = puede_cruce_responsable(g)
        if res["apto"] and g.modo_cruce_responsable:
            gatos_aptos.append(g)

    # Si no tiene gatos aptos, redirigir a mis gatos con un aviso
    if not gatos_aptos:
        messages.warning(
            request,
            "Para poder buscar parejas (hacer swipe), primero debes tener al menos un gato "
            "con vacunación vigente, certificado médico registrado, no esterilizado y con el "
            "modo 'cruce responsable' activado."
        )
        return redirect('cats:mis_gatos')

    # Determinar qué gato del usuario está haciendo el swipe
    gato_activo_id = request.GET.get('gato_id')
    gato_activo = None
    if gato_activo_id:
        gato_activo = get_object_or_404(Cat, id=gato_activo_id, owner=request.user)
        # Validar que el gato sea apto
        if not puede_cruce_responsable(gato_activo)["apto"] or not gato_activo.modo_cruce_responsable:
            messages.error(request, f"{gato_activo.nombre} no es apto para cruce responsable actualmente.")
            return redirect('cats:mis_gatos')
    else:
        gato_activo = gatos_aptos[0]

    # 2. Filtrar candidatos del sexo opuesto
    sexo_opuesto = "F" if gato_activo.sexo == "M" else "M"

    # Obtener IDs de gatos con vacunas vigentes
    gatos_con_vacuna_vigente = Vaccine.objects.filter(
        gato__modo_cruce_responsable=True,
        fecha_vencimiento__gte=date.today()
    ).values_list('gato_id', flat=True)

    # Obtener IDs de gatos con certificado médico
    gatos_con_certificado = MedicalRecord.objects.filter(
        gato__modo_cruce_responsable=True,
        documento__isnull=False
    ).exclude(documento="").values_list('gato_id', flat=True)

    # Excluir gatos ya deslizados (swiped) por este gato_activo usando el modelo Match existente
    swiped_como_emisor = Match.objects.filter(
        gato_emisor=gato_activo
    ).values_list('gato_receptor_id', flat=True)

    swiped_como_receptor = Match.objects.filter(
        gato_receptor=gato_activo,
        estado__in=["ACEPTADO", "RECHAZADO"]
    ).values_list('gato_emisor_id', flat=True)

    # Consultar candidatos
    candidatos_qs = Cat.objects.filter(
        sexo=sexo_opuesto,
        modo_cruce_responsable=True,
        esterilizado=False,
        id__in=gatos_con_vacuna_vigente
    ).filter(
        id__in=gatos_con_certificado
    ).exclude(
        owner=request.user
    ).exclude(
        id__in=swiped_como_emisor
    ).exclude(
        id__in=swiped_como_receptor
    )

    # Obtener el primer candidato disponible
    candidato = candidatos_qs.first()
    candidato_edad = calcular_edad(candidato.fecha_nacimiento) if candidato else None

    context = {
        "gatos_aptos": gatos_aptos,
        "gato_activo": gato_activo,
        "candidato": candidato,
        "candidato_edad": candidato_edad,
    }
    return render(request, 'matching/swipe.html', context)


@login_required
@require_POST
def registrar_swipe(request, candidato_id, decision):
    """
    Registra un like/rechazo del gato_activo hacia un candidato.
    Si el candidato ya le había dado like (match pendiente entrante),
    un 'like' aquí lo convierte en match mutuo (ACEPTADO); la creación
    del Chat correspondiente la maneja una señal en la app chat.
    """
    gato_id = request.POST.get('gato_id')
    gato_activo = get_object_or_404(Cat, id=gato_id, owner=request.user)
    candidato = get_object_or_404(Cat, id=candidato_id)

    match_entrante = Match.objects.filter(
        gato_emisor=candidato,
        gato_receptor=gato_activo,
        estado="PENDIENTE"
    ).first()

    if decision == "like":
        if match_entrante:
            match_entrante.estado = "ACEPTADO"
            match_entrante.save()
            messages.success(request, f"¡Es un match con {candidato.nombre}!")
        else:
            Match.objects.get_or_create(
                gato_emisor=gato_activo,
                gato_receptor=candidato,
                defaults={"estado": "PENDIENTE"}
            )
    else:
        if match_entrante:
            match_entrante.estado = "RECHAZADO"
            match_entrante.save()
        else:
            Match.objects.get_or_create(
                gato_emisor=gato_activo,
                gato_receptor=candidato,
                defaults={"estado": "RECHAZADO"}
            )

    return redirect(f"{reverse('matching:swipe')}?gato_id={gato_activo.id}")
