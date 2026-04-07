#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Dash + coleta de proposições, upload p/ GCS e dashboard.
Requisitos:
    pip install dash dash-bootstrap-components pandas openpyxl requests google-cloud-storage
Env vars necessários:
    BUCKET_NAME   → nome do bucket GCS
    TMP_DIR       → opcional (/tmp por padrão)
"""
import os
import io
import re
import time
import unicodedata
import logging
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, List, Tuple, Union, Optional

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import dash
import dash_bootstrap_components as dbc
from dash import html, dcc, dash_table, Input, Output
from zoneinfo import ZoneInfo

# ---------------------------------------------------------------------
# Configuração de logging
# ---------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    force=True,
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------
# Constantes gerais
# ---------------------------------------------------------------------
TMP_DIR     = os.getenv("TMP_DIR", "data")
LOCAL_FILE  = os.path.join(TMP_DIR, "proposicoes_unificadas.xlsx")
CSV_FILE    = os.path.join(TMP_DIR, "proposicoes_unificadas.csv")
ALERTS_FILE = os.path.join(TMP_DIR, "alertas_situacao.csv")
TZ = ZoneInfo("America/Sao_Paulo")   # 🟢 fuso oficial de Brasília
ALERT_COLUMNS = [
    "Casa",
    "Tipo",
    "Proposição",
    "Situação Anterior",
    "Situação Atual",
    "Data Ultima Tramitação",
    "Atualizado Em",
]

# -----------------------------------------------------------------
# Helper para acessar datasets e recarregar os dados em memória
# -----------------------------------------------------------------
def load_dataset() -> Optional[pd.DataFrame]:
    if os.path.exists(CSV_FILE):
        try:
            return pd.read_csv(CSV_FILE, dtype=str)
        except Exception as exc:  # pragma: no cover - defesa
            log.warning("Falha ao carregar CSV consolidado: %s", exc)
            return None
    if os.path.exists(LOCAL_FILE):
        try:
            return pd.read_excel(LOCAL_FILE, dtype=str)
        except Exception as exc:  # pragma: no cover - defesa
            log.warning("Falha ao carregar XLSX consolidado: %s", exc)
            return None
    return None


def refresh_data():
    global df_original, casa_counts, cd_count, sf_count, df_alertas

    df_final = load_dataset()
    if df_final is None:
        log.info("Nenhum arquivo de dataset encontrado; carregando estado vazio")
        df_original = pd.DataFrame(columns=SELECTED_COLS)
        df_alertas = load_alerts()
        casa_counts = {}
        cd_count = 0
        sf_count = 0
        return

    missing_cols = [col for col in SELECTED_COLS if col not in df_final.columns]
    if missing_cols:
        log.warning(
            "Dataset sem colunas esperadas %s; carregando dataset vazio",
            missing_cols,
        )
        df_original = pd.DataFrame(columns=SELECTED_COLS)
        df_alertas = load_alerts()
        casa_counts = {}
        cd_count = 0
        sf_count = 0
        return

    df_original = df_final[SELECTED_COLS].copy().fillna("")

    # --- garante que Peso seja numérico para ordenação correta ---
    df_original["Peso"] = pd.to_numeric(
        df_original["Peso"], errors="coerce"
    ).fillna(0).astype(int)

    # Converte datas e formata links – mesmo pré-processamento que já existia
    df_original["Data Ultima Tramitação"] = pd.to_datetime(
        df_original["Data Ultima Tramitação"], errors="coerce"
    )
    df_original["Inteiro Teor - Inicial"] = df_original["Inteiro Teor - Inicial"]\
        .apply(lambda x: f"[Inteiro Teor]({x})" if pd.notna(x) and x.strip() else "")
    df_original["Ficha Tramitação"] = df_original["Ficha Tramitação"]\
        .apply(lambda x: f"[Ficha]({x})" if pd.notna(x) and x.strip() else "")

    # Contagens usadas nos rótulos
    casa_counts = df_original["Casa"].value_counts().to_dict()
    cd_count = casa_counts.get("CD", 0)
    sf_count = casa_counts.get("SF", 0)

    df_alertas = load_alerts()


def load_alerts() -> pd.DataFrame:
    if not os.path.exists(ALERTS_FILE):
        return pd.DataFrame(columns=ALERT_COLUMNS)
    try:
        alerts = pd.read_csv(ALERTS_FILE, dtype=str).fillna("")
        missing = [col for col in ALERT_COLUMNS if col not in alerts.columns]
        if missing:
            log.warning("Arquivo de alertas sem colunas %s; descartando conteúdo", missing)
            return pd.DataFrame(columns=ALERT_COLUMNS)
        return alerts[ALERT_COLUMNS]
    except Exception as exc:  # pragma: no cover - defensivo
        log.warning("Falha ao carregar alertas: %s", exc)
        return pd.DataFrame(columns=ALERT_COLUMNS)


def detect_status_changes(new_df: pd.DataFrame, previous_df: Optional[pd.DataFrame]) -> pd.DataFrame:
    if previous_df is None or previous_df.empty:
        return pd.DataFrame(columns=ALERT_COLUMNS)

    required_new = ["Casa", "Tipo", "Proposição", "Situação Atual", "Data Ultima Tramitação"]
    if any(col not in new_df.columns for col in required_new):
        log.warning("Dataset novo sem colunas necessárias para alertas")
        return pd.DataFrame(columns=ALERT_COLUMNS)
    if "Situação Atual" not in previous_df.columns:
        log.warning("Dataset anterior sem coluna 'Situação Atual'; alertas desativados")
        return pd.DataFrame(columns=ALERT_COLUMNS)

    def _normalize(series: pd.Series) -> pd.Series:
        return series.fillna("").astype(str).str.strip()

    novo = new_df[required_new].copy()
    antigo = previous_df[["Casa", "Proposição", "Situação Atual"]].copy()
    antigo = antigo.rename(columns={"Situação Atual": "Situação Anterior"})

    novo = novo.drop_duplicates(subset=["Casa", "Proposição"], keep="last")
    antigo = antigo.drop_duplicates(subset=["Casa", "Proposição"], keep="last")

    combinado = novo.merge(antigo, on=["Casa", "Proposição"], how="inner")

    combinado["Situação Atual"] = _normalize(combinado["Situação Atual"])
    combinado["Situação Anterior"] = _normalize(combinado["Situação Anterior"])
    combinado["Data Ultima Tramitação"] = _normalize(combinado["Data Ultima Tramitação"])

    alterados = combinado[
        (combinado["Situação Atual"] != combinado["Situação Anterior"])
        & combinado["Situação Atual"].ne("")
    ].copy()

    if alterados.empty:
        return pd.DataFrame(columns=ALERT_COLUMNS)

    alterados["Atualizado Em"] = datetime.now(tz=TZ).strftime("%Y-%m-%d %H:%M:%S")
    return alterados[
        [
            "Casa",
            "Tipo",
            "Proposição",
            "Situação Anterior",
            "Situação Atual",
            "Data Ultima Tramitação",
            "Atualizado Em",
        ]
    ]

# Sessão HTTP com retry
session = requests.Session()
retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET"],
)
adapter = HTTPAdapter(max_retries=retry_strategy)
session.mount("https://", adapter)
session.mount("http://", adapter)

# ---------------------------------------------------------------------
# Constantes de coleta Câmara (CSV)
# ---------------------------------------------------------------------
_ILLEGAL_RE = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F]")
def _xlsx_safe(v: Any) -> Any:
    return _ILLEGAL_RE.sub("", v) if isinstance(v, str) else v

URL_CSV_CAMARA = (
    "https://dadosabertos.camara.leg.br/arquivos/proposicoes/csv/"
    "proposicoes-{ano}.csv"
)
TIPOS_CAMARA = {"PL","MPV","PDL","PLP","PLV","PEC","PLN"}
SIT_EXC_CAMARA = {
    "Arquivada","Transformado em Norma Jurídica","Vetado totalmente",
    "Transformado em nova proposição","Retirado pelo(a) Autor(a)",
    "Devolvida ao(à) Autor(a)","Perdeu a Eficácia","Tramitação Finalizada",
    "Aguardando Despacho de Arquivamento",
}
SIT_TRAM_EXC_CAMARA = {
    "Arquivamento","Retirada pelo(a) Autor(a)",
    "Transformado em Norma Jurídica com Veto Parcial","Vetado Totalmente",
    "Arquivamento - Art.133 do RI","Transformação em Norma Jurídica",
}

# somente as colunas que vamos usar para reduzir memória
CAMARA_USECOLS = [
    "idProposicao",       # ou "id" se não existir
    "siglaTipo","numero","ano",
    "dataApresentacao","ementa",
    "ultimoStatus_dataHora",
    "ultimoStatus_descricaoSituacao",
    "ultimoStatus_descricaoTramitacao",
    "urlInteiroTeor"
]

# ---------------------------------------------------------------------
# Constantes de coleta Senado
# ---------------------------------------------------------------------
BASE_URL_SENADO   = "https://legis.senado.leg.br/dadosabertos"
HEADERS_SENADO    = {"Accept": "application/json"}
ITENS_POR_PAGINA  = 200
MAX_RETRIES       = 3
BACKOFF_FACTOR    = 1.5
TIMEOUT           = 15
MAX_WORKERS       = 2
TIPOS_SENADO      = {"PL","PEC","MPV","PDL","PLP","PRC","PLN","SUG","PLS",
                     "MSC","PEP","PDC","EPP","PDS","PLS","PLC", "PPR"}

# ---------------------------------------------------------------------
# Colunas finais e pesos
# ---------------------------------------------------------------------
COLUNAS = [
    "Casa","Tipo","Proposição","Autor","Data Apresent.","Ementa",
    "Situação Atual","Data Ultima Tramitação","Última Tramitação",
    "Peso","Inteiro Teor - Inicial","PESO SMA","Ficha Tramitação"
]

SELECTED_COLS = [
    "Casa", "Tipo", "Proposição", "Data Apresent.", "Ementa",
    "Situação Atual", "Data Ultima Tramitação", "Última Tramitação",
    "Peso", "Inteiro Teor - Inicial", "Ficha Tramitação"
]

# Valores padrão para evitar falhas na inicialização do Dash quando o XLSX ainda
# não está disponível ou teve o schema alterado.
df_original = pd.DataFrame(columns=SELECTED_COLS)
casa_counts = {}
cd_count = 0
sf_count = 0

# Pesos para cálculo de relevância
PESOS = {
    # NÚCLEO ESTRATÉGICO
    "Gestão": 14, "Inovação": 14, "Serviços Públicos": 14,
    "Administração Pública Federal": 12, "Governança": 10,
    "Transformação do Estado": 12, "Modernização": 10,

    # GOVERNO DIGITAL E TECNOLOGIA
    "Governo Digital": 14, "Digitalização": 12, "Serviços Digitais": 12,
    "Carteira de Identidade Nacional": 14, "CIN": 12, "Identificação Civil": 10,
    "Infraestrutura Nacional de Dados": 10, "IND": 8, "Dados Abertos": 8,
    "LGPD": 10, "Privacidade": 10, "Segurança da Informação": 10,
    "Inteligência Artificial": 10, "TIC": 8, "Tecnologia da Informação": 8,
    "SEI": 8, "Sistema Eletrônico de Informações": 8,
    "Estratégia Federal de Governo Digital": 10, "Cidadania Digital": 8,

    # CARGOS, FUNÇÕES E PESSOAS (CONGRESSO/LEIS)
    "Servidor Público": 14, "Carreiras Transversais": 14, "Carreira": 12,
    "Cargos Efetivos": 12, "Cargos em Comissão": 10, "Funções de Confiança": 10,
    "Remuneração": 10, "Estrutura Remuneratória": 10, "Vencimento Básico": 8,
    "Gratificações": 8, "Subsídio": 8, "Reestruturação de Carreiras": 12,
    "Concurso Público Nacional Unificado": 14, "CNU": 12, "Concursos Públicos": 12,
    "Lei 8.112": 10, "Estatuto do Servidor": 8, "Sigepe": 8,
    "Gestão de Pessoas": 12, "Desenvolvimento de Pessoas": 10,
    "Relações do Trabalho": 10, "Negociação Sindical": 8,
    "Acumulação de Cargos": 8, "Agentes Públicos": 10,

    # OUTRAS ÁREAS ESTRUTURANTES
    "Patrimônio da União": 12, "SPU": 8, "Imóveis Funcionais": 6,
    "Empresas Estatais": 10, "Governança Corporativa": 8, "SEST": 6,
    "Compras Públicas Centralizadas": 12, "Contratações Públicas": 10, "Logística": 8,
    "Enap": 8, "Capacitação": 8, "Funpresp-Exe": 6,
    "Protocolo de Intenções": 6, "Convênios": 6, "Transferências da União": 6,
    "Atos Normativos": 6, "Decretos": 6
}
PESOS_SMA = {
    # TÓPICOS CENTRAIS E ÓRGÃOS
    "CMAP": 12, "Conselho de Monitoramento e Avaliação de Políticas Públicas": 12,
    "Revisão do Gasto": 10, "Monitoramento e avaliação": 10,
    
    # PROCESSOS PRINCIPAIS
    "Monitoramento": 8, "Avaliação": 8, "Monitorar": 4, "Avaliar": 4, 
    
    # INSTRUMENTOS E RESULTADOS
    "Estudo de monitoramento": 8, "Estudo de avaliação": 8,
    "Relatório de monitoramento": 8, "Relatório de avaliação": 8,
    "Demonstrativos": 6, 
    
    # SUBSÍDIOS E BENEFÍCIOS (Tópico de Revisão de Gasto)
    "Subsídios": 10, 
    "Benefícios tributários": 9, "Benefícios financeiros": 9, "Benefícios creditícios": 9,
    
    # TIPOS DE MONITORAMENTO
    "Gasto Direto": 5, 
    "Monitoramento econômico": 7, "Monitoramento contábil": 7, "Monitoramento financeiro": 7,
}

try:
    import django  # type: ignore
    from django.apps import apps as django_apps  # type: ignore

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "base_pl.settings")
    if not django_apps.ready:  # type: ignore[attr-defined]
        django.setup()  # type: ignore[attr-defined]
    from pesos import services as pesos_services  # type: ignore

    try:
        _weights_map = pesos_services.load_all_weights()
    except Exception as exc:  # pragma: no cover - defensivo
        log.warning("Falha ao carregar pesos dinamicamente: %s", exc)
    else:
        if _weights_map.get("PESOS"):
            PESOS = dict(_weights_map["PESOS"])
        if _weights_map.get("PESOS_SMA"):
            PESOS_SMA = dict(_weights_map["PESOS_SMA"])
except Exception:  # pragma: no cover - ambiente sem Django
    pass

# ---------------------------------------------------------------------
# Funções auxiliares (Câmara + compartilhadas)
# ---------------------------------------------------------------------
def _sem_acento(txt: str) -> str:
    return unicodedata.normalize("NFKD", txt)\
        .encode("ascii", "ignore").decode()

def calcular_peso(texto: Any, mapa: dict[str,int]) -> int:
    if not isinstance(texto, str):
        return 0
    tx = _sem_acento(texto).lower()
    tot = 0
    for termo, p in mapa.items():
        pat = rf"\b{re.escape(_sem_acento(termo).lower())}\b"
        if re.search(pat, tx):
            tot += p
    return tot

# ---------------------------------------------------------------------
# Coleta Câmara (CSV enxuto, validações e parsing robusto)
# ---------------------------------------------------------------------
def coletar_camara() -> pd.DataFrame:
    log.info("🔎  Coletando CÂMARA (CSV)…")
    ano_atual = datetime.now().year
    frames: List[pd.DataFrame] = []

    for ano in range(1984, ano_atual + 1):
        url = URL_CSV_CAMARA.format(ano=ano)
        try:
            resp = session.get(url, timeout=TIMEOUT)
            resp.raise_for_status()

            # tenta ler apenas as colunas necessárias
            try:
                df_raw = pd.read_csv(
                    io.StringIO(resp.text),
                    sep=";",
                    dtype=str,
                    usecols=CAMARA_USECOLS,
                    on_bad_lines="skip",
                    encoding="utf-8"
                )
            except ValueError:
                # se não existir idProposicao, usa "id" como fallback
                cols = [c.replace("idProposicao", "id") for c in CAMARA_USECOLS]
                df_raw = pd.read_csv(
                    io.StringIO(resp.text),
                    sep=";",
                    dtype=str,
                    usecols=cols,
                    on_bad_lines="skip",
                    encoding="utf-8"
                ).rename(columns={"id": "idProposicao"})

            # valida colunas mínimas
            faltantes = set(CAMARA_USECOLS) - set(df_raw.columns)
            if faltantes:
                raise RuntimeError(f"Ano {ano}: faltam colunas {faltantes}")

            # aplica filtros
            df = df_raw[df_raw["siglaTipo"].isin(TIPOS_CAMARA)]
            df = df[~df["ultimoStatus_descricaoSituacao"].isin(SIT_EXC_CAMARA)]
            df = df[~df["ultimoStatus_descricaoTramitacao"].isin(SIT_TRAM_EXC_CAMARA)]

            # monta o mini-DataFrame já no formato final, preservando a data ISO
            mini = pd.DataFrame({
                "Casa": "CD",
                "Tipo": df["siglaTipo"],
                "Proposição": df["siglaTipo"] + " " + df["numero"] + "/" + df["ano"],
                "Autor": "",
                "Data Apresent.": df["dataApresentacao"],
                "Ementa": df["ementa"],
                "Situação Atual": df["ultimoStatus_descricaoSituacao"],
                "Data Ultima Tramitação": df["ultimoStatus_dataHora"],
                "Última Tramitação": df["ultimoStatus_descricaoTramitacao"],
                "Peso": df["ementa"].map(lambda x: calcular_peso(x, PESOS)),
                "Inteiro Teor - Inicial": df["urlInteiroTeor"],
                "PESO SMA": df["ementa"].map(lambda x: calcular_peso(x, PESOS_SMA)),
                "Ficha Tramitação": (
                    "https://www.camara.leg.br/proposicoesWeb/"
                    "fichadetramitacao?idProposicao=" + df["idProposicao"]
                )
            })

            frames.append(mini)
            log.info("  Ano %d: %d proposições", ano, len(mini))

        except Exception as e:
            log.warning("⚠ Ano %d falhou: %s", ano, e)

    if not frames:
        raise RuntimeError("Nenhum CSV da Câmara baixado com sucesso.")

    resultado = pd.concat(frames, ignore_index=True)
    return resultado[COLUNAS]

# --------------------------------------------------------------------
# ----------------------------- SENADO -------------------------------
# --------------------------------------------------------------------
class SenadoAPIError(Exception):
    """Erro de comunicação com a API do Senado."""

# ========= utilidades =================================================
def _get_json(endpoint: str, params: dict[str, Any]) -> Any:
    url = f"{BASE_URL_SENADO}/{endpoint}"
    for tent in range(1, MAX_RETRIES + 1):
        if log.level == logging.DEBUG:
            log.debug("→ GET %s %s (tent.%d)", url, params, tent)
        try:
            r = session.get(url, headers=HEADERS_SENADO,
                            params=params, timeout=TIMEOUT)
            r.raise_for_status()
            return r.json()
        except Exception as exc:
            if tent == MAX_RETRIES:
                raise SenadoAPIError(exc) from exc
            time.sleep(BACKOFF_FACTOR * tent)

def _extrair(obj: Any) -> List[dict]:
    """Detecta automaticamente o nome do contêiner e devolve a lista de processos."""
    if isinstance(obj, list):
        return obj
    if not isinstance(obj, dict):
        return []
    for k in ("listaProcessos", "ListaProcessos",
              "listaProcesso", "ListaProcesso"):
        if k in obj:
            container = obj[k]
            break
    else:
        return []
    if isinstance(container, list):
        return container
    for inn in ("processos", "Processos", "processo", "Processo"):
        if inn in container:
            lst = container[inn]
            return lst if isinstance(lst, list) else [lst]
    return []

def _tipo_senado(p: dict) -> str:
    ident = p.get("identificacao", "")
    return ident.split()[0].upper() if ident else ""

_CACHE_DET: dict[str, dict] = {}
def _det(pid: str) -> dict:
    """Detalhe completo de um processo (com cache in-memory)."""
    if pid not in _CACHE_DET:
        _CACHE_DET[pid] = _get_json(f"processo/{pid}", {"v": 1})
    return _CACHE_DET[pid]

def _url_documento_por_codigo(cod: Union[int, str]) -> str:
    try:
        j = _get_json("processo", {"codigoMateria": cod, "formato": "json"})
        lst = _extrair(j)
        return lst[0].get("urlDocumento", "") if lst else ""
    except SenadoAPIError:
        return ""

# ========= helpers para corrigir Data/Última Tramitação ===============
def _iso_date(raw: str) -> str:
    """
    Converte qualquer string de data para YYYY-MM-DDT00:00:00.
    Retorna '' se não for possível converter.
    """
    if not raw:
        return ""
    date_part = raw.split("T")[0].strip()  # corta hora se existir
    try:
        # valida data
        pd.to_datetime(date_part, errors="raise")
        return f"{date_part}T00:00:00"
    except Exception:
        return ""

def _coletar_eventos(detalhe: dict) -> List[Tuple[str, str]]:
    """
    Devolve todos os pares (data, descricao) encontrados em:
      • autuacoes[*].informesLegislativos[]
      • autuacoes[*].situacoes[]
    Data já no formato ISO (YYYY-MM-DDT00:00:00).
    """
    eventos: List[Tuple[str, str]] = []
    for aut in detalhe.get("autuacoes") or []:
        # Informes Legislativos – são os mais ricos
        for inf in aut.get("informesLegislativos", []):
            data_iso = _iso_date(inf.get("data", ""))
            desc = (inf.get("descricao") or "").strip()
            if data_iso and desc:
                eventos.append((data_iso, desc))

        # Situações – menos descritivas, mas úteis como fallback
        for sit in aut.get("situacoes", []):
            data_bruta = sit.get("fim") or sit.get("inicio") or ""
            data_iso = _iso_date(data_bruta)
            desc = (sit.get("descricao") or "").strip()
            if data_iso and desc:
                eventos.append((data_iso, desc))
    return eventos

# ========= campos enriquecidos =======================================
def _ementa_senado(p):
    if p.get("ementa"):
        return p["ementa"]
    try:
        return _det(str(p["id"])).get("conteudo", {}).get("ementa", "")
    except SenadoAPIError:
        return ""

def _autor_senado(p):
    try:
        d = _det(str(p["id"]))
        auts = d.get("autoriaIniciativa") \
            or d.get("documento", {}).get("autoria") \
            or []
        return auts[0].get("autor", "") if auts else ""
    except SenadoAPIError:
        return ""

def _data_ap_senado(p):
    try:
        dt = _det(str(p["id"])).get("documento", {}).get("dataApresentacao")
        return pd.to_datetime(dt).strftime("%d/%m/%Y") if dt else ""
    except SenadoAPIError:
        return ""

def _inteiro_teor(p):
    try:
        url = _det(str(p["id"])).get("documento", {}).get(
            "urlInteiroTeor", "")
        if url:
            return url
    except SenadoAPIError:
        pass
    try:
        cod = _det(str(p["id"])).get("codigoMateria")
        if cod:
            return _url_documento_por_codigo(cod)
    except SenadoAPIError:
        pass
    return ""

def _situacao_senado(p):
    """
    Situação Atual (campo 'Situação Atual' na planilha):
      1º) tenta campo direto retornado pela lista
      2º) tenta detalhe.autuacoes[0].situacoes[-1].descricao
      3º) tenta último evento de _coletar_eventos()
    """
    # nível superior
    s = (p.get("situacao") or p.get("situacaoAtual") or "").strip()
    if s:
        return s

    try:
        d = _det(str(p["id"]))
        aut = d.get("autuacoes") or []
        if aut and aut[0].get("situacoes"):
            s = aut[0]["situacoes"][-1]["descricao"].strip()
            if s:
                return s
        # fallback – mesmo algoritmo usado em _ult_senado
        eventos = _coletar_eventos(d)
        if eventos:
            # eventos já vêm ordenados posteriormente; pegamos o mais recente
            return eventos[-1][1]
    except SenadoAPIError:
        pass
    return ""

def _ult_senado(p) -> Tuple[str, str]:
    """
    Retorna (descricao, data_iso) da ÚLTIMA tramitação do Senado.
    Procura sempre o evento mais recente dentre:
      • informesLegislativos
      • situacoes
    """
    try:
        detalhe = _det(str(p["id"]))
        eventos = _coletar_eventos(detalhe)
        if not eventos:
            return "", ""

        # ordena pela data ISO crescente e pega o último
        eventos.sort(key=lambda t: t[0])
        data_iso, desc = eventos[-1]
        return desc, data_iso
    except SenadoAPIError:
        return "", ""

def _codigo_materia(p) -> str:
    try:
        return str(_det(str(p["id"])).get("codigoMateria", ""))
    except SenadoAPIError:
        return ""

# ========= varredura principal =======================================
def _listar_processos() -> List[dict]:
    processos, vistos = [], set()
    pag = 1
    while True:
        page = _get_json("processo", {
            "tramitando": "S", "pagina": pag,
            "itens": ITENS_POR_PAGINA, "formato": "json"
        })
        lote = _extrair(page)
        novos = 0
        for p in lote:
            if _tipo_senado(p) not in TIPOS_SENADO:
                continue
            pid = str(p["id"])
            if pid not in vistos:
                vistos.add(pid)
                processos.append(p)
                novos += 1
        if log.level == logging.DEBUG:
            log.debug("  página %d: +%d novos", pag, novos)
        if novos == 0:
            break
        pag += 1
    return processos

def coletar_senado() -> pd.DataFrame:
    log.info("🔎  Coletando SENADO…")
    brutos = _listar_processos()
    registros: List[dict] = []

    def enrich(p: dict) -> dict:
        emt = _ementa_senado(p)
        ult_desc, ult_dt = _ult_senado(p)
        cod_mat = _codigo_materia(p)
        ficha = (
            f"https://www25.senado.leg.br/web/atividade/materias/-/materia/{cod_mat}"
            if cod_mat else ""
        )
        return {
            "Casa": "SF",
            "Tipo": _tipo_senado(p),
            "Proposição": p["identificacao"],
            "Autor": _autor_senado(p),
            "Data Apresent.": _data_ap_senado(p),
            "Ementa": emt,
            "Situação Atual": _situacao_senado(p),
            "Data Ultima Tramitação": ult_dt,
            "Última Tramitação": ult_desc,
            "Peso": calcular_peso(emt, PESOS),
            "Inteiro Teor - Inicial": _inteiro_teor(p),
            "PESO SMA": calcular_peso(emt, PESOS_SMA),
            "Ficha Tramitação": ficha,
        }

    with ThreadPoolExecutor(MAX_WORKERS) as pool:
        for f in as_completed(pool.submit(enrich, p) for p in brutos):
            registros.append(f.result())
    return pd.DataFrame(registros)[COLUNAS]

# ---------------------------------------------------------------------
# Função principal
# ---------------------------------------------------------------------
def main() -> pd.DataFrame:
    ini = time.time()
    previous_df = load_dataset()
    df_cam = coletar_camara()
    df_sen = coletar_senado()
    df_final = pd.concat([df_cam, df_sen], ignore_index=True).apply(_xlsx_safe)
    df_final = df_final.applymap(_xlsx_safe)

    os.makedirs(TMP_DIR, exist_ok=True)
    df_final.to_excel(LOCAL_FILE, index=False, engine="openpyxl")
    log.info("💾 Salvo em %s", LOCAL_FILE)
    df_final.to_csv(CSV_FILE, index=False)
    log.info("💾 Salvo em %s", CSV_FILE)

    novos_alertas = detect_status_changes(df_final, previous_df)
    if not novos_alertas.empty:
        existentes = load_alerts()
        consolidados = pd.concat([novos_alertas, existentes], ignore_index=True)
        consolidados = consolidados.drop_duplicates(
            subset=["Casa", "Proposição", "Situação Atual"], keep="first"
        )
        consolidados = consolidados.sort_values(
            by="Atualizado Em", ascending=False, kind="stable"
        )
        consolidados.to_csv(ALERTS_FILE, index=False)
        log.info("🚨 %d novas alterações de situação registradas", len(novos_alertas))
    else:
        log.info("Nenhuma alteração de situação identificada.")

    log.info("⏱ Duração: %.1f s", time.time() - ini)
    return df_final

# ---------------------------------------------------------------------
# Download inicial para o Dash (agora apenas lê o arquivo local)
# ---------------------------------------------------------------------
try:
    os.makedirs(TMP_DIR, exist_ok=True)
    # Apenas para garantir que o arquivo exista para o refresh_data não falhar na primeira execução
    if not os.path.exists(LOCAL_FILE):
        pd.DataFrame().to_excel(LOCAL_FILE)
    if not os.path.exists(CSV_FILE):
        pd.DataFrame(columns=SELECTED_COLS).to_csv(CSV_FILE, index=False)
    if not os.path.exists(ALERTS_FILE):
        pd.DataFrame(columns=ALERT_COLUMNS).to_csv(ALERTS_FILE, index=False)
    refresh_data()
except Exception as exc:
    log.warning("Não foi possível ler o arquivo XLSX inicial: %s", exc)


# Data de atualização – prioriza CSV; fallback para XLSX
dataset_path = CSV_FILE if os.path.exists(CSV_FILE) else LOCAL_FILE
try:
    mod_ts = os.path.getmtime(dataset_path)
except FileNotFoundError:
    mod_ts = time.time()
update_date = datetime.fromtimestamp(mod_ts, tz=TZ)\
    .strftime("%d/%m/%Y às %H:%M")

# ----------------------------------------------------------
# 1.2) Definição das colunas do DataTable
# ----------------------------------------------------------
columns = []
for col in SELECTED_COLS:
    col_dict = {"id": col}
    if col in {"Inteiro Teor - Inicial", "Ficha Tramitação"}:
        col_dict["presentation"] = "markdown"
    columns.append(col_dict)

# ----------------------------------------------------------
# 2) Criação da aplicação Dash
# ----------------------------------------------------------
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    title="Busca Avançada em Proposições"
)
server = app.server  # para adicionar rota customizada

app.layout = dbc.Container([
    # Título
    dbc.Row(dbc.Col(
        html.H1("Busca Avançada em Proposições", style={
            "color": "#183EFF", "fontFamily": "Verdana",
            "marginTop": "20px", "marginBottom": "0"
        })
    )),
    # Linha divisória
    dbc.Row(dbc.Col(html.Hr(style={"borderTop": "2px solid #183EFF", "margin": "20px 0"}))),
    # Mensagem de atualização
    dbc.Row(dbc.Col(html.Div(
        f"Dados atualizados em {update_date}\n"
        "Dados obtidos via Dados Abertos da CD e do SF\n"
        "Classificação global (todas as páginas) por última tramitação",
        style={
            "whiteSpace": "pre-wrap", "textAlign": "right",
            "fontSize": "0.9em", "fontFamily": "Verdana, sans-serif",
            "fontStyle": "italic", "marginBottom": "20px"
        }
    ))),
    # Campo de busca
    dbc.Row(dbc.Col(dcc.Input(
        id="search-input", type="text", placeholder="Buscar na ementa...",
        style={
            "width": "100%", "padding": "10px", "marginBottom": "20px",
            "fontFamily": "Verdana, sans-serif", "fontSize": "14px"
        }
    ))),
    # Filtro por Casa
    dbc.Row(dbc.Col(html.Div([
        html.Label("Filtrar por Casa:", style={"fontWeight": "bold"}),
        dcc.Checklist(
            id="casa-filter",
            options=[
                {"label": f"CD ({cd_count})", "value": "CD"},
                {"label": f"SF ({sf_count})", "value": "SF"}
            ],
            value=["CD", "SF"],
            inline=True,
            labelStyle={"marginRight": "30px", "fontFamily": "Verdana, sans-serif"},
            style={"marginBottom": "20px"}
        )
    ]))),
    # Botão de exportação
    dbc.Row(dbc.Col(dbc.Button("Exportar XLSX", id="export-xlsx-button", color="primary"),
                   className="mb-3")),
    dcc.Download(id="download-xlsx"),
    # Tabela
    dbc.Row(dbc.Col(dcc.Loading(
        id="loading-table", type="default",
        children=[dash_table.DataTable(
            id="table", columns=columns, data=[],
            page_action="custom", page_current=0, page_size=50,
            sort_action="custom", sort_mode="multi",
            fixed_rows={"headers": True},
            markdown_options={"link_target": "_blank"},
            style_header={
                'backgroundColor': '#183EFF', 'fontWeight': 'bold',
                'color': 'white', 'fontFamily': 'Verdana, sans-serif',
                'whiteSpace': 'normal', 'height': 'auto',
                'lineHeight': '18px', 'fontSize': '14px'
            },
            style_cell={
                'textAlign': 'left', 'padding': '5px',
                'whiteSpace': 'normal', 'height': 'auto',
                'fontFamily': 'Verdana, sans-serif',
                'wordBreak': 'break-word'
            },
            style_cell_conditional=[
                {"if": {"column_id": "Casa"}, "width": "60px"},
                {"if": {"column_id": "Tipo"}, "width": "80px"},
                {"if": {"column_id": "Proposição"}, "width": "180px"},
                {"if": {"column_id": "Data Apresent."}, "width": "120px"},
                {"if": {"column_id": "Ementa"}, "width": "300px"},
                {"if": {"column_id": "Situação Atual"}, "width": "180px"},
                {"if": {"column_id": "Data Ultima Tramitação"}, "width": "140px"},
                {"if": {"column_id": "Última Tramitação"}, "width": "140px"},
                {"if": {"column_id": "Peso"}, "width": "60px"},
                {"if": {"column_id": "Inteiro Teor - Inicial"}, "width": "110px"},
                {"if": {"column_id": "Ficha Tramitação"}, "width": "100px"},
            ],
                style_table={
                    'minWidth': '100%',
                    'overflowX': 'auto',
                    'height': '600px',                # 🟢 altura da área visível
                    'overflowY': 'auto'               # 🟢 ativa rolagem vertical
                }
        )]
    ))),
], fluid=True)

# ----------------------------------------------------------
# 3) Callback de Paginação, Ordenação, Busca e Filtro por Casa
# ----------------------------------------------------------
@app.callback(
    [Output("table", "data"), Output("table", "page_count")],
    [Input("table", "page_current"), Input("table", "page_size"),
     Input("table", "sort_by"), Input("search-input", "value"),
     Input("casa-filter", "value")]
)
def update_table(page_current, page_size, sort_by, search_value, selected_casas):
    dff = df_original.copy()
    if selected_casas:
        dff = dff[dff["Casa"].isin(selected_casas)]
    if search_value:
        dff = dff[dff["Ementa"].str.contains(search_value.strip(), case=False, na=False)]
    if not sort_by:
        dff = dff.sort_values(
            by=["Data Ultima Tramitação", "Peso"],
            ascending=[False, False], kind="stable"
        )
    else:
        for s in reversed(sort_by):
            dff = dff.sort_values(
                by=s["column_id"],
                ascending=(s["direction"] == "asc"),
                kind="stable"
            )
    total_pages = -(-len(dff) // page_size)
    start, end = page_current * page_size, (page_current + 1) * page_size
    return dff.iloc[start:end].to_dict("records"), total_pages

# ----------------------------------------------------------
# 4) Callback de Exportar XLSX
# ----------------------------------------------------------
@app.callback(
    Output("download-xlsx", "data"),
    Input("export-xlsx-button", "n_clicks"),
    prevent_initial_call=True
)
def export_xlsx(_):
    buffer = io.BytesIO()
    df_export = df_original.drop(columns=["PESO SMA"], errors="ignore")
    df_export.to_excel(buffer, index=False)
    buffer.seek(0)
    return dcc.send_bytes(buffer.getvalue(), filename="proposicoes_consolidadas.xlsx")

# ---------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------
@app.server.route("/update-data", methods=["POST"])
def update_data():
    try:
        main()              # gera e envia o novo XLSX
        refresh_data()      # 🟢 recarrega dados em memória
        return "Dados atualizados com sucesso", 200
    except Exception as e:
        log.exception("Erro em /update-data")
        return f"Erro: {e}", 500

@app.server.route("/healthz")
def healthz():
    return "ok", 200

# ----------------------------------------------------------
# Execução
# ----------------------------------------------------------
if __name__ == "__main__":
    # Porta padrão do Cloud Run: 8080
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8080)),
            debug=False, dev_tools_ui=False)
