from __future__ import annotations

import json
from typing import Any

from django.db import transaction

from .models import TrackedDocument, TrackedProposition


def _normalize_casa(valor: str | None) -> str:
    if not valor:
        return TrackedProposition.CASA_CAMARA
    valor = valor.strip().lower()
    if valor in {"cd", "camara", "câmara", "c"}:
        return TrackedProposition.CASA_CAMARA
    if valor in {"sf", "senado", "senado federal", "s"}:
        return TrackedProposition.CASA_SENADO
    if "senad" in valor:
        return TrackedProposition.CASA_SENADO
    if "camar" in valor or "câmar" in valor:
        return TrackedProposition.CASA_CAMARA
    return TrackedProposition.CASA_CAMARA


def _extract_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def load_document_from_json(content: bytes, profile: str) -> TrackedDocument:
    payload = json.loads(content.decode("utf-8"))
    description = payload.get("descrição") or payload.get("descricao") or ""
    reference = payload.get("data_referencia") or payload.get("referencia") or ""
    entries = payload.get("proposicoes_mgi") or payload.get("proposicoes") or []
    if not isinstance(entries, list):
        raise ValueError("O JSON informado não contém a lista de proposições esperada.")

    document, _ = TrackedDocument.objects.get_or_create(
        slug=TrackedDocument.DEFAULT_SLUG,
        defaults={"name": "Proposições monitoradas"},
    )

    with transaction.atomic():
        document.description = description
        document.reference_label = reference
        document.raw_payload = payload
        document.last_updated_profile = profile or ""
        document.save()
        document.propositions.all().delete()

        objetos: list[TrackedProposition] = []
        for entry in entries:
            proposition_id = _extract_int(
                entry.get("id_proposicao")
                or entry.get("proposicao_id")
                or entry.get("id")
            )
            if not proposition_id:
                continue
            casa = _normalize_casa(
                entry.get("casa")
                or entry.get("Casa")
                or entry.get("casa_sigla")
            )
            numero = entry.get("numero") or ""
            ano = _extract_int(entry.get("ano"))
            prioridade = _extract_int(
                entry.get("prioridade")
                or entry.get("prioridade_mgi")
            )
            objetos.append(
                TrackedProposition(
                    document=document,
                    proposition_id=proposition_id,
                    casa=casa,
                    secretaria=(entry.get("secretaria") or entry.get("Secretaria") or "").strip(),
                    tipo_sigla=(entry.get("tipo_sigla") or entry.get("sigla_tipo") or "").strip(),
                    numero=str(numero).strip(),
                    ano=ano,
                    assunto=(entry.get("assunto") or entry.get("tema") or "").strip(),
                    prioridade=prioridade,
                    justificativa=(entry.get("justificativa") or "").strip(),
                )
            )

        TrackedProposition.objects.bulk_create(objetos)

    return document


def build_document_payload(document: TrackedDocument) -> dict[str, Any]:
    itens = []
    for proposition in document.propositions.order_by("proposition_id"):
        itens.append(
            {
                "id_proposicao": proposition.proposition_id,
                "casa": proposition.get_casa_display(),
                "casa_sigla": "CD" if proposition.casa == TrackedProposition.CASA_CAMARA else "SF",
                "secretaria": proposition.secretaria,
                "tipo_sigla": proposition.tipo_sigla,
                "numero": proposition.numero,
                "ano": proposition.ano,
                "assunto": proposition.assunto,
                "prioridade": proposition.prioridade,
                "justificativa": proposition.justificativa,
            }
        )

    return {
        "descricao": document.description,
        "data_referencia": document.reference_label,
        "proposicoes": itens,
    }
