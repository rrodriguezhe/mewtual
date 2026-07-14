from django import forms
from django.contrib.auth.models import User

from .models import Report

INPUT_CLASS = (
    "w-full px-4 py-2.5 rounded-xl border border-gray-100 "
    "focus:outline-none focus:border-brandOrange bg-white shadow-sm"
)


class ReportForm(forms.ModelForm):
    """Formulario para reportar a otro usuario."""

    class Meta:
        model = Report
        fields = ["usuario_reportado", "motivo"]
        widgets = {
            "usuario_reportado": forms.HiddenInput(),
            "motivo": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "Describe el motivo del reporte...",
                    "class": INPUT_CLASS,
                }
            ),
        }
        labels = {
            "motivo": "Motivo",
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user is not None:
            self.fields["usuario_reportado"].queryset = User.objects.exclude(pk=user.pk)
