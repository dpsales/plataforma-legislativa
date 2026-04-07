from __future__ import annotations

from datetime import date
from typing import Iterable, Mapping

from django.db import transaction

from ..models import Event, MonitoredProposition, Proposition

_TRUE_VALUES = {"1", "true", "t", "yes", "y", "sim", "s"}


def _coerce_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if value in (None, "", 0, "0"):
        return False
    if isinstance(value, (int, float)):
        return value != 0
    return str(value).strip().lower() in _TRUE_VALUES

PROPOSITION_FIELDS = (
    "casa",
    "sigla_tipo",
    "numero",
    "ano",
    "ementa",
    "justificativa",
    "autor",
    "autor_partido_uf",
    "link_inteiro_teor",
    "link_ficha",
    "tem_pl",
    "impacto_fiscal",
    "impacto_categoria",
    "palavras_chave",
)

_PROPOSITION_STR_FIELDS = {
    "casa",
    "sigla_tipo",
    "numero",
    "ano",
    "ementa",
    "justificativa",
    "autor",
    "autor_partido_uf",
    "link_inteiro_teor",
    "link_ficha",
    "impacto_fiscal",
    "impacto_categoria",
    "palavras_chave",
}

EVENT_FIELDS = (
    "external_id",
    "casa",
    "colegiado",
    "data_evento",
    "hora_evento",
    "link_colegiado",
    "plenario_ou_comissao",
    "marcar_para_relatorio",
)

_EVENT_STR_FIELDS = {
    "casa",
    "colegiado",
    "hora_evento",
    "link_colegiado",
    "plenario_ou_comissao",
}


def upsert_catalog(entries: Iterable[Mapping[str, object]]) -> list[Proposition]:
    created: list[Proposition] = []
    with transaction.atomic():
        for item in entries:
            identifier = str(item["identifier"]).strip()
            defaults = {}
            for field in PROPOSITION_FIELDS:
                value = item.get(field)
                if field in _PROPOSITION_STR_FIELDS:
                    defaults[field] = "" if value is None else str(value)
                elif field == "tem_pl":
                    defaults[field] = _coerce_bool(value)
                else:
                    defaults[field] = value
            obj, _ = Proposition.objects.update_or_create(identifier=identifier, defaults=defaults)
            created.append(obj)
    return created


def upsert_events(entries: Iterable[Mapping[str, object]]) -> None:
    with transaction.atomic():
        for item in entries:
            identifier = str(item["identifier"]).strip()
            proposition = Proposition.objects.filter(identifier=identifier).first()
            if not proposition:
                continue
            external_id = str(item["external_id"]).strip()
            defaults = {}
            for field in EVENT_FIELDS:
                if field == "external_id":
                    continue
                value = item.get(field)
                if field in _EVENT_STR_FIELDS:
                    defaults[field] = "" if value is None else str(value)
                elif field == "marcar_para_relatorio":
                    defaults[field] = _coerce_bool(value)
                else:
                    defaults[field] = value
            if isinstance(defaults.get("data_evento"), str):
                try:
                    defaults["data_evento"] = date.fromisoformat(str(defaults["data_evento"]))
                except ValueError:
                    defaults.pop("data_evento", None)
            Event.objects.update_or_create(
                external_id=external_id,
                proposition=proposition,
                defaults=defaults,
            )


def clear_monitoring_for_missing(identifiers: Iterable[str]) -> None:
    keep = {str(identifier).strip() for identifier in identifiers}
    for monitor in MonitoredProposition.objects.select_related("proposition").all():
        if monitor.proposition.identifier not in keep:
            monitor.delete()
