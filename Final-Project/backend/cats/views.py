from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from rest_framework import permissions, viewsets

from .forms import CatForm, MedicalRecordForm, VaccineForm
from .models import Cat, MedicalRecord, Vaccine
from .serializers import CatSerializer


# ─────────────────────────────────────────────
#  Utilidades
# ─────────────────────────────────────────────

def calcular_edad(fecha_nacimiento):
    """Devuelve la edad en años a partir de fecha_nacimiento (DateField)."""
    hoy = date.today()
    años = hoy.year - fecha_nacimiento.year
    if (hoy.month, hoy.day) < (fecha_nacimiento.month, fecha_nacimiento.day):
        años -= 1
    return años


def vacunas_vigentes(gato):
    """Devuelve True si el gato tiene al menos una vacuna vigente."""
    return Vaccine.objects.filter(
        gato=gato,
        fecha_vencimiento__gte=date.today()
    ).exists()


def puede_cruce_responsable(gato):
    """
    Devuelve un dict con el estado de cada requisito para el modo cruce responsable:
      - vacuna_vigente : bool
      - certificado_medico: bool  (al menos un MedicalRecord con documento adjunto)
      - apto           : bool     (todos los requisitos cumplidos y no esterilizado)
    """
    tiene_vacuna = vacunas_vigentes(gato)
    tiene_certificado = MedicalRecord.objects.filter(
        gato=gato,
        documento__isnull=False,
    ).exclude(documento="").exists()

    apto = tiene_vacuna and tiene_certificado and not gato.esterilizado

    return {
        "vacuna_vigente": tiene_vacuna,
        "certificado_medico": tiene_certificado,
        "apto": apto,
    }


# ─────────────────────────────────────────────
#  Vistas de plantilla (Template Views)
# ─────────────────────────────────────────────

@login_required
def mis_gatos(request):
    """
    RF-08 / RF-11: Lista todos los gatos del usuario autenticado.
    Calcula la edad de cada gato y verifica estado de vacunación.
    """
    gatos_qs = Cat.objects.filter(owner=request.user).order_by("-fecha_registro")

    gatos = []
    for gato in gatos_qs:
        gatos.append({
            "obj": gato,
            "edad": calcular_edad(gato.fecha_nacimiento),
            "vacunado": vacunas_vigentes(gato),
            "cruce": puede_cruce_responsable(gato),
        })

    return render(request, "cats/mis_gatos.html", {"gatos": gatos})


@login_required
def ver_perfil(request, cat_id):
    """Perfil de un gato tal como lo vería otro usuario (adopción, match, etc.)."""
    gato = get_object_or_404(Cat, pk=cat_id)
    edad = calcular_edad(gato.fecha_nacimiento)
    es_owner = gato.owner_id == request.user.id

    gato_activo_id = request.GET.get('gato_activo')
    gato_activo = None
    if gato_activo_id and gato_activo_id.isdigit():
        gato_activo = Cat.objects.filter(pk=gato_activo_id, owner=request.user).first()
    puede_swipe = not es_owner and gato_activo is not None

    post_adopcion = gato.adoptionpost_set.filter(estado="DISPONIBLE").first()
    puede_contactar = not es_owner and not puede_swipe and post_adopcion is not None

    return render(request, "cats/ver_perfil.html", {
        "gato": gato,
        "edad": edad,
        "es_owner": es_owner,
        "gato_activo": gato_activo,
        "puede_swipe": puede_swipe,
        "post_adopcion": post_adopcion,
        "puede_contactar": puede_contactar,
    })


@login_required
def crear_perfil(request):
    """
    RF-08: Crea un nuevo perfil de gato.
    Campos obligatorios: nombre, raza, edad (fecha_nacimiento), foto.
    El owner se asigna automáticamente al usuario autenticado.
    """
    if request.method == "POST":
        form = CatForm(request.POST, request.FILES)
        vaccine_form = VaccineForm(request.POST, request.FILES, prefix="vac")
        medical_form = MedicalRecordForm(request.POST, request.FILES, prefix="med")

        if form.is_valid() and vaccine_form.is_valid() and medical_form.is_valid():
            gato = form.save(commit=False)
            gato.owner = request.user
            gato.save()

            if vaccine_form.tiene_datos():
                vacuna = vaccine_form.save(commit=False)
                vacuna.gato = gato
                vacuna.save()

            if medical_form.tiene_datos():
                registro = medical_form.save(commit=False)
                registro.gato = gato
                registro.save()

            messages.success(request, f"Perfil de {gato.nombre} creado exitosamente.")
            return redirect("cats:mis_gatos")
        else:
            messages.error(request, "Por favor corrige los errores del formulario.")
    else:
        form = CatForm()
        vaccine_form = VaccineForm(prefix="vac")
        medical_form = MedicalRecordForm(prefix="med")

    return render(request, "cats/crear_perfil.html", {
        "form": form,
        "vaccine_form": vaccine_form,
        "medical_form": medical_form,
    })


@login_required
def editar_perfil(request, cat_id):
    """
    RF-09: Edita el perfil de un gato.
    Regla de negocio: solo el propietario puede editar.
    Permite agregar vacunas y certificados médicos adicionales.
    """
    gato = get_object_or_404(Cat, pk=cat_id, owner=request.user)
    vacunas = Vaccine.objects.filter(gato=gato).order_by("-fecha_aplicacion")
    registros_medicos = MedicalRecord.objects.filter(gato=gato).order_by("-fecha_registro")

    if request.method == "POST":
        form = CatForm(request.POST, request.FILES, instance=gato)
        vaccine_form = VaccineForm(request.POST, request.FILES, prefix="vac")
        medical_form = MedicalRecordForm(request.POST, request.FILES, prefix="med")

        if form.is_valid() and vaccine_form.is_valid() and medical_form.is_valid():
            form.save()

            if vaccine_form.tiene_datos():
                vacuna = vaccine_form.save(commit=False)
                vacuna.gato = gato
                vacuna.save()
                messages.success(request, "Vacuna registrada correctamente.")

            if medical_form.tiene_datos():
                registro = medical_form.save(commit=False)
                registro.gato = gato
                registro.save()
                messages.success(request, "Certificado médico registrado.")

            messages.success(request, f"Perfil de {gato.nombre} actualizado.")
            return redirect("cats:mis_gatos")
        else:
            messages.error(request, "Por favor corrige los errores del formulario.")
    else:
        form = CatForm(instance=gato)
        vaccine_form = VaccineForm(prefix="vac")
        medical_form = MedicalRecordForm(prefix="med")

    return render(request, "cats/editar_perfil.html", {
        "form": form,
        "vaccine_form": vaccine_form,
        "medical_form": medical_form,
        "gato": gato,
        "vacunas": vacunas,
        "registros_medicos": registros_medicos,
        "cruce": puede_cruce_responsable(gato),
        "edad": calcular_edad(gato.fecha_nacimiento),
        "vacunado": vacunas_vigentes(gato),
        "today": date.today(),
    })


@login_required
def eliminar_perfil(request, cat_id):
    """
    RF-10: Elimina el perfil de un gato.
    Solo el propietario puede hacerlo. Se confirma con POST.
    """
    gato = get_object_or_404(Cat, pk=cat_id, owner=request.user)

    if request.method == "POST":
        nombre = gato.nombre
        gato.delete()
        messages.success(request, f"El perfil de {nombre} fue eliminado.")
        return redirect("cats:mis_gatos")

    return render(request, "cats/confirmar_eliminar.html", {"gato": gato})


@login_required
def eliminar_registro_medico(request, registro_id):
    """Elimina un registro médico de un gato propio del usuario."""
    registro = get_object_or_404(MedicalRecord, pk=registro_id, gato__owner=request.user)
    cat_id = registro.gato.pk
    registro.delete()
    messages.success(request, "Registro médico eliminado.")
    return redirect("cats:editar_perfil", cat_id=cat_id)


@login_required
def eliminar_vacuna(request, vacuna_id):
    """Elimina una vacuna puntual de un gato propio del usuario."""
    vacuna = get_object_or_404(Vaccine, pk=vacuna_id, gato__owner=request.user)
    cat_id = vacuna.gato.pk
    vacuna.delete()
    messages.success(request, "Vacuna eliminada.")
    return redirect("cats:editar_perfil", cat_id=cat_id)


# ─────────────────────────────────────────────
#  ViewSet REST (API)
# ─────────────────────────────────────────────

class CatViewSet(viewsets.ModelViewSet):
    """
    API REST para el modelo Cat.
    Solo devuelve los gatos del usuario autenticado.
    """
    serializer_class = CatSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Cat.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
