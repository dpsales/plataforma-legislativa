from __future__ import annotations

import logging
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Any

from django.utils import timezone

from .client import get_session

logger = logging.getLogger(__name__)

BASE_URL = "https://legis.senado.leg.br/dadosabertos"
_SENADOR_CACHE: dict[str, tuple[str, str]] | None = None


def _fetch_json(url: str) -> dict[str, Any] | None:
    session = get_session()
    try:
        response = session.get(url, timeout=30)
        response.raise_for_status()
        return response.json()  # type: ignore[no-any-return]
    except Exception as exc:  # pragma: no cover - defensivo
        logger.warning("Falha ao acessar %s: %s", url, exc)
        return None


def _fetch_content(url: str) -> bytes | None:
    session = get_session()
    try:
        response = session.get(url, timeout=30)
        response.raise_for_status()
        return response.content
    except Exception as exc:  # pragma: no cover - defensivo
        logger.warning("Falha ao acessar %s: %s", url, exc)
        return None


def _load_senadores() -> dict[str, tuple[str, str]]:
    global _SENADOR_CACHE
    if _SENADOR_CACHE is not None:
        return _SENADOR_CACHE
    payload = _fetch_json(f"{BASE_URL}/senador/lista/atual.json")
    mapa: dict[str, tuple[str, str]] = {}
    try:
        parlamentares = (
            payload.get("ListaParlamentarEmExercicio", {})
            .get("Parlamentares", {})
            .get("Parlamentar", [])
        ) if payload else []
        if isinstance(parlamentares, dict):
            parlamentares = [parlamentares]
        for item in parlamentares:
            identificacao = item.get("IdentificacaoParlamentar", {}) or {}
            nome = (identificacao.get("NomeParlamentar") or "").strip()
            partido = (identificacao.get("SiglaPartidoParlamentar") or "").strip()
            uf = (identificacao.get("UfParlamentar") or "").strip()
            if nome:
                mapa[nome.lower()] = (partido, uf)
    except Exception as exc:  # pragma: no cover - defensivo
        logger.debug("Falha ao interpretar lista de senadores: %s", exc)
    _SENADOR_CACHE = mapa
    return mapa


def _format_autor(raw: str | None) -> str:
    if not raw or raw == "Autor não disponível":
        return "Autor não disponível"
    nome = raw.rsplit("-", 1)[-1].strip() if " - " in raw else raw.strip()
    partido, uf = _load_senadores().get(nome.lower(), ("", ""))
    partido = partido if partido and partido != "Sem Partido" else ""
    uf = uf if uf and uf != "Sem UF" else ""
    if partido or uf:
        return f"{nome} ({partido}/{uf})".replace("//", "/").strip(" ()/")
    return nome


def _parse_datetime(valor: str | None) -> timezone.datetime | None:
    if not valor:
        return None
    for formato in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            parsed = datetime.strptime(valor, formato)
            if timezone.is_naive(parsed):
                return timezone.make_aware(parsed, timezone.get_current_timezone())
            return parsed.astimezone(timezone.get_current_timezone())
        except ValueError:
            continue
    return None


def fetch_senado_details(codigo_materia: int) -> dict[str, Any] | None:
    conteudo = _fetch_content(f"{BASE_URL}/materia/{codigo_materia}")
    if not conteudo:
        return None

    titulo = "Título não disponível"
    ementa = "Ementa não disponível"
    autor = "Autor não disponível"
    try:
        root = ET.fromstring(conteudo)
        titulo = root.findtext(".//DescricaoIdentificacaoMateria", titulo) or titulo
        ementa = root.findtext(".//EmentaMateria", ementa) or ementa
        autor_raw = root.findtext(".//Autor", "Autor não disponível")
        autor = _format_autor(autor_raw)
    except ET.ParseError as exc:  # pragma: no cover - defensivo
        logger.debug("Falha ao interpretar XML do Senado: %s", exc)

    ficha_url = f"https://www25.senado.leg.br/web/atividade/materias/-/materia/{codigo_materia}"
    link_inteiro_teor = ""
    status = "Status não disponível"
    ultima_movimentacao = ""
    data_movimentacao = None

    movimentacoes = _fetch_json(f"{BASE_URL}/materia/movimentacoes/{codigo_materia}.json")
    if movimentacoes:
        materia = movimentacoes.get("MovimentacaoMateria", {}).get("Materia", {})
        autuacoes = materia.get("Autuacoes", {}).get("Autuacao", []) if materia else []
        if isinstance(autuacoes, dict):
            autuacoes = [autuacoes]
        if autuacoes:
            historico = autuacoes[0].get("HistoricoSituacoes", {}).get("Situacao", [])
            if isinstance(historico, dict):
                historico = [historico]
            historico.sort(
                key=lambda item: _parse_datetime(item.get("DataSituacao")) or timezone.make_aware(datetime(1900, 1, 1)),
                reverse=True,
            )
            if historico:
                registro = historico[0]
                status = (registro.get("DescricaoSituacao") or "").strip() or status
                data_movimentacao = _parse_datetime(registro.get("DataSituacao"))
                ultima_movimentacao = registro.get("DescricaoSituacao") or ""
            informes = autuacoes[0].get("InformesLegislativos", {}).get("InformeLegislativo", [])
            if isinstance(informes, dict):
                informes = [informes]
            textos = []
            for informe in informes:
                associados = informe.get("TextosAssociados", {}).get("TextoAssociado", [])
                if isinstance(associados, dict):
                    associados = [associados]
                for texto in associados:
                    url_texto = (texto.get("UrlTexto") or "").strip()
                    if url_texto:
                        if url_texto.startswith("http://"):
                            url_texto = "https://" + url_texto[len("http://"):]
                        textos.append(url_texto)
            if textos:
                link_inteiro_teor = textos[0]

    return {
        "titulo": titulo or "Título não disponível",
        "ementa": ementa or "Ementa não disponível",
        "autor": autor or "Autor não disponível",
        "status": status or "Status não disponível",
        "ultima_movimentacao": ultima_movimentacao or "",
        "data_movimentacao": data_movimentacao,
        "link_ficha": ficha_url,
        "link_inteiro_teor": link_inteiro_teor,
        "fonte": "senado",
    }
