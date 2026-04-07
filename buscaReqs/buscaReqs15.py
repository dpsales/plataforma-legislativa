"""Generate a static HTML page listing requerimentos of interest.# #!/usr/bin/env python

# # -*- coding: utf-8 -*-

The original version of this script bundled a Flask + Dash application.  The

project now exposes the interactive experience through the Django service, so# # ----------------------------------------------------------

this helper focuses on a reproducible, non-interactive export.  It fetches data# # IMPORTS

from the Câmara e Senado open-data APIs (or a local SQLite snapshot, when# # ----------------------------------------------------------

available), applies the terms configured in the Django admin, and writes a

Bootstrap flavoured HTML table that can be served directly by the portal.

"""# from apscheduler.schedulers.background import BackgroundScheduler

# import time

from __future__ import annotations# import re

# from flask import Flask, jsonify

import argparse# import dash

import datetime as dt# import threading

import html# import pytz

import json# from requests.adapters import HTTPAdapter, Retry

import logging# import http.client

import sqlite3# from json import JSONDecodeError

from dataclasses import dataclass, field# from requests.exceptions import ChunkedEncodingError

from pathlib import Path# from PyPDF2 import PdfReader

from typing import Iterable, Sequence

# # >>> Biblioteca do Google Cloud Storage <<<

import requests# from google.cloud import storage



LOGGER = logging.getLogger(__name__)# from concurrent.futures import ThreadPoolExecutor, as_completed

# MAX_WORKERS = 12

BASE_DIR = Path(__file__).resolve().parent

DEFAULT_OUTPUT = BASE_DIR / "templates" / "requisicoes" / "busca.html"# # ---- Banco de Dados (novo) ----

DEFAULT_DB_PATH = BASE_DIR / "data" / "db.sqlite3"# from sqlalchemy import create_engine, text

CAMARA_API_BASE = "https://dadosabertos.camara.leg.br/api/v2"# from sqlalchemy.exc import SQLAlchemyError

SENADO_API_BASE = "https://legis.senado.leg.br/dadosabertos"

REQUEST_TIMEOUT = 45# # ----------------------------------------------------------

# # FLASK SERVER / LOG / VARIÁVEIS GLOBAIS

# # ----------------------------------------------------------

@dataclass# server = Flask(__name__)

class Configuration:

    proposition_types: list[str] = field(default_factory=list)# logging.basicConfig(

    presentation_years: list[int] = field(default_factory=list)#     level=logging.INFO,

    unit_groups: list[dict] = field(default_factory=list)#     format='[%(asctime)s] %(levelname)s - %(message)s'

    subjects: list[dict] = field(default_factory=list)# )

    updated_at: dt.datetime | None = None# logger = logging.getLogger(__name__)

# logger.setLevel(logging.DEBUG)

    @property

    def unit_terms(self) -> list[str]:# # Flags / Modo

        terms: list[str] = []# LOCAL_MODE = str(os.getenv("LOCAL_MODE", "true")).lower() == "true"   # True = teste local | False = produção (GCS)

        for group in self.unit_groups:# USE_DB     = str(os.getenv("USE_DB", "false")).lower() == "true"      # Liga/desliga uso de banco

            for term in group.get("terms", []) or []:

                term_str = str(term).strip()# # GCS (opcional)

                if term_str and term_str not in terms:# BUCKET_NAME       = os.getenv("BUCKET_NAME", "data")

                    terms.append(term_str)# GCS_OBJECT_NAME   = os.getenv("GCS_OBJECT_NAME", "resultados_filtrados_expressa.xlsx")

        return terms# LOCAL_OUTPUT_FILE = os.getenv("LOCAL_OUTPUT_FILE", "data/resultados_filtrados_expressa.xlsx")



# # DB URL (Postgres ou MySQL)

@dataclass# DB_URL = os.getenv("DB_URL", "")  # Ex.: postgresql+psycopg2://usuario:senha@host:5432/db

class Proposition:

    titulo: str# scheduler_global = None

    autor: str

    ementa: str# def is_db_empty() -> bool:

    situacao: str#     """Verifica se a tabela de proposicoes está vazia."""

    data_apresentacao: str#     if not USE_DB:

    data_ultima_tramitacao: str#         return True # Se não usa DB, considera "vazio" para fins de arquivo

    link_ficha: str#     engine = get_engine()

    link_inteiro_teor: str#     if engine is None:

    termos_encontrados: str#         return True

    grupos_encontrados: str#     try:

    assuntos_encontrados: str#         with engine.begin() as conn:

    local: str#             # Query mais eficiente para verificar se existe algum registro

    casa: str#             result = conn.execute(text("SELECT 1 FROM proposicoes LIMIT 1")).scalar()

#             is_empty = result is None

#             logger.info(f"Verificando se DB está vazio: {'Sim' if is_empty else 'Não'}")

def parse_iso_datetime(value: str | None) -> dt.datetime | None:#             return is_empty

    if not value:#     except SQLAlchemyError as e:

        return None#         logger.error(f"Erro ao verificar se DB está vazio: {e}")

    value = value.strip()#         # Em caso de erro, é mais seguro assumir que está vazio e tentar buscar dados.

    if not value:#         return True

        return None

    cleaned = value.replace("Z", "+00:00")# # ----------------------------------------------------------

    for parser in (# # TERMOS DE INTERESSE E CONSTANTES

        dt.datetime.fromisoformat,# # ----------------------------------------------------------

        lambda v: dt.datetime.strptime(v, "%Y-%m-%d"),# TERMOS = [

        lambda v: dt.datetime.strptime(v, "%d/%m/%Y"),#     "Dweck"

        lambda v: dt.datetime.strptime(v, "%d/%m/%Y %H:%M"),#     "Esther Dweck",

    ):#     "Governo Federal",

        try:#     "Ministério da Gestão e Inovação em Serviços Públicos",

            candidate = parser(cleaned)#     # 1. NÚCLEO ESTRATÉGICO E POLÍTICA

        except ValueError:#     "Gestão", 

            continue#     "Inovação",

        if candidate.tzinfo is None:#     "Reforma Administrativa",

            return candidate.replace(tzinfo=dt.timezone.utc)#     "Carreiras Transversais", 

        return candidate.astimezone(dt.timezone.utc)#     "Concurso Público Nacional Unificado",

    return None#     "CNU",

#     "Transformação do Estado",

#     "Administração Pública Federal",

def format_display_date(value: str | None) -> str:#     "Eficiência",

    dt_obj = parse_iso_datetime(value)#     # 2. GOVERNO DIGITAL E TECNOLOGIA

    if not dt_obj:#     "Governo Digital",

        return ""#     "Carteira de Identidade Nacional",

    local = dt_obj.astimezone(dt.datetime.now().astimezone().tzinfo)#     "CIN",

    if local.hour == 0 and local.minute == 0:#     "Identidade Digital",

        return local.strftime("%d/%m/%Y")#     "Digitalização",

    return local.strftime("%d/%m/%Y %H:%M")#     "Serviços Digitais",

#     "LGPD",

#     "Segurança da Informação",

def load_configuration(db_path: Path) -> Configuration:#     "Cibersegurança",

    if not db_path.exists():#     "Inteligência Artificial",

        LOGGER.debug("SQLite database not found at %s", db_path)#     "SISP", "Gov.br",

        return Configuration()#     "Gov.br",

    try:#     "Sistemas Estruturantes",

        conn = sqlite3.connect(db_path)#     # 3. PESSOAL, CARGOS E FUNÇÕES

    except sqlite3.Error as exc:  # pragma: no cover - IO error guard#     "Servidor Público",

        LOGGER.warning("Could not open SQLite database: %s", exc)#     "Reestruturação de Carreiras",

        return Configuration()#     "Plano de Cargos e Salários",

    conn.row_factory = sqlite3.Row#     "Cargos Efetivos",

    try:#     "Funções de Confiança",

        row = conn.execute(#     "Remuneração",

            """#     "Gestão de Pessoas",

            SELECT proposition_types, presentation_years, unit_groups, subjects, updated_at#     "Desenvolvimento de Pessoas",

            FROM requisicoes_configuration#     "Relações do Trabalho",

            ORDER BY id ASC LIMIT 1#     "Negociação", 

            """#     # 4. FISCALIZAÇÃO E REVISÃO DE GASTOS

        ).fetchone()#     "CMAP",

    except sqlite3.Error as exc:#     "Conselho de Monitoramento e Avaliação de Políticas Públicas",

        LOGGER.debug("Configuration table not available: %s", exc)#     "Revisão do Gasto",

        conn.close()#     "Auditoria",

        return Configuration()#     "Fiscalização",

    conn.close()#     "Monitoramento e avaliação",

    if not row:#     "Subsídios", 

        return Configuration()#     "Benefícios tributários",

#     "Benefícios financeiros",

    def parse_json_field(value: str | None, default: Iterable | None = None) -> list:#     "Benefícios creditícios",

        if value in (None, "", "null"):#     "Monitoramento",

            return list(default or [])#     "Avaliação",

        try:#     "TCU",

            payload = json.loads(value)#     # 5. LOGÍSTICA, COMPRAS E PATRIMÔNIO

        except json.JSONDecodeError as exc:#     "Licitações",

            LOGGER.warning("Invalid JSON in configuration: %s", exc)#     "Compras Públicas Centralizadas",

            return list(default or [])#     "Contratações Públicas",

        if isinstance(payload, list):#     "Patrimônio da União",

            return payload#     "Imóveis da União",

        return list(default or [])#     "SPU",

#     "Receitas Patrimoniais",

    updated_at = None#     "Sustentabilidade",

    if row["updated_at"]:#     "Compras Sustentáveis",

        updated_at = parse_iso_datetime(str(row["updated_at"]))#     "Logística",

#     "SIASG", 

    years = [int(y) for y in parse_json_field(row["presentation_years"], []) if str(y).isdigit()]#     # 6. GOVERNANÇA E CONTROLE

#     "Governança", 

    return Configuration(#     "Transparência",

        proposition_types=[str(item).strip().upper() for item in parse_json_field(row["proposition_types"], [])],#     "LAI", 

        presentation_years=sorted(years),#     "Acesso à Informação",

        unit_groups=parse_json_field(row["unit_groups"], []),#     "Governo Aberto", 

        subjects=parse_json_field(row["subjects"], []),#     "Participação Social", 

        updated_at=updated_at,#     "Empresas Estatais", 

    )#     "Governança Corporativa",

#     "Conselhos de Usuários"

# ]

def match_unit_terms(text: str, unit_groups: Sequence[dict]) -> tuple[str, str]:

    if not text or not unit_groups:# TIPOS_BUSCA_CAMARA = ["RIC", "INC", "REQ", "RCP", "REL", "RDP", "REC", "RQN", 

        return "", ""#                       "RPD","RQC", "RCM"]

    lowered = text.lower()# URL_CAMARA         = "https://dadosabertos.camara.leg.br/api/v2/proposicoes"

    matched_terms: set[str] = set()

    matched_groups: list[str] = []# # ==============================================================================

    for group in unit_groups:# # CAMADA DE BANCO – helpers

        terms = [str(term).strip() for term in (group.get("terms") or []) if str(term).strip()]# # ==============================================================================

        if not terms:# _engine = None

            continue

        hits = [term for term in terms if term.lower() in lowered]# def get_engine():

        if hits:#     global _engine

            matched_terms.update(hits)#     if not USE_DB:

            label = str(group.get("label") or group.get("value") or "").strip()#         return None

            if label:#     if _engine is None:

                matched_groups.append(f"{label}: {', '.join(hits)}")#         if not DB_URL:

    return ", ".join(sorted(matched_terms)), "; ".join(matched_groups)#             logger.error("USE_DB=true mas DB_URL não foi definido.")

#             return None

#         _engine = create_engine(DB_URL, pool_pre_ping=True, pool_recycle=1800)

def match_subjects(text: str, subjects: Sequence[dict]) -> str:#     return _engine

    if not text or not subjects:

        return ""# def ensure_tables():

    lowered = text.lower()#     """

    hits: set[str] = set()#     Cria a tabela 'proposicoes' se não existir.

    for subject in subjects:#     Colunas espelham o DataFrame consolidado.

        label = str(subject.get("label") or subject.get("value") or "").strip()#     """

        if not label:#     if not USE_DB:

            continue#         return

        value = str(subject.get("value") or "").strip()#     engine = get_engine()

        candidates = {label.lower()}#     if engine is None:

        if value:#         return

            candidates.add(value.lower())#     ddl = """

        if any(candidate and candidate in lowered for candidate in candidates):#     CREATE TABLE IF NOT EXISTS proposicoes (

            hits.add(label)#         CodigoMateria TEXT,

    return ", ".join(sorted(hits))#         Titulo TEXT,

#         Autor TEXT,

#         DataApresentacao TEXT,

def fetch_camara_authors(session: requests.Session, proposition_id: int, timeout: int) -> str:#         Ementa TEXT,

    url = f"{CAMARA_API_BASE}/proposicoes/{proposition_id}/autores"#         SituacaoAtual TEXT,

    try:#         DataUltimaTramitacao TEXT,

        response = session.get(url, timeout=timeout)#         DescricaoUltimaTramitacao TEXT,

        response.raise_for_status()#         LinkFicha TEXT,

        data = response.json().get("dados", [])#         LinkInteiroTeor TEXT,

    except requests.RequestException as exc:#         TermosEncontrados TEXT,

        LOGGER.debug("Could not fetch Câmara authors for %s: %s", proposition_id, exc)#         Local TEXT,

        return ""#         "Prazo para Resposta" TEXT,

    if not data:#         Casa TEXT

        return ""#     );

    primary = next((item for item in data if item.get("ordemAssinatura") == 1), data[0])#     """

    name = primary.get("nome", "")#     with engine.begin() as conn:

    party = primary.get("siglaPartido", "")#         conn.execute(text(ddl))

    uf = primary.get("siglaUf", "")

    metadata = [name.strip()]# def df_to_db(df: pd.DataFrame):

    suffix = " / ".join([value for value in (party, uf) if value])#     """

    if suffix:#     Grava o DF na tabela (estratégia simples: truncate + bulk insert).

        metadata.append(f"({suffix})")#     Se preferir 'upsert', dá para trocar por MERGE/ON CONFLICT.

    return " ".join([part for part in metadata if part])#     """

#     if not USE_DB:

#         return

def fetch_camara_propositions(#     engine = get_engine()

    config: Configuration,#     if engine is None:

    start_date: dt.date,#         return

    end_date: dt.date,#     # Normaliza colunas para garantir o mesmo esquema

    tipos: list[str] | None,#     expected_cols = [

    timeout: int,#         "CodigoMateria","Titulo","Autor","DataApresentacao","Ementa",

) -> list[Proposition]:#         "SituacaoAtual","DataUltimaTramitacao","DescricaoUltimaTramitacao",

    session = requests.Session()#         "LinkFicha","LinkInteiroTeor","TermosEncontrados","Local",

    siglas = tipos or config.proposition_types or ["REQ", "RIC", "INC"]#         "Prazo para Resposta","Casa"

    page = 1#     ]

    results: list[Proposition] = []#     for c in expected_cols:

    LOGGER.info("Consultando Câmara (%s tipos, %s a %s)", len(siglas), start_date, end_date)#         if c not in df.columns:

    while True:#             df[c] = None

        params = {#     df = df[expected_cols].copy()

            "siglaTipo": ",".join(siglas),

            "dataApresentacaoInicio": start_date.isoformat(),#     # TRUNCATE + INSERT (simples e rápido para esse caso)

            "dataApresentacaoFim": end_date.isoformat(),#     try:

            "itens": 100,#         with engine.begin() as conn:

            "pagina": page,#             conn.execute(text("DELETE FROM proposicoes"))

        }#         df.to_sql("proposicoes", engine, if_exists="append", index=False, method="multi", chunksize=1000)

        try:#         logger.info("Dados gravados no banco com sucesso.")

            response = session.get(f"{CAMARA_API_BASE}/proposicoes", params=params, timeout=timeout)#     except SQLAlchemyError as e:

            response.raise_for_status()#         logger.error(f"Erro ao gravar no banco: {e}")

        except requests.RequestException as exc:

            LOGGER.warning("Erro ao consultar proposições da Câmara: %s", exc)# def load_df_from_db() -> pd.DataFrame:

            break#     if not USE_DB:

        payload = response.json().get("dados", [])#         return pd.DataFrame()

        if not payload:#     engine = get_engine()

            break#     if engine is None:

        for item in payload:#         return pd.DataFrame()

            uri = item.get("uri")#     try:

            if not uri:#         with engine.begin() as conn:

                continue#             df = pd.read_sql(text("SELECT * FROM proposicoes"), conn)

            try:#         logger.info("Dados carregados do banco com sucesso.")

                detail = session.get(uri, timeout=timeout).json().get("dados", {})#         return df

            except requests.RequestException as exc:#     except SQLAlchemyError as e:

                LOGGER.debug("Falha ao obter detalhes da proposição %s: %s", item.get("id"), exc)#         logger.error(f"Erro ao carregar do banco: {e}")

                continue#         return pd.DataFrame()

            ementa = detail.get("ementaDetalhada") or detail.get("ementa") or ""

            ultimo_status = detail.get("ultimoStatus", {})# # ==============================================================================

            local_orgao = ultimo_status.get("orgao", {})# # FUNÇÕES AUXILIARES – SALVAR/CARREGAR XLSX

            termos, grupos = match_unit_terms(ementa, config.unit_groups)# # ==============================================================================

            subjects = match_subjects(ementa, config.subjects)# def _forcar_https(url: str | None) -> str:

            titulo = f"{detail.get('siglaTipo', '')} {detail.get('numero', '')}/{detail.get('ano', '')}".strip()#     if not url:

            autor = fetch_camara_authors(session, detail.get("id"), timeout)#         return ""

            ficha = detail.get("urlProposicao") or (#     if url.startswith("http://www.camara.leg.br") or url.startswith("http://www25.senado.leg.br"):

                f"https://www.camara.leg.br/proposicoesWeb/fichadetramitacao?idProposicao={detail.get('id')}"#         return url.replace("http://", "https://", 1)

                if detail.get("id")#     return url

                else ""

            )# def salvar_df(df: pd.DataFrame):

            results.append(#     # 1) Banco (se habilitado)

                Proposition(#     if USE_DB:

                    titulo=titulo or item.get("titulo", ""),#         ensure_tables()

                    autor=autor,#         df_to_db(df)

                    ementa=ementa,

                    situacao=ultimo_status.get("descricaoSituacao", ""),#     # 2) XLSX (mantido para compatibilidade)

                    data_apresentacao=format_display_date(detail.get("dataApresentacao")),#     try:

                    data_ultima_tramitacao=format_display_date(ultimo_status.get("dataHora")),#         if LOCAL_MODE:

                    link_ficha=ficha,#             df.to_excel(LOCAL_OUTPUT_FILE, index=False)

                    link_inteiro_teor=detail.get("urlInteiroTeor", ""),#             logger.info(f"Dados salvos localmente em {LOCAL_OUTPUT_FILE}")

                    termos_encontrados=termos,#         else:

                    grupos_encontrados=grupos,#             from io import BytesIO

                    assuntos_encontrados=subjects,#             output = BytesIO()

                    local=local_orgao.get("sigla") or local_orgao.get("nomePublicacao") or "",#             df.to_excel(output, index=False, engine='openpyxl')

                    casa="Câmara",#             output.seek(0)

                )#             try:

            )#                 client = storage.Client()

        if len(payload) < 100:#                 bucket = client.bucket(BUCKET_NAME)

            break#                 blob = bucket.blob(GCS_OBJECT_NAME)

        page += 1#                 blob.upload_from_file(

    LOGGER.info("Câmara: %s registros coletados", len(results))#                     output,

    return results#                     content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'

#                 )

#                 logger.info(f"Arquivo XLSX enviado ao GCS: gs://{BUCKET_NAME}/{GCS_OBJECT_NAME}")

def _flatten_processos(payload: object) -> list[dict]:#             except Exception as e:

    if isinstance(payload, list):#                 logger.error(f"Erro ao salvar DataFrame no GCS: {e}")

        rows: list[dict] = []#     except Exception as e:

        for item in payload:#         logger.error(f"Erro ao salvar XLSX: {e}")

            rows.extend(_flatten_processos(item))

        return rows# def carregar_df() -> pd.DataFrame:

    if isinstance(payload, dict):#     # Lógica exclusiva para o banco de dados

        if "processos" in payload and isinstance(payload["processos"], list):#     if USE_DB:

            return _flatten_processos(payload["processos"])#         # Se USE_DB for verdadeiro, SÓ tentamos o banco. Não há fallback.

        if "processo" in payload:#         return load_df_from_db()

            return _flatten_processos(payload["processo"])

        return [payload]#     # O código abaixo só executa se USE_DB for falso

    return []#     logger.info("USE_DB=false, carregando de arquivo XLSX.")

#     try:

#         if LOCAL_MODE:

def fetch_senado_propositions(#             if not os.path.exists(LOCAL_OUTPUT_FILE):

    config: Configuration,#                 logger.warning(f"Arquivo {LOCAL_OUTPUT_FILE} não encontrado.")

    siglas: list[str] | None,#                 return pd.DataFrame()

    timeout: int,#             df = pd.read_excel(LOCAL_OUTPUT_FILE, engine='openpyxl')

) -> list[Proposition]:#             logger.info("Arquivo carregado localmente com sucesso.")

    session = requests.Session()#             return df

    targets = siglas or ["req", "rqs"]#         else:

    results: list[Proposition] = []#             # Lógica GCS

    LOGGER.info("Consultando Senado (%s siglas)", len(targets))#             client = storage.Client()

    for sigla in targets:#             bucket = client.bucket(BUCKET_NAME)

        try:#             blob = bucket.blob(GCS_OBJECT_NAME)

            response = session.get(f"{SENADO_API_BASE}/processo", params={"sigla": sigla}, timeout=timeout)#             if not blob.exists():

            response.raise_for_status()#                 logger.warning(f"Objeto gs://{BUCKET_NAME}/{GCS_OBJECT_NAME} não existe.")

        except requests.RequestException as exc:#                 return pd.DataFrame()

            LOGGER.warning("Erro ao consultar Senado (%s): %s", sigla, exc)#             from io import BytesIO

            continue#             data = BytesIO()

        try:#             blob.download_to_file(data)

            payload = response.json()#             data.seek(0)

        except ValueError as exc:#             df = pd.read_excel(data, engine='openpyxl')

            LOGGER.warning("Resposta do Senado não é JSON válido (%s): %s", sigla, exc)#             logger.info("Carregado XLSX do GCS com sucesso.")

            continue#             return df

        for item in _flatten_processos(payload):#     except Exception as e:

            ementa = str(item.get("ementa") or item.get("Ementa") or "")#         logger.error(f"Erro ao carregar o arquivo XLSX: {e}")

            termos, grupos = match_unit_terms(ementa, config.unit_groups)#         return pd.DataFrame()

            subjects = match_subjects(ementa, config.subjects)    

            numero = item.get("identificacao") or item.get("nome") or item.get("sigla") or ""# def pegar_data_ultima_atualizacao() -> str:

            ano = item.get("ano") or ""#     try:

            titulo = f"{numero} {str(ano).strip()}".strip()#         # Se estiver usando o banco, a "última atualização" é agora.

            data_apresentacao = item.get("dataApresentacao") or item.get("dataInicio")#         if USE_DB:

            data_ultima = item.get("dataUltimaAtualizacao") or item.get("dataAtualizacao")#             sp_tz = pytz.timezone("America/Sao_Paulo")

            if isinstance(data_apresentacao, dict):#             dt_sp = dt.now(sp_tz)

                data_apresentacao = data_apresentacao.get("data")#             return dt_sp.strftime("Dados do Banco em %d/%m/%Y às %H:%M")

            if isinstance(data_ultima, dict):

                data_ultima = data_ultima.get("data")#         # O código abaixo só executa se USE_DB for falso

            link_codigo = item.get("codigoMateria") or item.get("codigo") or item.get("id")#         if LOCAL_MODE:

            ficha = (#             if not os.path.exists(LOCAL_OUTPUT_FILE):

                f"https://www25.senado.leg.br/web/atividade/materias/-/materia/{link_codigo}"#                 return "Nenhum arquivo local gerado ainda."

                if link_codigo#             timestamp = os.path.getmtime(LOCAL_OUTPUT_FILE)

                else ""#             dt_obj = dt.fromtimestamp(timestamp)

            )#         else:

            results.append(#             # Lógica GCS

                Proposition(#             client = storage.Client()

                    titulo=titulo,#             bucket = client.bucket(BUCKET_NAME)

                    autor=str(item.get("autoria") or item.get("autor") or ""),#             blob = bucket.blob(GCS_OBJECT_NAME)

                    ementa=ementa,#             if not blob.exists():

                    situacao=str(item.get("situacao") or item.get("descricaoSituacao") or ""),#                 return "Nenhum arquivo no GCS gerado ainda."

                    data_apresentacao=format_display_date(str(data_apresentacao) if data_apresentacao else ""),#             blob.reload()

                    data_ultima_tramitacao=format_display_date(str(data_ultima) if data_ultima else ""),#             if not blob.updated:

                    link_ficha=ficha,#                 return "Arquivo sem data de atualização."

                    link_inteiro_teor=str(item.get("urlDocumento") or item.get("linkInteiroTeor") or ""),#             dt_obj = blob.updated

                    termos_encontrados=termos,            

                    grupos_encontrados=grupos,#         sp_tz = pytz.timezone("America/Sao_Paulo")

                    assuntos_encontrados=subjects,#         dt_sp = dt_obj.astimezone(sp_tz)

                    local=str(item.get("siglaEnteIdentificador") or item.get("local") or ""),#         return dt_sp.strftime("Arquivo atualizado em %d/%m/%Y às %H:%M")

                    casa="Senado",#     except Exception as e:

                )#         logger.error(f"Erro ao obter data de atualização: {e}")

            )#         return "Falha ao obter data de atualização."

    LOGGER.info("Senado: %s registros coletados", len(results))    

    return results# # ==============================================================================

# # FUNÇÕES AUXILIARES GERAIS (parse, safe_request, ordenar, ...)

# # ==============================================================================

def load_propositions_from_sqlite(db_path: Path, limit: int | None = None) -> list[Proposition]:# def parse_data(strdata):

    if not db_path.exists():#     formatos = [

        return []#         "%Y-%m-%dT%H:%M:%S",

    try:#         "%Y-%m-%dT%H:%M",

        conn = sqlite3.connect(db_path)#         "%Y-%m-%d %H:%M:%S",

    except sqlite3.Error:#         "%Y-%m-%d %H:%M",

        return []#         "%Y-%m-%d",

    conn.row_factory = sqlite3.Row#         "%d/%m/%Y %H:%M:%S",

    try:#         "%d/%m/%Y"

        query = "SELECT * FROM proposicoes ORDER BY datetime(DataUltimaTramitacao) DESC"

        if limit:#     for fmt in formatos:

            query += f" LIMIT {int(limit)}"#         try:

        rows = conn.execute(query).fetchall()#             return dt.strptime(strdata, fmt)

    except sqlite3.Error:#         except:

        conn.close()#             pass

        return []#     return None

    conn.close()

    props: list[Proposition] = []# def contem_termos(texto, termos):

    for row in rows:#     if not texto:

        props.append(#         return False

            Proposition(#     texto_lower = texto.lower()

                titulo=row.get("Titulo", ""),#     return any(termo.lower() in texto_lower for termo in termos)

                autor=row.get("Autor", ""),

                ementa=row.get("Ementa", ""),# def safe_request(

                situacao=row.get("SituacaoAtual", ""),#     url, *, params=None, timeout=60, max_tentativas=3,

                data_apresentacao=row.get("DataApresentacao", ""),#     stream=False, headers=None, **kwargs

                data_ultima_tramitacao=row.get("DataUltimaTramitacao", ""),# ):

                link_ficha=row.get("LinkFicha", ""),#     default_headers = {

                link_inteiro_teor=row.get("LinkInteiroTeor", ""),#         "User-Agent": (

                termos_encontrados=row.get("TermosEncontrados", ""),#             "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "

                grupos_encontrados=row.get("GruposEncontrados", ""),#             "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"

                assuntos_encontrados=row.get("AssuntosEncontrados", ""),#         ),

                local=row.get("Local", ""),#         "Accept": "*/*",

                casa=row.get("Casa", ""),#         "Accept-Encoding": "identity",

            )#     }

        )#     sess = requests.Session()

#     retry_cfg = Retry(

def _sort_key(proposition: Proposition) -> tuple:#         connect=max_tentativas,

    def to_key(value: str) -> dt.datetime:#         read=max_tentativas,

        parsed = parse_iso_datetime(value)#         total=max_tentativas,

        if parsed:#         backoff_factor=1.5,

            return parsed#         status_forcelist=[500, 502, 503, 504],

        try:#         allowed_methods=["GET", "HEAD"],

            return dt.datetime.strptime(value, "%d/%m/%Y %H:%M").replace(tzinfo=dt.timezone.utc)#         raise_on_status=False,

        except Exception:  # pragma: no cover - defensive#     )

            try:#     sess.mount("https://", HTTPAdapter(max_retries=retry_cfg))

                return dt.datetime.strptime(value, "%d/%m/%Y").replace(tzinfo=dt.timezone.utc)#     sess.mount("http://",  HTTPAdapter(max_retries=retry_cfg))

            except Exception:

                return dt.datetime.min.replace(tzinfo=dt.timezone.utc)#     for tent in range(max_tentativas):

#         try:

    return (to_key(proposition.data_ultima_tramitacao), to_key(proposition.data_apresentacao))#             # --- CORREÇÃO APLICADA AQUI ---

#             # Passamos os parâmetros corretamente para a chamada 'get'

#             r = sess.get(

def render_html(propositions: list[Proposition], config: Configuration, output_path: Path) -> None:#                 url,

    generated_at = dt.datetime.now().astimezone()#                 params=params,

    rows_html: list[str] = []#                 timeout=timeout,

    for prop in propositions:#                 stream=stream,

        title_text = html.escape(prop.titulo or "(sem título)")#                 headers=default_headers,

        title_cell = (#                 **kwargs

            f"<a href='{html.escape(prop.link_inteiro_teor)}' target='_blank' rel='noopener'>{title_text}</a>"#             )

            if prop.link_inteiro_teor#             # --------------------------------

            else title_text

        )#             if not stream:

        ficha_cell = (#                 try:

            f"<a href='{html.escape(prop.link_ficha)}' target='_blank' rel='noopener'>Ficha</a>"#                     _ = r.content

            if prop.link_ficha#                 except (http.client.IncompleteRead, ChunkedEncodingError) as e:

            else ""#                     raise e

        )            

        rows_html.append(#             # Checa se o status code indica sucesso antes de retornar

            """

            <tr>

                <td>{titulo}</td>            

                <td>{autor}</td>

                <td>{ementa}</td>

                <td>{situacao}</td>

                <td>{data_ap}</td>

                <td>{data_tram}</td>

                <td>{local}</td>

                <td>{casa}</td>

                <td>{termos}</td>

                <td>{grupos}</td>            

                <td>{assuntos}</td>

                <td>{ficha}</td>

            </tr>

            """
            .format(# def ordenar_por_ultima_tramitacao(df: pd.DataFrame) -> pd.DataFrame:

                titulo=title_cell,#     if 'DataUltimaTramitacao' in df.columns:

                autor=html.escape(prop.autor or ""),#         df['DataUltimaTramitacao_dt'] = pd.to_datetime(

                ementa=html.escape(prop.ementa or ""),#             df['DataUltimaTramitacao'], dayfirst=True, errors='coerce'

                situacao=html.escape(prop.situacao or ""),#         )

                data_ap=html.escape(prop.data_apresentacao or ""),#         df.sort_values(by='DataUltimaTramitacao_dt', ascending=False, inplace=True)

                data_tram=html.escape(prop.data_ultima_tramitacao or ""),#         df.drop(columns=['DataUltimaTramitacao_dt'], inplace=True)

                local=html.escape(prop.local or ""),#     return df

                casa=html.escape(prop.casa or ""),

                termos=html.escape(prop.termos_encontrados or ""),# # =====================================================================

                grupos=html.escape(prop.grupos_encontrados or ""),# # === BUSCA TODOS OS TERMOS EM TODAS AS PÁGINAS DO PDF ================

                assuntos=html.escape(prop.assuntos_encontrados or ""),# # =====================================================================

                ficha=ficha_cell,# def pdf_tem_termos(url_pdf: str,

            )#                    termos: list[str] = TERMOS) -> list[str]:

        )#     """

#     Baixa o PDF (url_pdf) e devolve a lista de TERMOS encontrados

    summary_parts: list[str] = []

    if config.proposition_types:#     """

        summary_parts.append(#     if not url_pdf:

            "<li><strong>Tipos monitorados:</strong> {items}</li>".format( 

                items=", ".join(html.escape(sigla) for sigla in config.proposition_types)

            ) #     resp = safe_request(url_pdf, timeout=120, stream=True)

        )#     if not (resp and resp.status_code == 200 and resp.content):

    if config.presentation_years:#         return []

        summary_parts.append(

            "<li><strong>Anos monitorados:</strong> {items}</li>".format(#     try:

                items=", ".join(str(year) for year in config.presentation_years)#         pdf = PdfReader(io.BytesIO(resp.content))

            )#     except Exception as e:

        )#         logger.error(f"Erro ao abrir PDF {url_pdf}: {e}")

    if config.unit_groups:#         return []

        summary_parts.append(

            "<li><strong>Grupos:</strong> {items}</li>".format(#     termos_lower = [t.lower() for t in termos]

                items=", ".join(#     encontrados: set[str] = set()

                    html.escape(str(group.get("label") or group.get("value") or ""))

                    for group in config.unit_groups#     for page in pdf.pages:

                )#         try:

            )#             texto = (page.extract_text() or "").lower()

        )#         except Exception:

    if config.subjects:#             texto = ""

        summary_parts.append(

            "<li><strong>Assuntos:</strong> {items}</li>".format(#         for termo, termo_l in zip(termos, termos_lower):

                items=", ".join(#             if termo_l in texto:

                    html.escape(str(subject.get("label") or subject.get("value") or ""))#                 encontrados.add(termo)

                    for subject in config.subjects

                )#     return list(encontrados)

            )

        )# # ==============================================================================

# # FUNÇÕES DE COLETA DE DADOS – CÂMARA

    config_block = "".join(summary_parts)# # ==============================================================================

    updated_label = (# def obter_local_ultima_tramitacao(tramitacao):

        config.updated_at.astimezone().strftime("%d/%m/%Y %H:%M")#     sigla = tramitacao.get("siglaOrgao", "")

        if config.updated_at#     uri_orgao = tramitacao.get("uriOrgao", "")

        else "não informado"#     nome_pub = ""

    )#     if uri_orgao:

#         r = safe_request(uri_orgao, timeout=30)

    html_document = """
    
    <!DOCTYPE html>

    <html lang="pt-BR">
    <head>#     if sigla and nome_pub:

        <meta charset="utf-8">

        <meta name="viewport" content="width=device-width, initial-scale=1">

        <title>Requerimentos de Interesse</title>

        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" integrity="sha384-QWTKZyjpPEjISv5WaRU9OFeRpok6YctnYmDr5pNlyT2bRjXh0JMhjY6hW+ALEwIH" crossorigin="anonymous">

        <style>

            body {{ padding: 2rem; background-color: #f8f9fa; }}

            .table thead th {{ white-space: nowrap; }}

            .table tbody td {{ vertical-align: top; font-size: 0.92rem; }}

            .config-summary {{ font-size: 0.9rem; color: #555; }}

        </style>
    </head>

    <body>

        <div class="container-fluid">

            <div class="row mb-4">

                <div class="col">

                    <h1 class="h3">Requerimentos de Interesse</h1>

                    <p class="text-muted mb-1">Página gerada em {generated}</p>

                    <p class="text-muted mb-1">Configuração atualizada em {config_updated}</p>

                    {config_summary}

                </div>

            </div>

            <div class="row">

                <div class="col">

                    <div class="table-responsive">

                        <table class="table table-striped table-hover table-sm">

                            <thead class="table-light">

                                <tr>

                                    <th>Proposição</th>

                                    <th>Autor</th>

                                    <th>Ementa</th>

                                    <th>Situação</th>

                                    <th>Data Apresentação</th>

                                    <th>Última Tramitação</th>

                                    <th>Local</th>

                                    <th>Casa</th>

                                    <th>Termos</th>

                                    <th>Grupos</th>

                                    <th>Assuntos</th>

                                    <th>Ficha</th>

                                </tr>

                            </thead>

                            <tbody>

                                {rows}

                            </tbody>

                        </table>
                    </div>

                </div>

            </div>

        </div>

    </body>

    </html>

    """.format(
        generated=generated_at.strftime("%d/%m/%Y %H:%M"),
        config_updated=updated_label,
        config_summary=f"<ul class='config-summary'>{config_block}</ul>" if config_block else "",
        rows="\n".join(rows_html),
    )


    output_path.parent.mkdir(parents=True, exist_ok=True)#                         ultimo_status = deputado_dados.get("ultimoStatus", {})

    output_path.write_text(html_document, encoding="utf-8")#                         partido = (ultimo_status.get("siglaPartido") or "Sem Partido").strip()

    LOGGER.info("Arquivo HTML gerado em %s", output_path)#                         uf = (ultimo_status.get("siglaUf") or "Sem UF").strip()

#                         logger.info(f"[DEBUG] Dados do deputado obtidos: Partido={partido}, UF={uf}")

#                 autor_str = f"{nome} ({partido}/{uf})"


def deduplicate(propositions: Iterable[Proposition]) -> list[Proposition]:#                 logger.info(f"[DEBUG] Autor (ordem=1) formatado: {autor_str}")

    catalog: dict[tuple[str, str, str], Proposition] = {}#                 return autor_str

    for prop in propositions:#             else:

        key = (prop.titulo, prop.casa, prop.link_inteiro_teor or prop.link_ficha)#                 logger.warning("[AVISO] Nenhum autor encontrado na lista.")

        if key not in catalog:#         else:

            catalog[key] = prop#             logger.error(f"[ERRO] Falha ao obter autores da proposição ID {codigo_proposicao}. Status: {response.status_code if response else 'N/A'}")

            continue#     except Exception as e:

        existing = catalog[key]#         logger.error(f"[ERRO] Exceção ao obter autores da proposição ID {codigo_proposicao}: {e}")

        if not existing.termos_encontrados and prop.termos_encontrados:
            catalog[key] = prop
    return list(catalog.values())# def obter_prazo_resposta_cam(det_id: int) -> str:

def filter_propositions(propositions: list[Proposition], config: Configuration) -> list[Proposition]:
    """Filtra proposições com base nos grupos de unidades e assuntos configurados."""
    if not propositions:
        return []

    filtered: list[Proposition] = []
    for prop in propositions:
        # Se grupos de unidades estão configurados, pelo menos um deve ter sido encontrado.
        if config.unit_groups and not prop.grupos_encontrados:
            continue

        # Se assuntos estão configurados, pelo menos um deve ter sido encontrado.
        if config.subjects and not prop.assuntos_encontrados:
            continue
        filtered.append(prop)

    return filtered

def parse_args() -> argparse.Namespace:#     if not (r and r.status_code==200):

    parser = argparse.ArgumentParser(description="Gerar página estática de requerimentos")#         return ""
    parser.add_argument("--api", action="store_true", help="Buscar dados nas APIs do Congresso")#     tram = r.json().get("dados", [])
    parser.add_argument("--from-sqlite", action="store_true", help="Carregar dados de busca preexistentes no SQLite")#     tram.sort(
    parser.add_argument("--start", type=str, help="Data inicial (YYYY-MM-DD)")#         key=lambda t: parse_data(t.get("dataHora","")) or dt.min,
    parser.add_argument("--end", type=str, help="Data final (YYYY-MM-DD)")#         reverse=True
    parser.add_argument("--tipos", nargs="*", help="Sobrescrever tipos de proposição da Câmara")#     )
    parser.add_argument("--siglas", nargs="*", help="Sobrescrever siglas utilizadas na coleta do Senado")#     for t in tram:
    parser.add_argument("--timeout", type=int, default=REQUEST_TIMEOUT, help="Timeout em segundos para chamadas HTTP")#         texto = t.get("despacho") or t.get("descricaoTramitacao","")
    parser.add_argument("--limit", type=int, help="Limitar quantidade ao carregar do SQLite")#         if "prazo para resposta" in texto.lower():
    parser.add_argument("--db", type=str, default=str(DEFAULT_DB_PATH), help="Caminho do banco SQLite a utilizar")#             m = re.search(r"\(de\s*([^\)]+)\)", texto, flags=re.I)
    parser.add_argument("--output", type=str, default=str(DEFAULT_OUTPUT), help="Arquivo HTML de saída")#             if m:
    parser.add_argument("--dump-json", type=str, help="Opcional: salvar dados consolidados em JSON")#                 return m.group(1).strip()
    parser.add_argument("--skip-senado", action="store_true", help="Não consultar dados do Senado")#     return ""
    parser.add_argument("--skip-camara", action="store_true", help="Não consultar dados da Câmara")
    parser.add_argument("--verbose", action="store_true", help="Habilitar logs detalhados")# def _baixar_processar_camara(uri_prop: str, termos=TERMOS):
      
    return parser.parse_args()#     det_r = safe_request(uri_prop, timeout=30)


def main() -> None:
    args = parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="[%(asctime)s] %(levelname)s %(message)s",
    )

    db_path = Path(args.db)
    config = load_configuration(db_path)

    # Determine date range based on config, then CLI args, then default
    if config.presentation_years:
        start = dt.date(min(config.presentation_years), 1, 1)
        end = dt.date(max(config.presentation_years), 12, 31)
    else:
        start = dt.date.today() - dt.timedelta(days=90)
        end = dt.date.today()

    if args.start:
        start = dt.date.fromisoformat(args.start)
    if args.end:
        end = dt.date.fromisoformat(args.end)

    if start > end:
        start, end = end, start

    LOGGER.info("Tipos configurados: %s", ", ".join(config.proposition_types) or "nenhum")


    dataset: list[Proposition] = []

    if args.api:
        if not args.skip_camara:
            dataset.extend(fetch_camara_propositions(config, start, end, args.tipos, args.timeout))
        if not args.skip_senado:
            dataset.extend(fetch_senado_propositions(config, args.siglas, args.timeout))
    if args.from_sqlite:
        dataset.extend(load_propositions_from_sqlite(db_path, args.limit))

    if not dataset:
        raise SystemExit("Nenhum dado foi carregado. Utilize --api e/ou --from-sqlite.")
    
    # Filtra as proposições com base na configuração antes de deduplicar
    filtered_propositions = filter_propositions(dataset, config)
    LOGGER.info("%s proposições retidas após filtro", len(filtered_propositions))
    
    unique = deduplicate(filtered_propositions)
    unique.sort(key=_sort_key, reverse=True)
    
    output_path = Path(args.output)
    
    render_html(unique, config, output_path)   

    if args.dump_json:
        payload = [prop.__dict__ for prop in unique]
        Path(args.dump_json).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        LOGGER.info("JSON auxiliar salvo em %s", args.dump_json)
