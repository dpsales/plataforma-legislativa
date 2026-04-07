from __future__ import annotations

from django import forms

from .models import MonitoredProposition, Proposition


class MonitorSelectionForm(forms.ModelForm):
    class Meta:
        model = MonitoredProposition
        fields = ["prioridade", "destaque", "observacoes"]
        widgets = {
            "prioridade": forms.NumberInput(attrs={"class": "form-control", "min": 0}),
            "destaque": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "observacoes": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        }


class AddMonitorForm(forms.Form):
    proposition = forms.ModelChoiceField(
        queryset=Proposition.objects.none(),
        widget=forms.Select(attrs={"class": "form-select"}),
        label="Selecionar proposição",
    )

    def __init__(self, *args, **kwargs):
        queryset = kwargs.pop("queryset", Proposition.objects.none())
        super().__init__(*args, **kwargs)
        self.fields["proposition"].queryset = queryset


class BulkUploadForm(forms.Form):
    arquivo = forms.FileField(label="Arquivo CSV", help_text="Colunas: identifier, prioridade, destaque, observacoes")
