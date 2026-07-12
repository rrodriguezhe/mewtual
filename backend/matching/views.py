from rest_framework import viewsets
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from datetime import date
from cats.models import Cat, Vaccine, MedicalRecord
from cats.views import puede_cruce_responsable, calcular_edad
from .models import Match
from .serializers import MatchSerializer

class MatchViewSet(viewsets.ModelViewSet):
    queryset = Match.objects.all()
    serializer_class = MatchSerializer

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