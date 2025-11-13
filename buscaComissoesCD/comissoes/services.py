"""Serviços de coleta e persistência das proposições em comissões da Câmara."""
from __future__ import annotations

import io
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

from .models import CommissionSelection, Proposition

logger = logging.getLogger(__name__)

TIPOS_PROP = {"PL", "MPV", "PDL", "PLP", "PEC", "PLN", "PLS", "PLC", "PDS", "PDN"}
SITUACOES_FILTER = {"Pronta para Pauta", "Aguardando Vistas"}
ORGAO_SIGLAS_FALLBACK = {"PLEN", "CCJC", "CFT", "CMO", "CCDD", "CAS", "CAE"}
ORGAOS_URL_TEMPLATE = (
    "http://dadosabertos.camara.leg.br/arquivos/orgaos/{formato}/orgaos.{formato}"
)
YEAR_MIN = 2023

SESSION = requests.Session()
SESSION.mount(
    "https://",
    HTTPAdapter(
        max_retries=Retry(
            total=3,
            backoff_factor=1.5,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=frozenset({"GET"}),
        )
    ),
)

_catalog_cache: dict[str, object] = {"value": None, "expires_at": None}


def _safe_get(url: str, *, timeout: float = 60.0) -> requests.Response | None:
    for attempt in range(1, 4):
        try:
            headers = {
                "User-Agent": "PlataformaLegislativa/1.0 (+https://github.com/)"
            }
            response = SESSION.get(url, timeout=timeout, headers=headers)
            response.raise_for_status()
            return response
        except Exception as exc:  # pragma: no cover - resiliente
            logger.warning("Falha na requisição %s (%d/3): %s", url, attempt, exc)
            time.sleep(1.5 * attempt)
    logger.error("Falha definitiva ao acessar %s", url)
    return None


def fetch_orgao_catalog(force: bool = False) -> dict[str, object]:
    """Retorna o catálogo de órgãos da Câmara (sigla e nome)."""
    now = timezone.now()
    cached = _catalog_cache.get("value")
    expires_at = _catalog_cache.get("expires_at")
    if not force and cached and isinstance(expires_at, datetime) and expires_at > now:
        return cached  # type: ignore[return-value]

    url = ORGAOS_URL_TEMPLATE.format(formato="csv")
    entries: list[dict[str, str]] = []

    response = _safe_get(url)
    if response and response.content:
        try:
            df = pd.read_csv(io.BytesIO(response.content), sep=";", engine="python", dtype=str)
        except Exception as exc:  # pragma: no cover - parsing defensivo
            logger.warning("Erro ao ler CSV de órgãos %s: %s", url, exc)
        else:
            registros: dict[str, str] = {}
            nome_col = None
            candidatos = {"nome", "nomeorgao", "descricao", "descricaoorgao"}
            for coluna in df.columns:
                chave = coluna.lower()
                if chave in candidatos:
                    nome_col = coluna
                    break
            for _, row in df.iterrows():
                sigla = str(row.get("sigla") or "").strip().upper()
                if not sigla:
                    continue
                nome = ""
                if nome_col:
                    nome = str(row.get(nome_col) or "").strip()
                registros[sigla] = nome
            if registros:
                entries = [
                    {"sigla": sigla, "nome": registros[sigla]}
                    for sigla in sorted(registros.keys())
                ]

    if not entries:
        logger.warning("Catálogo de órgãos indisponível; utilizando lista padrão")
        entries = [{"sigla": sigla, "nome": ""} for sigla in sorted(ORGAO_SIGLAS_FALLBACK)]

    catalogo = {
        "orgaos": entries,
        "generated_at": now,
    }
    _catalog_cache["value"] = catalogo
    _catalog_cache["expires_at"] = now + timedelta(minutes=60)
    return catalogo


def _allowed_orgao_siglas() -> set[str]:
    catalogo = fetch_orgao_catalog()
    return {
        str(item.get("sigla", "")).strip().upper()
        for item in catalogo.get("orgaos", [])
        if item.get("sigla")
    }


def selected_orgao_siglas() -> set[str]:
    configuracao = CommissionSelection.objects.filter(name=CommissionSelection.DEFAULT_NAME).first()
    if not configuracao or not configuracao.siglas:
        return set()
    selecionadas = {sigla.strip().upper() for sigla in configuracao.siglas if sigla}
    if not selecionadas:
        return set()
    permitidas = _allowed_orgao_siglas()
    if not permitidas:
        return selecionadas
    return {sigla for sigla in selecionadas if sigla in permitidas}


def _fetch_year(year: int, target_siglas: set[str]) -> pd.DataFrame:
    url = f"https://dadosabertos.camara.leg.br/arquivos/proposicoes/csv/proposicoes-{year}.csv"
    response = _safe_get(url)
    if response is None or not response.content:
        return pd.DataFrame()
    try:
        df = pd.read_csv(io.BytesIO(response.content), sep=";", engine="python", dtype=str)
    except Exception as exc:  # pragma: no cover - parsing defensive
        logger.warning("Erro ao ler CSV %s: %s", url, exc)
        return pd.DataFrame()

    df = df[df["siglaTipo"].isin(TIPOS_PROP)]
    df = df[df["ultimoStatus_descricaoSituacao"].isin(SITUACOES_FILTER)]
    df = df[df["ultimoStatus_siglaOrgao"].isin(target_siglas)]

    df["dataApresentacao"] = pd.to_datetime(df["dataApresentacao"], errors="coerce")
    df["ultimoStatus_dataHora"] = pd.to_datetime(df["ultimoStatus_dataHora"], errors="coerce")
    return df


def _obter_partido_uf(uri: str) -> tuple[str, str]:
    if not uri or not uri.startswith("http"):
        return "", ""
    url = uri
    response = _safe_get(url, timeout=20)
    if not response:
        return "", ""
    try:
        dados = response.json().get("dados", {})
        ultimo = dados.get("ultimoStatus")
        if not ultimo:
            return "", ""
        return ultimo.get("siglaPartido", "") or "", ultimo.get("siglaUf", "") or ""
    except Exception as exc:  # pragma: no cover - parsing defensive
        logger.debug("Falha ao obter partido/UF: %s", exc)
        return "", ""


def _fetch_author(prop_id: str) -> str:
    url = f"https://dadosabertos.camara.leg.br/api/v2/proposicoes/{prop_id}/autores"
    response = _safe_get(url, timeout=20)
    if not response:
        return ""
    try:
        autores = response.json().get("dados", [])
        if not autores:
            return ""
        principal = next((a for a in autores if a.get("proponente") == 1), autores[0])
        nome = (principal.get("nome") or "").strip()
        uri = principal.get("uri") or ""
        if uri.startswith("http"):
            partido, uf = _obter_partido_uf(uri)
            if partido and uf:
                return f"{nome} ({partido}/{uf})"
        return nome
    except Exception as exc:  # pragma: no cover - defensive
        logger.debug("Falha ao obter autor %s: %s", prop_id, exc)
        return ""


def fetch_dataset() -> pd.DataFrame:
    logger.info("Coletando proposições de comissões da Câmara")
    target_siglas = selected_orgao_siglas()
    if not target_siglas:
        logger.info("Nenhum órgão selecionado. Utilizando órgãos padrão.")
        target_siglas = ORGAO_SIGLAS_FALLBACK

    current_year = timezone.now().year
    start_year = YEAR_MIN
    frames: list[pd.DataFrame] = []
    for year in range(start_year, current_year + 1):
        df_year = _fetch_year(year, target_siglas)
        if df_year.empty:
            continue
        frames.append(df_year)
        logger.info("Ano %d: %d registros relevantes", year, len(df_year))
    if not frames:
        return pd.DataFrame()
    df = pd.concat(frames, ignore_index=True)

    with ThreadPoolExecutor(max_workers=12) as pool:
        futures = {pool.submit(_fetch_author, pid): pid for pid in df["id"]}
        for future in as_completed(futures):
            pid = futures[future]
            try:
                autor = future.result()
                df.loc[df["id"] == pid, "Autor"] = autor
            except Exception as exc:  # pragma: no cover - thread defensive
                logger.debug("Autor %s falhou: %s", pid, exc)

    numero_original = df["numero"].fillna("")
    numero_sanitizado = numero_original.str.lstrip("0")
    numero_final = numero_sanitizado.where(numero_sanitizado != "", numero_original)
    df["Proposicao"] = df["siglaTipo"] + " " + numero_final + "/" + df["ano"]
    df["Ficha"] = (
        "https://www.camara.leg.br/proposicoesWeb/fichadetramitacao?idProposicao="
        + df["id"].astype(str)
    )
    return df


def _build_defaults(row: pd.Series) -> dict[str, object]:
    def _clean(value: object) -> str:
        return "" if pd.isna(value) else str(value).strip()

    data_apresentacao = row.get("dataApresentacao")
    if isinstance(data_apresentacao, pd.Timestamp):
        data_apresentacao = data_apresentacao.date()
    else:
        data_apresentacao = None

    data_tram = row.get("ultimoStatus_dataHora")
    if isinstance(data_tram, pd.Timestamp):
        py_dt = data_tram.to_pydatetime()
        if data_tram.tzinfo is None:
            data_tram = timezone.make_aware(py_dt, timezone=timezone.utc)
        else:
            data_tram = py_dt.astimezone(timezone.utc)
    else:
        data_tram = None

    return {
        "sigla_tipo": _clean(row.get("siglaTipo")),
        "numero": _clean(row.get("numero")),
        "ano": _clean(row.get("ano")),
        "proposicao": _clean(row.get("Proposicao")),
        "autor": _clean(row.get("Autor")),
        "ementa": _clean(row.get("ementa")),
        "situacao": _clean(row.get("ultimoStatus_descricaoSituacao")),
        "situacao_tramitacao": _clean(row.get("ultimoStatus_descricaoTramitacao")),
        "orgao_sigla": _clean(row.get("ultimoStatus_siglaOrgao")),
        "inteiro_teor_url": _clean(row.get("urlInteiroTeor")),
        "ficha_tramitacao_url": _clean(row.get("Ficha")),
        "data_apresentacao": data_apresentacao,
        "data_ultima_tramitacao": data_tram,
    }


def persist_dataset(df: pd.DataFrame) -> int:
    if df.empty:
        logger.warning("Nenhum dado coletado para persistir")
        return 0

    updated = 0
    existing_ids: set[str] = set()
    with transaction.atomic():
        for _, row in df.iterrows():
            proposition_id = str(row.get("id", "")).strip()
            if not proposition_id:
                continue
            defaults = _build_defaults(row)
            _, _created = Proposition.objects.update_or_create(
                proposition_id=proposition_id,
                defaults=defaults,
            )
            existing_ids.add(proposition_id)
            updated += 1
        if existing_ids:
            Proposition.objects.exclude(proposition_id__in=existing_ids).delete()
    logger.info("Persistência concluída (%d registros ativos)", Proposition.objects.count())
    return updated


def refresh_dataset() -> int:
    start = time.monotonic()
    df = fetch_dataset()
    count = persist_dataset(df)
    elapsed = time.monotonic() - start
    logger.info("Atualização finalizada em %.1fs", elapsed)
    return count
