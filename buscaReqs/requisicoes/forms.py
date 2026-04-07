from __future__ import annotations

import re
from typing import Iterable

from django import forms
from django.utils.text import slugify

from .models import Configuration


class ConfigurationForm(forms.Form):
    proposition_types = forms.CharField(
        label="Tipos de proposição",
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 4}),
        required=False,
        strip=False,
        help_text="Uma sigla por linha (ex.: RIC). Vírgulas ou ponto e vírgula também são aceitos.",
    )
    presentation_years = forms.CharField(
        label="Anos de apresentação",
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        required=False,
        strip=False,
        help_text="Informe um ano por linha. Apenas números são permitidos (ex.: 2023).",
    )
    unit_groups = forms.CharField(
        label="Unidades / Cargos",
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 6}),
        required=False,
        strip=False,
        help_text=(
            "Formato: identificador|Rótulo|termo1, termo2, termo3. "
            "Um grupo por linha. Os termos serão usados para filtrar a coluna Termos Encontrados."
        ),
    )
    subjects = forms.CharField(
        label="Assuntos monitorados",
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 6}),
        required=False,
        strip=False,
        help_text=(
            "Informe um assunto por linha. Utilize o formato valor|Rótulo (ex.: L14133|Lei nº 14.133/2021). "
            "Se o valor não for informado, um identificador será gerado automaticamente."
        ),
    )

    def __init__(self, *args, config: Configuration | None = None, **kwargs) -> None:
        self.config = config
        initial = kwargs.setdefault("initial", {})
        if config is not None:
            initial.setdefault("proposition_types", self._join_lines(config.proposition_types))
            initial.setdefault(
                "presentation_years",
                self._join_lines(str(year) for year in (config.presentation_years or [])),
            )
            initial.setdefault("unit_groups", self._format_unit_groups(config.unit_groups))
            initial.setdefault("subjects", self._format_subjects(config.subjects))
        super().__init__(*args, **kwargs)

    @staticmethod
    def _join_lines(values: Iterable[str] | Iterable[int]) -> str:
        return "\n".join(str(value).strip() for value in values if str(value).strip())

    @staticmethod
    def _normalise_label(label: str | Iterable[str]) -> str:
        if isinstance(label, str):
            return label.strip()
        if isinstance(label, (set, list, tuple)):
            return ", ".join(str(item).strip() for item in label if str(item).strip())
        return str(label).strip()

    @classmethod
    def _format_unit_groups(cls, groups: Iterable[dict[str, object]] | None) -> str:
        if not groups:
            return ""
        lines: list[str] = []
        for item in groups:
            value = str(item.get("value", "")).strip()
            label = cls._normalise_label(item.get("label", ""))
            terms = item.get("terms", [])
            if isinstance(terms, str):
                terms_list = [terms]
            else:
                terms_list = [str(term).strip() for term in (terms or []) if str(term).strip()]
            if not value and not label and not terms_list:
                continue
            if not value:
                value = slugify(label) or label.replace(" ", "_").lower()
            if not label:
                label = value
            lines.append(f"{value}|{label}|{', '.join(terms_list)}")
        return "\n".join(lines)

    @classmethod
    def _format_subjects(cls, subjects: Iterable[dict[str, str]] | None) -> str:
        if not subjects:
            return ""
        lines: list[str] = []
        for item in subjects:
            value = str(item.get("value", "")).strip()
            label = cls._normalise_label(item.get("label", ""))
            if not value and not label:
                continue
            if not label:
                label = value
            if not value:
                value = slugify(label) or label.replace(" ", "_").lower()
            lines.append(f"{value}|{label}")
        return "\n".join(lines)

    def clean_proposition_types(self) -> list[str]:
        raw = self.cleaned_data.get("proposition_types", "") or ""
        tokens: list[str] = []
        for fragment in re.split(r"[\n,;]+", raw):
            token = fragment.strip().upper()
            if not token:
                continue
            if token not in tokens:
                tokens.append(token)
        return tokens

    def clean_presentation_years(self) -> list[int]:
        raw = self.cleaned_data.get("presentation_years", "") or ""
        years: list[int] = []
        for fragment in re.split(r"[\n,;]+", raw):
            value = fragment.strip()
            if not value:
                continue
            if not value.isdigit():
                raise forms.ValidationError(f"Ano inválido: '{value}'")
            year = int(value)
            if year < 1500 or year > 9999:
                raise forms.ValidationError(f"Ano fora do intervalo esperado: '{value}'")
            if year not in years:
                years.append(year)
        years.sort()
        return years

    def clean_subjects(self) -> list[dict[str, str]]:
        raw = self.cleaned_data.get("subjects", "") or ""
        subjects: list[dict[str, str]] = []
        seen_values: set[str] = set()
        for line in raw.splitlines():
            entry = line.strip()
            if not entry:
                continue
            if "|" in entry:
                value_part, label_part = entry.split("|", 1)
                value = value_part.strip()
                label = label_part.strip()
            else:
                label = entry.strip()
                value = slugify(label) or label.replace(" ", "_").lower()
            if not label:
                raise forms.ValidationError("Informe um rótulo para cada assunto.")
            if not value:
                value = slugify(label) or label.replace(" ", "_").lower()
            if value in seen_values:
                continue
            seen_values.add(value)
            subjects.append({"value": value, "label": label})
        return subjects

    def clean_unit_groups(self) -> list[dict[str, object]]:
        raw = self.cleaned_data.get("unit_groups", "") or ""
        groups: list[dict[str, object]] = []
        seen_values: set[str] = set()
        for line in raw.splitlines():
            entry = line.strip()
            if not entry:
                continue
            parts = [part.strip() for part in entry.split("|")]
            if len(parts) < 2:
                raise forms.ValidationError(
                    "Use o formato identificador|Rótulo|termo1, termo2."
                )
            value = parts[0] or slugify(parts[1]) or parts[1].replace(" ", "_").lower()
            if not value:
                raise forms.ValidationError("Informe um identificador para cada grupo.")
            if value in seen_values:
                continue
            seen_values.add(value)
            label = parts[1] or value
            terms_raw = parts[2] if len(parts) > 2 else ""
            terms: list[str] = []
            for fragment in re.split(r"[,;]+", terms_raw):
                token = fragment.strip()
                if token and token not in terms:
                    terms.append(token)
            groups.append({"value": value, "label": label, "terms": terms})
        return groups

    def save(self) -> Configuration:
        if self.config is None:
            self.config = Configuration.load()
        self.config.proposition_types = self.cleaned_data["proposition_types"]
        self.config.presentation_years = self.cleaned_data["presentation_years"]
        self.config.unit_groups = self.cleaned_data["unit_groups"]
        self.config.subjects = self.cleaned_data["subjects"]
        self.config.save()
        return self.config
