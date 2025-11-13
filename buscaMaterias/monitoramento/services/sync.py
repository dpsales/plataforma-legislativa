from __future__ import annotations

import logging
from typing import Iterable

from django.db import transaction

from ..models import TrackedDocument, TrackedProposition
from .camara import fetch_camara_details
from .senado import fetch_senado_details

logger = logging.getLogger(__name__)


def _update_proposition(proposition: TrackedProposition) -> bool:
    if proposition.casa == TrackedProposition.CASA_CAMARA:
        payload = fetch_camara_details(proposition.proposition_id)
    else:
        payload = fetch_senado_details(proposition.proposition_id)

    if not payload:
        logger.warning(
            "Nenhum dado retornado para %s (%s)",
            proposition.proposition_id,
            proposition.casa,
        )
        return False

    fields = {
        "titulo": payload.get("titulo", ""),
        "ementa": payload.get("ementa", ""),
        "autor": payload.get("autor", ""),
        "status": payload.get("status", ""),
        "ultima_movimentacao": payload.get("ultima_movimentacao", ""),
        "data_movimentacao": payload.get("data_movimentacao"),
        "link_ficha": payload.get("link_ficha", ""),
        "link_inteiro_teor": payload.get("link_inteiro_teor", ""),
        "fonte": payload.get("fonte", proposition.casa),
    }

    for field, value in fields.items():
        setattr(proposition, field, value or "" if isinstance(value, str) else value)

    update_fields = list(fields.keys()) + ["updated_at"]
    proposition.save(update_fields=update_fields)
    return True


def sync_document(document: TrackedDocument) -> int:
    atualizados = 0
    for proposition in document.propositions.all():
        try:
            if _update_proposition(proposition):
                atualizados += 1
        except Exception as exc:  # pragma: no cover - defensivo
            logger.exception(
                "Falha ao atualizar proposição %s (%s)",
                proposition.proposition_id,
                proposition.casa,
                exc_info=exc,
            )
    return atualizados


def sync_all_documents(documents: Iterable[TrackedDocument] | None = None) -> int:
    documentos = list(documents) if documents is not None else list(TrackedDocument.objects.all())
    total = 0
    for document in documentos:
        logger.info("Atualizando documento '%s'", document.name)
        with transaction.atomic():
            total += sync_document(document)
    return total
