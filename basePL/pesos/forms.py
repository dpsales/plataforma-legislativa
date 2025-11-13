from django import forms

from .models import WeightEntry, WeightNamespace


class WeightEntryForm(forms.ModelForm):
    class Meta:
        model = WeightEntry
        fields = ["term", "weight"]
        widgets = {
            "term": forms.TextInput(attrs={"class": "form-control", "placeholder": "Palavra-chave"}),
            "weight": forms.NumberInput(attrs={"class": "form-control", "min": 0}),
        }


class NewWeightEntryForm(forms.ModelForm):
    namespace = forms.ChoiceField(
        choices=WeightNamespace.choices,
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    class Meta:
        model = WeightEntry
        fields = ["namespace", "term", "weight"]
        widgets = {
            "term": forms.TextInput(attrs={"class": "form-control", "placeholder": "Palavra-chave"}),
            "weight": forms.NumberInput(attrs={"class": "form-control", "min": 0}),
        }

    def clean_term(self):
        term = self.cleaned_data["term"].strip()
        if not term:
            raise forms.ValidationError("Informe a palavra-chave.")
        return term
