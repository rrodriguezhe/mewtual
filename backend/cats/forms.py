from django import forms
from django.core.exceptions import ValidationError
from datetime import date

from .models import Cat, MedicalRecord, Vaccine


ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/png", "image/webp"]
MAX_IMAGE_SIZE_MB = 5


class CatForm(forms.ModelForm):
    """
    Formulario para crear y editar el perfil de un gato.
    Todos los campos obligatorios según RF-08 / RF-09:
    nombre, raza, fecha_nacimiento (edad), foto.
    """

    class Meta:
        model = Cat
        fields = [
            "nombre",
            "raza",
            "sexo",
            "fecha_nacimiento",
            "peso",
            "color",
            "foto",
            "gustos_preferencias",
            "esterilizado",
            "modo_cruce_responsable",
        ]
        widgets = {
            "nombre": forms.TextInput(
                attrs={
                    "placeholder": "Nombre del gato",
                    "class": "w-full px-4 py-2.5 rounded-xl border border-gray-100 "
                             "focus:outline-none focus:border-brandOrange bg-white shadow-sm",
                }
            ),
            "raza": forms.TextInput(
                attrs={
                    "placeholder": "Ej: Angora, Bengalí...",
                    "class": "w-full px-4 py-2.5 rounded-xl border border-gray-100 "
                             "focus:outline-none focus:border-brandOrange bg-white shadow-sm",
                }
            ),
            "sexo": forms.RadioSelect(
                attrs={"class": "sexo-radio"}
            ),
            "fecha_nacimiento": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "w-full px-4 py-2.5 rounded-xl border border-gray-100 "
                             "focus:outline-none focus:border-brandOrange bg-white shadow-sm",
                }
            ),
            "peso": forms.NumberInput(
                attrs={
                    "step": "0.1",
                    "min": "0.1",
                    "placeholder": "Peso en kg",
                    "class": "w-full px-4 py-2.5 rounded-xl border border-gray-100 "
                             "focus:outline-none focus:border-brandOrange bg-white shadow-sm",
                }
            ),
            "color": forms.TextInput(
                attrs={
                    "placeholder": "Ej: Blanco y naranja",
                    "class": "w-full px-4 py-2.5 rounded-xl border border-gray-100 "
                             "focus:outline-none focus:border-brandOrange bg-white shadow-sm",
                }
            ),
            "gustos_preferencias": forms.Textarea(
                attrs={
                    "rows": 3,
                    "placeholder": "Describe los gustos y personalidad de tu gato...",
                    "class": "w-full px-4 py-2.5 rounded-xl border border-gray-100 "
                             "focus:outline-none focus:border-brandOrange bg-white shadow-sm",
                }
            ),
            "esterilizado": forms.CheckboxInput(
                attrs={"class": "w-5 h-5 accent-brandGreen"}
            ),
            "modo_cruce_responsable": forms.CheckboxInput(
                attrs={"class": "w-5 h-5 accent-brandOrange"}
            ),
        }
        labels = {
            "nombre": "Nombre",
            "raza": "Raza",
            "sexo": "Género",
            "fecha_nacimiento": "Fecha de nacimiento",
            "peso": "Peso (kg)",
            "color": "Color de pelaje",
            "foto": "Foto",
            "gustos_preferencias": "Descripción",
            "esterilizado": "Esterilizado",
            "modo_cruce_responsable": "Habilitar modo cruce responsable",
        }

    def clean_foto(self):
        foto = self.cleaned_data.get("foto")
        if foto:
            # Tamaño máximo (RNF archivos)
            if foto.size > MAX_IMAGE_SIZE_MB * 1024 * 1024:
                raise ValidationError(
                    f"La imagen no puede superar {MAX_IMAGE_SIZE_MB} MB."
                )
            # Formato permitido (RNF archivos): JPG, PNG, WEBP
            if hasattr(foto, "content_type") and foto.content_type not in ALLOWED_IMAGE_TYPES:
                raise ValidationError(
                    "Solo se aceptan imágenes en formato JPG, PNG o WEBP."
                )
        return foto

    def clean_fecha_nacimiento(self):
        fecha = self.cleaned_data.get("fecha_nacimiento")
        if fecha and fecha > date.today():
            raise ValidationError(
                "La fecha de nacimiento no puede ser futura."
            )
        return fecha

    def clean_peso(self):
        peso = self.cleaned_data.get("peso")
        if peso is not None and peso <= 0:
            raise ValidationError("El peso debe ser un valor positivo.")
        return peso

    def clean(self):
        cleaned_data = super().clean()
        esterilizado = cleaned_data.get("esterilizado")
        modo_cruce = cleaned_data.get("modo_cruce_responsable")

        # Regla de negocio: gatos esterilizados no pueden usar modo cruce responsable
        if esterilizado and modo_cruce:
            self.add_error(
                "modo_cruce_responsable",
                "Un gato esterilizado no puede habilitarse en modo cruce responsable.",
            )
        return cleaned_data


class VaccineForm(forms.ModelForm):
    """
    Formulario OPCIONAL para registrar una vacuna.
    Si todos los campos principales están vacíos, el formulario
    se ignora por completo (no es obligatorio rellenarlo).
    Solo valida cuando el usuario empieza a rellenar algún campo.
    """

    class Meta:
        model = Vaccine
        fields = ["nombre", "fecha_aplicacion", "fecha_vencimiento", "soporte"]
        widgets = {
            "nombre": forms.TextInput(
                attrs={
                    "placeholder": "Ej: Rabia, Panleucopenia...",
                    "class": "w-full px-4 py-2.5 rounded-xl border border-gray-100 "
                             "focus:outline-none focus:border-brandOrange bg-white shadow-sm",
                }
            ),
            "fecha_aplicacion": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "w-full px-4 py-2.5 rounded-xl border border-gray-100 "
                             "focus:outline-none focus:border-brandOrange bg-white shadow-sm",
                }
            ),
            "fecha_vencimiento": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "w-full px-4 py-2.5 rounded-xl border border-gray-100 "
                             "focus:outline-none focus:border-brandOrange bg-white shadow-sm",
                }
            ),
        }
        labels = {
            "nombre": "Nombre de la vacuna",
            "fecha_aplicacion": "Fecha de aplicación",
            "fecha_vencimiento": "Fecha de vencimiento",
            "soporte": "Documento de soporte (opcional)",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Todos los campos son opcionales a nivel de formulario.
        # La validación cruzada se hace en clean() solo si hay datos.
        self.fields["nombre"].required = False
        self.fields["fecha_aplicacion"].required = False
        self.fields["fecha_vencimiento"].required = False
        self.fields["soporte"].required = False

    def tiene_datos(self):
        """Devuelve True si el usuario rellenó al menos el nombre."""
        return bool(self.cleaned_data.get("nombre"))

    def clean(self):
        cleaned_data = super().clean()
        nombre = cleaned_data.get("nombre")
        aplicacion = cleaned_data.get("fecha_aplicacion")
        vencimiento = cleaned_data.get("fecha_vencimiento")

        # Si no hay nombre, el bloque entero se ignora
        if not nombre:
            return cleaned_data

        # Si hay nombre, las fechas sí son obligatorias
        if not aplicacion:
            self.add_error("fecha_aplicacion",
                           "Indica la fecha de aplicación de la vacuna.")
        if not vencimiento:
            self.add_error("fecha_vencimiento",
                           "Indica la fecha de vencimiento de la vacuna.")

        if aplicacion and vencimiento:
            if aplicacion > date.today():
                self.add_error("fecha_aplicacion",
                               "La fecha de aplicación no puede ser futura.")
            if vencimiento <= aplicacion:
                self.add_error("fecha_vencimiento",
                               "La fecha de vencimiento debe ser posterior a la de aplicación.")

        return cleaned_data


class MedicalRecordForm(forms.ModelForm):
    """
    Formulario OPCIONAL para registrar un certificado/historial médico.
    El diagnóstico es el campo disparador: si está vacío, todo se ignora.
    El documento adjunto (PDF, imagen) es obligatorio cuando se registra
    un certificado médico, ya que es requisito para el modo cruce responsable.
    """

    class Meta:
        model = MedicalRecord
        fields = ["diagnostico_procedimiento", "notas", "documento"]
        widgets = {
            "diagnostico_procedimiento": forms.TextInput(
                attrs={
                    "placeholder": "Ej: Revisión general, Desparasitación...",
                    "class": "w-full px-4 py-2.5 rounded-xl border border-gray-100 "
                             "focus:outline-none focus:border-brandOrange bg-white shadow-sm",
                }
            ),
            "notas": forms.Textarea(
                attrs={
                    "rows": 2,
                    "placeholder": "Observaciones adicionales del veterinario (opcional)...",
                    "class": "w-full px-4 py-2.5 rounded-xl border border-gray-100 "
                             "focus:outline-none focus:border-brandOrange bg-white shadow-sm",
                }
            ),
        }
        labels = {
            "diagnostico_procedimiento": "Diagnóstico o procedimiento",
            "notas": "Notas adicionales",
            "documento": "Certificado médico (PDF o imagen)",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["diagnostico_procedimiento"].required = False
        self.fields["notas"].required = False
        self.fields["documento"].required = False

    def tiene_datos(self):
        """Devuelve True si el usuario escribió al menos el diagnóstico."""
        return bool(self.cleaned_data.get("diagnostico_procedimiento"))

    def clean(self):
        cleaned_data = super().clean()
        diagnostico = cleaned_data.get("diagnostico_procedimiento")

        # Sin diagnóstico, el formulario entero se ignora
        if not diagnostico:
            return cleaned_data

        # Si hay diagnóstico, el documento es obligatorio para cruce responsable
        if not cleaned_data.get("documento"):
            self.add_error(
                "documento",
                "Adjunta el certificado médico emitido por el veterinario.",
            )

        return cleaned_data