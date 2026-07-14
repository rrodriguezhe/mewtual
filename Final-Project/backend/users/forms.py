from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from .models import Profile

ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/png", "image/webp"]
MAX_IMAGE_SIZE_MB = 5


class AccountNameForm(forms.ModelForm):
    """
    Formulario para editar el nombre del usuario desde "Mi cuenta".
    """

    class Meta:
        model = User
        fields = ["first_name", "last_name"]
        widgets = {
            "first_name": forms.TextInput(
                attrs={
                    "placeholder": "Nombre",
                    "class": "w-full px-4 py-2.5 rounded-xl border border-gray-100 "
                             "focus:outline-none focus:border-brandOrange bg-white shadow-sm",
                }
            ),
            "last_name": forms.TextInput(
                attrs={
                    "placeholder": "Apellido",
                    "class": "w-full px-4 py-2.5 rounded-xl border border-gray-100 "
                             "focus:outline-none focus:border-brandOrange bg-white shadow-sm",
                }
            ),
        }
        labels = {
            "first_name": "Nombre",
            "last_name": "Apellido",
        }


class ProfilePictureForm(forms.ModelForm):
    """
    Formulario para editar la foto de perfil del usuario desde "Mi cuenta".
    """

    class Meta:
        model = Profile
        fields = ["foto_perfil"]
        labels = {
            "foto_perfil": "Foto de perfil",
        }

    def clean_foto_perfil(self):
        foto = self.cleaned_data.get("foto_perfil")
        if foto:
            if foto.size > MAX_IMAGE_SIZE_MB * 1024 * 1024:
                raise ValidationError(
                    f"La imagen no puede superar {MAX_IMAGE_SIZE_MB} MB."
                )
            if hasattr(foto, "content_type") and foto.content_type not in ALLOWED_IMAGE_TYPES:
                raise ValidationError(
                    "Solo se aceptan imágenes en formato JPG, PNG o WEBP."
                )
        return foto
