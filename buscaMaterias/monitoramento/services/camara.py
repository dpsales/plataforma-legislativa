from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from django.utils import timezone

from .client import get_session

logger = logging.getLogger(__name__)

API_BASE = "https://dadosabertos.camara.leg.br/api/v2"


def _parse_datetime(value: str | None) -> timezone.datetime | None:
    if not value:
        return None
    for pattern in ("%Y-%m-%dT%H:%M", "%Y-%m-%dT%H:%M:%S"):
        try:
            parsed = datetime.strptime(value, pattern)
            if timezone.is_naive(parsed):
                return timezone.make_aware(parsed, timezone.get_current_timezone())
            return parsed.astimezone(timezone.get_current_timezone())
        except ValueError:
            continue
    return None


def _fetch_json(url: str) -> dict[str, Any] | None:
    session = get_session()
    try:
        response = session.get(url, timeout=30)
        response.raise_for_status()
        return response.json()  # type: ignore[no-any-return]
    except Exception as exc:  # pragma: no cover - defensivo
        logger.warning("Falha ao acessar %s: %s", url, exc)
        return None


def _fetch_status(proposition_id: int) -> str:
    payload = _fetch_json(f"{API_BASE}/proposicoes/{proposition_id}")
    if not payload:
        return "Status não disponível"
    dados = payload.get("dados", {})
    status = dados.get("statusProposicao", {}) or {}
    return status.get("descricaoSituacao", "Status não disponível")


def _fetch_author_metadata(autor: dict[str, Any]) -> str:
    nome = autor.get("nome", "Autor não disponível")
    if autor.get("codTipo") != 1:
        return nome
    dep_uri = autor.get("uri", "")
    if not dep_uri:
        return nome
    payload = _fetch_json(dep_uri)
    if not payload:
        return nome
    dados = payload.get("dados", {})
    ultimo_status = dados.get("ultimoStatus", {}) or {}
    partido = (ultimo_status.get("siglaPartido") or "").strip()
    uf = (ultimo_status.get("siglaUf") or "").strip()
    if partido == "Sem Partido":
        partido = ""
    if uf == "Sem UF":
        uf = ""
    if partido or uf:
        return f"{nome} ({partido}/{uf})".replace("//", "/").strip(" ()/")
    return nome


def _fetch_author(proposition_id: int) -> str:
    payload = _fetch_json(f"{API_BASE}/proposicoes/{proposition_id}/autores")
    if not payload:
        return "Autor não disponível"
    autores = payload.get("dados", []) or []
    if not autores:
        return "Autor não disponível"
    principal = next((item for item in autores if item.get("ordemAssinatura") == 1), autores[0])
    return _fetch_author_metadata(principal)


def fetch_camara_details(proposition_id: int) -> dict[str, Any] | None:
    dados_basicos = _fetch_json(f"{API_BASE}/proposicoes/{proposition_id}")
    if not dados_basicos:
        return None

    conteudo = dados_basicos.get("dados", {})
    titulo = "Título não disponível"
    if conteudo:
        titulo = f"{conteudo.get('siglaTipo', '')} {conteudo.get('numero', '')}/{conteudo.get('ano', '')}".strip()
        titulo = titulo.strip(" /") or titulo

    ementa = conteudo.get("ementa", "Ementa não disponível")
    link_inteiro_teor = conteudo.get("urlInteiroTeor", "") or ""

    payload_tramitacoes = _fetch_json(f"{API_BASE}/proposicoes/{proposition_id}/tramitacoes")
    ultima_movimentacao = "N/A"
    data_movimentacao = None
    status = "Status não disponível"
    if payload_tramitacoes:
        dados_tram = payload_tramitacoes.get("dados", []) or []
        for item in dados_tram:
            data_str = item.get("dataHora")
            if data_str:
                item["dataHora_dt"] = _parse_datetime(data_str)
        fallback_dt = timezone.make_aware(datetime(1900, 1, 1))
        dados_tram.sort(
            key=lambda entry: (
                entry.get("sequencia") or 0,
                entry.get("dataHora_dt") or fallback_dt,
            ),
            reverse=True,
        )
        if dados_tram:
            registro = dados_tram[0]
            ultima_movimentacao = registro.get("despacho") or registro.get("descricaoTramitacao") or "N/A"
            data_movimentacao = registro.get("dataHora_dt")
            status = (
                registro.get("descricaoSituacao")
                or _fetch_status(proposition_id)
                or "Status não disponível"
            )
    if not status or status == "Status não disponível":
        status = _fetch_status(proposition_id)

    autor = _fetch_author(proposition_id)
    link_ficha = f"https://www.camara.leg.br/proposicoesWeb/fichadetramitacao?idProposicao={proposition_id}"

    return {
        "titulo": titulo or "Título não disponível",
        "ementa": ementa or "Ementa não disponível",
        "autor": autor or "Autor não disponível",
        "status": status or "Status não disponível",
        "ultima_movimentacao": ultima_movimentacao or "N/A",
        "data_movimentacao": data_movimentacao,
        "link_ficha": link_ficha,
        "link_inteiro_teor": link_inteiro_teor or "",
        "fonte": "camara",
    }
