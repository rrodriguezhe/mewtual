from django import forms

from cats.models import Cat
from .models import AdoptionPost

INPUT_CLASS = (
    "w-full px-4 py-2.5 rounded-xl border border-gray-100 "
    "focus:outline-none focus:border-brandOrange bg-white shadow-sm"
)


class AdoptionPostForm(forms.ModelForm):
    """Formulario para publicar uno de los gatos propios en adopción."""

    class Meta:
        model = AdoptionPost
        fields = ["gato", "descripcion"]
        widgets = {
            "gato": forms.Select(attrs={"class": INPUT_CLASS}),
            "descripcion": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "Cuenta la historia del gato, su personalidad y "
                                   "por qué buscas darlo en adopción...",
                    "class": INPUT_CLASS,
                }
            ),
        }
        labels = {
            "gato": "Gato a publicar",
            "descripcion": "Descripción",
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user is not None:
            self.fields["gato"].queryset = Cat.objects.filter(owner=user)


class AdoptionPostEstadoForm(forms.ModelForm):
    """Formulario para actualizar la descripción y el estado de una publicación propia."""

    class Meta:
        model = AdoptionPost
        fields = ["descripcion", "estado"]
        widgets = {
            "descripcion": forms.Textarea(attrs={"rows": 4, "class": INPUT_CLASS}),
            "estado": forms.Select(attrs={"class": INPUT_CLASS}),
        }
        labels = {
            "descripcion": "Descripción",
            "estado": "Estado",
        }
