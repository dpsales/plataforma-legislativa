from __future__ import annotations

from django import forms

from .models import TrackedProposition


class UploadJsonForm(forms.Form):
    arquivo = forms.FileField(
        label="Documento JSON",
        help_text="Envie um arquivo JSON com a lista de proposições monitoradas.",
    )

    def clean_arquivo(self):
        arquivo = self.cleaned_data["arquivo"]
        if arquivo.content_type not in {"application/json", "text/json", "application/octet-stream"}:
            raise forms.ValidationError("Envie um arquivo JSON válido.")
        if arquivo.size > 2 * 1024 * 1024:
            raise forms.ValidationError("O arquivo deve ter no máximo 2MB.")
        return arquivo


class TrackedPropositionForm(forms.ModelForm):
    class Meta:
        model = TrackedProposition
        fields = [
            "proposition_id",
            "casa",
            "secretaria",
            "tipo_sigla",
            "numero",
            "ano",
            "assunto",
            "prioridade",
            "justificativa",
        ]
        widgets = {
            "justificativa": forms.Textarea(attrs={"rows": 3}),
        }

    def clean_proposition_id(self):
        valor = self.cleaned_data["proposition_id"]
        if valor <= 0:
            raise forms.ValidationError("Informe um ID válido.")
        return valor
