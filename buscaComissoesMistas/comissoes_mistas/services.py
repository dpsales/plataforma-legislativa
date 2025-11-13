"""Serviços para coletar e persistir proposições em comissões do Senado."""
from __future__ import annotations

import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from typing import Iterable

import pandas as pd
import requests
from django.db import transaction
from django.utils import timezone
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .models import Proposition

logger = logging.getLogger(__name__)

BASE_URL = "https://legis.senado.leg.br/dadosabertos"
# COLEGIADOS_URL = f"{BASE_URL}/comissao/lista/colegiados"
COMISSOES_MISTAS_URL = f"{BASE_URL}/comissao/lista/mistas?format=json"
SITUACOES_COMISSOES = {"PRONTPAUT", "PEDVISTA", "INPAUTA"}
SITUACAO_PLENARIO = "PRONDEPLEN"
TIPOS_INTERESSE = {"PL", "PEC", "PLP", "PLC", "PLS", "PDL", "PDS", "PLN"}
TIPOS_TEXTO_PERMITIDOS = {
    "Relatório Legislativo",
    "Avulso inicial da matéria",
    "Projeto de Lei Ordinária",
    "Projeto de Lei Complementar",
    "Proposta de Emenda à Constituição",
}

SESSION = requests.Session()
SESSION.mount(
    "https://",
    HTTPAdapter(
        max_retries=Retry(
            total=3,
            status_forcelist=[429, 500, 502, 503, 504],
            backoff_factor=1.5,
            allowed_methods=frozenset({"GET"}),
        )
    ),
)

_catalog_cache: dict[str, object] = {"value": None, "expires_at": None}


def _safe_get(url: str) -> dict | None:
    for attempt in range(1, 4):
        try:
            response = SESSION.get(url, headers={"Accept": "application/json"}, timeout=60)
            response.raise_for_status()
            return response.json()
        except Exception as exc:  # pragma: no cover - defensivo
            logger.warning("Falha na requisição %s (%d/3): %s", url, attempt, exc)
            time.sleep(attempt)
    logger.error("Falha definitiva ao acessar %s", url)
    return None


def _parse_colegiados(payload: dict | None) -> list[dict[str, str]]:
    if not payload:
        return []
    cole = (
        payload.get("ListaColegiados", {})
        .get("Colegiados", {})
        .get("Colegiado", [])
    )
    if isinstance(cole, dict):
        cole = [cole]

    resultado: list[dict[str, str]] = []
    for item in cole:
        sigla = (item.get("Sigla") or "").strip()
        if not sigla:
            continue
        resultado.append(
            {
                "sigla": sigla,
                "nome": (item.get("Nome") or "").strip(),
                "sigla_casa": (item.get("SiglaCasa") or "").strip(),
                "codigo": str(item.get("Codigo") or item.get("CodigoColegiado") or "").strip(),
            }
        )

    return sorted(resultado, key=lambda entry: entry["sigla"])


def _parse_mistas(payload: dict | None) -> list[dict[str, str]]:
    if not payload:
        return []
    cole = (
        payload.get("ComissoesMistasCongresso", {})
        .get("Colegiados", {})
        .get("Colegiado", [])
    )
    if isinstance(cole, dict):
        cole = [cole]

    resultado: list[dict[str, str]] = []
    for item in cole:
        sigla = (item.get("SiglaColegiado") or "").strip()
        if not sigla:
            continue
        resultado.append(
            {
                "sigla": sigla,
                "nome": (item.get("NomeColegiado") or "").strip(),
                "codigo": str(item.get("CodigoColegiado") or "").strip(),
            }
        )

    return sorted(resultado, key=lambda entry: entry["sigla"])


def fetch_commission_catalog(force: bool = False) -> dict[str, object]:
    """Retorna catálogo de comissões mistas da API Senado."""
    now = timezone.now()
    cached = _catalog_cache.get("value")
    expires_at = _catalog_cache.get("expires_at")
    if not force and cached and isinstance(expires_at, datetime) and expires_at > now:
        return cached  # type: ignore[return-value]

    # colegiados = _parse_colegiados(_safe_get(COLEGIADOS_URL))
    comissoes_mistas = _parse_mistas(_safe_get(COMISSOES_MISTAS_URL))

    catalogo = {
        # "senate": colegiados,
        "mixed": comissoes_mistas,
        "generated_at": now,
    }
    _catalog_cache["value"] = catalogo
    _catalog_cache["expires_at"] = now + timedelta(minutes=60)
    return catalogo


def _commission_siglas() -> list[str]:
    catalogo = fetch_commission_catalog()
    vistos: set[str] = set()
    resultado: list[str] = []

    for chave in ("senate", "mixed"):
        for entry in catalogo.get(chave, []) or []:
            sigla = (entry or {}).get("sigla", "").strip().upper()
            if not sigla or sigla in vistos:
                continue
            vistos.add(sigla)
            resultado.append(sigla)

    if "PLEN" not in vistos:
        resultado.append("PLEN")

    return resultado


def _format_autor(raw: str | None) -> str:
    if not raw:
        return "Autor não informado"
    autores = [parte.strip() for parte in raw.split(",") if parte.strip()]
    if not autores:
        return "Autor não informado"
    if len(autores) == 1:
        return autores[0]
    return f"{autores[0]} e outros"


def _materias_para_registros(comissao: str, payload: dict | None) -> list[dict[str, str]]:
    if not payload:
        return []
    materias = (
        payload.get("ListaMateriasEmComissao", {})
        .get("Comissoes", {})
        .get("Comissao", [])
    )
    if isinstance(materias, dict):
        materias = [materias]

    registros: list[dict[str, str]] = []
    for bloco in materias:
        sigla_comissao = (bloco.get("Sigla") or comissao or "").strip().upper()
        itens = bloco.get("Materias", {}).get("Materia", [])
        if isinstance(itens, dict):
            itens = [itens]
        for materia in itens:
            situacao = materia.get("SituacaoAtualProcesso", {}) or {}
            registros.append(
                {
                    "id": str(materia.get("Codigo", "")).strip(),
                    "sigla_tipo": (materia.get("Sigla") or "").strip().upper(),
                    "numero": str(materia.get("Numero", "")).strip(),
                    "ano": str(materia.get("Ano", "")).strip(),
                    "ementa": (materia.get("Ementa") or "").strip(),
                    "autor": _format_autor(materia.get("Autor")),
                    "situacao_sigla": (situacao.get("SiglaSituacao") or "").strip().upper(),
                    "situacao": (situacao.get("DescricaoSituacao") or "").strip(),
                    "comissao": sigla_comissao,
                }
            )
    return registros


def _buscar_materias(comissao: str, situacao: str | None = None) -> list[dict[str, str]]:
    comissao_param = comissao.lower()
    url = f"{BASE_URL}/materia/lista/comissao?comissao={comissao_param}"
    if situacao:
        url = f"{url}&situacao={situacao}"
    dados = _safe_get(url)
    return _materias_para_registros(comissao, dados)


def _fetch_detalhes(codigo: str) -> dict[str, object]:
    if not codigo:
        return {"data": None, "historico": "", "textos": []}
    url = f"{BASE_URL}/materia/movimentacoes/{codigo}.json"
    dados = _safe_get(url)
    if not dados:
        return {"data": None, "historico": "", "textos": []}

    materia = dados.get("MovimentacaoMateria", {}).get("Materia", {})
    autuacoes = materia.get("Autuacoes", {}).get("Autuacao", [])
    if isinstance(autuacoes, dict):
        autuacoes = [autuacoes]
    if not autuacoes:
        return {"data": None, "historico": "", "textos": []}

    historico_lista = autuacoes[0].get("HistoricoSituacoes", {}).get("Situacao", [])
    if isinstance(historico_lista, dict):
        historico_lista = [historico_lista]

    entradas: list[tuple[datetime, str]] = []
    for item in historico_lista:
        data_raw = item.get("DataSituacao") or ""
        descricao = (item.get("DescricaoSituacao") or "").strip()
        parsed = _parse_datetime(data_raw)
        if parsed:
            entradas.append((parsed, f"{data_raw} - {descricao}".strip(" -")))
    entradas.sort(key=lambda par: par[0], reverse=True)

    textos_associados: list[dict[str, str]] = []
    informes = autuacoes[0].get("InformesLegislativos", {}).get("InformeLegislativo", [])
    if isinstance(informes, dict):
        informes = [informes]
    for informe in informes:
        colegiado = (informe.get("Colegiado", {}) or {}).get("SiglaColegiado", "")
        associados = informe.get("TextosAssociados", {}).get("TextoAssociado", [])
        if isinstance(associados, dict):
            associados = [associados]
        for texto in associados:
            descricao = (texto.get("DescricaoTipoTexto") or "").strip()
            if descricao not in TIPOS_TEXTO_PERMITIDOS:
                continue
            url_texto = (texto.get("UrlTexto") or "").strip()
            if not url_texto:
                continue
            if url_texto.startswith("http://"):
                url_texto = "https://" + url_texto[len("http://"):]
            label = descricao if not colegiado else f"{descricao} ({colegiado})"
            textos_associados.append({"label": label, "url": url_texto})

    historico = "\n".join(item for _, item in entradas if item)
    data_recente = entradas[0][0] if entradas else None
    return {"data": data_recente, "historico": historico, "textos": textos_associados}


def _parse_datetime(valor: str | None) -> datetime | None:
    if not valor:
        return None
    for formato in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            parsed = datetime.strptime(valor, formato)
            tz = timezone.get_current_timezone()
            if timezone.is_naive(parsed):
                return timezone.make_aware(parsed, tz)
            return parsed.astimezone(tz)
        except ValueError:
            continue
    return None


def fetch_dataset() -> pd.DataFrame:
    registros: list[dict[str, object]] = []

    for comissao in sorted(_commission_siglas()):
        if comissao == "PLEN":
            registros.extend(_buscar_materias("PLEN", SITUACAO_PLENARIO))
            continue
        for situacao in SITUACOES_COMISSOES:
            registros.extend(_buscar_materias(comissao, situacao))

    if not registros:
        logger.warning("Nenhuma matéria retornada pelas APIs do Senado")
        return pd.DataFrame()

    df = pd.DataFrame(registros)
    if df.empty:
        return pd.DataFrame()

    df = df[df["sigla_tipo"].isin(TIPOS_INTERESSE)].copy()
    df = df[df["situacao_sigla"].isin(SITUACOES_COMISSOES | {SITUACAO_PLENARIO})]
    if df.empty:
        logger.warning("Dados do Senado não possuem registros com os filtros definidos")
        return pd.DataFrame()

    numero_limpo = df["numero"].fillna("").astype(str).str.lstrip("0")
    numero_final = numero_limpo.where(numero_limpo != "", df["numero"].fillna(""))
    ano = df["ano"].fillna("")
    df["proposicao"] = (df["sigla_tipo"].fillna("") + " " + numero_final + "/" + ano).str.strip(" /")
    df["ficha_tramitacao_url"] = "https://www25.senado.leg.br/web/atividade/materias/-/materia/" + df["id"].astype(str)

    with ThreadPoolExecutor(max_workers=10) as executor:
        futuros = {executor.submit(_fetch_detalhes, codigo): codigo for codigo in df["id"]}
        detalhes: dict[str, dict[str, object]] = {}
        for futuro in as_completed(futuros):
            codigo = futuros[futuro]
            try:
                detalhes[codigo] = futuro.result()
            except Exception as exc:  # pragma: no cover - defensivo
                logger.debug("Falha ao obter detalhes %s: %s", codigo, exc)
                detalhes[codigo] = {"data": None, "historico": "", "textos": []}

    df["data_situacao_recente"] = df["id"].map(lambda codigo: detalhes.get(codigo, {}).get("data"))
    df["historico"] = df["id"].map(lambda codigo: detalhes.get(codigo, {}).get("historico", ""))
    df["textos_associados"] = df["id"].map(lambda codigo: detalhes.get(codigo, {}).get("textos", []))

    df.rename(columns={"id": "proposition_id"}, inplace=True)
    return df


def _build_defaults(row: pd.Series) -> dict[str, object]:
    data = row.get("data_situacao_recente")
    if isinstance(data, datetime):
        data_aware = data.astimezone(timezone.utc)
    else:
        data_aware = None

    historico = row.get("historico", "")
    if not isinstance(historico, str):
        historico = ""

    textos = row.get("textos_associados", [])
    if not isinstance(textos, list):
        textos = []

    return {
        "sigla_tipo": row.get("sigla_tipo", ""),
        "numero": row.get("numero", ""),
        "ano": row.get("ano", ""),
        "proposicao": row.get("proposicao", ""),
        "autor": row.get("autor", ""),
        "ementa": row.get("ementa", ""),
        "situacao_sigla": row.get("situacao_sigla", ""),
        "situacao": row.get("situacao", ""),
        "comissao": row.get("comissao", ""),
        "data_situacao_recente": data_aware,
        "historico": historico,
        "textos_associados": textos,
        "ficha_tramitacao_url": row.get("ficha_tramitacao_url", ""),
    }


def persist_dataset(df: pd.DataFrame) -> int:
    if df.empty:
        logger.warning("Nenhum dado para persistir no banco")
        return 0

    atualizados = 0
    ids_presentes: set[str] = set()
    with transaction.atomic():
        for _, row in df.iterrows():
            proposition_id = str(row.get("proposition_id", "")).strip()
            if not proposition_id:
                continue
            defaults = _build_defaults(row)
            Proposition.objects.update_or_create(
                proposition_id=proposition_id,
                defaults=defaults,
            )
            ids_presentes.add(proposition_id)
            atualizados += 1
        if ids_presentes:
            Proposition.objects.exclude(proposition_id__in=ids_presentes).delete()
    logger.info("Persistência concluída (%d registros ativos)", Proposition.objects.count())
    return atualizados


def refresh_dataset() -> int:
    inicio = time.monotonic()
    df = fetch_dataset()
    quantidade = persist_dataset(df)
    duracao = time.monotonic() - inicio
    logger.info("Atualização finalizada em %.1fs", duracao)
    return quantidade
