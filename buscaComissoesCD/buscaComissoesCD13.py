# #!/usr/bin/env python
# # -*- coding: utf-8 -*-
# """
# busca-comissoes-cd – HCS/OBS
# Dash + Pipeline de Coleta/Atualização automáticos (Câmara dos Deputados)

# • Nome canônico do CSV: proposicoes_filtradas_cd.csv
# • Layout ORIGINAL restaurado (filtros Tipo / Órgão / Situação, tabela idêntica).
# • Armazenamento: Huawei Cloud OBS (Object Storage Service).
# """

# # ────────────────────────────────────────────────────────────────────────────
# # IMPORTS
# # ────────────────────────────────────────────────────────────────────────────
# import os, io, time, logging
# from datetime import datetime as dt
# from typing import Optional, Tuple
# from concurrent.futures import ThreadPoolExecutor, as_completed

# import pandas as pd
# import requests
# from requests.adapters import HTTPAdapter
# from urllib3.util.retry import Retry
# from requests.exceptions import ChunkedEncodingError

# from flask import Flask
# from apscheduler.schedulers.background import BackgroundScheduler

# import dash
# import dash_bootstrap_components as dbc
# from dash import html, dcc, dash_table, Input, Output, State
# from zoneinfo import ZoneInfo

# import os, io, time, logging, threading  # <-- ADICIONE AQUI
# from datetime import datetime as dt
# from typing import Optional, Tuple
# from concurrent.futures import ThreadPoolExecutor, as_completed

# # Huawei OBS SDK
# # pip install esdk-obs-python
# try:
#     from obs import ObsClient
# except Exception as _e:
#     ObsClient = None  # avisamos no log ao inicializar

# # ────────────────────────────────────────────────────────────────────────────
# # CONFIGURAÇÕES GERAIS
# # ────────────────────────────────────────────────────────────────────────────
# def _truthy(env_value: Optional[str], default: bool = False) -> bool:
#     if env_value is None:
#         return default
#     return str(env_value).strip().lower() in {"1", "true", "yes", "y", "on"}

# BASE_DIR        = os.getenv("BASE_DIR", "data").rstrip("/")
# os.makedirs(BASE_DIR, exist_ok=True)

# LOCAL_MODE      = _truthy(os.getenv("LOCAL_MODE"), True)  # True em desenvolvimento

# # OBS (Huawei Cloud)
# OBS_BUCKET      = os.getenv("HCS_OBS_BUCKET", "aspar")
# OBS_ENDPOINT    = os.getenv("HCS_OBS_ENDPOINT", "https://obs.la-south-6001.hcso.dataprev.gov.br")
# OBS_AK          = os.getenv("HCS_OBS_AK", "")
# OBS_SK          = os.getenv("HCS_OBS_SK", "")
# OBS_TOKEN       = os.getenv("HCS_OBS_TOKEN")  # opcional (STS)

# # Objeto/caminho no bucket
# OBS_OBJECT_KEY  = "proposicoes_filtradas_cd.csv"

# # Caminho local canonical (mantemos mesmo nome do arquivo)
# LOCAL_CSV_PATH  = os.path.join(BASE_DIR, "proposicoes_filtradas_cd.csv")

# # App
# PORT            = int(os.getenv("PORT", "8080"))

# # Coleta
# MAX_WORKERS     = 12
# SITUACOES_FILTER = ['Pronta para Pauta', 'Aguardando Vistas']
# ORGAO_SIGLAS     = ['PLEN', 'CCJC', 'CFT']
# TIPOS_PROP       = ['PL', 'MPV', 'PDL', 'PLP', 'PEC', 'PLN', 'PLS', 'PLC', 'PDS', 'PDN']
# ANOS_INICIO, ANOS_FIM = 2001, dt.now().year

# # ────────────────────────────────────────────────────────────────────────────
# # LOGGING
# # ────────────────────────────────────────────────────────────────────────────
# logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s - %(message)s")
# logger = logging.getLogger("busca-comissoes-cd")

# # timestamp global do CSV para o rodapé
# LAST_CSV_TS: Optional[dt] = None

# # ────────────────────────────────────────────────────────────────────────────
# # FLASK SERVER (Dash usa)
# # ────────────────────────────────────────────────────────────────────────────
# server = Flask(__name__)

# # ────────────────────────────────────────────────────────────────────────────
# # HELPERS – REDE
# # ────────────────────────────────────────────────────────────────────────────
# def safe_request(url: str, *, timeout=60, max_tries=3, stream=False, **kw):
#     headers = kw.pop("headers", {}) or {}
#     headers.setdefault("User-Agent",
#         "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
#         "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125 Safari/537.36")
#     sess = requests.Session()
#     sess.mount("https://", HTTPAdapter(max_retries=Retry(
#         total=max_tries, backoff_factor=1.5,
#         status_forcelist=[500, 502, 503, 504],
#         allowed_methods=frozenset(["GET"])
#     )))
#     for tent in range(1, max_tries + 1):
#         try:
#             r = sess.get(url, timeout=timeout, headers=headers, stream=stream, **kw)
#             _ = r.content if not stream else None
#             return r
#         except (ChunkedEncodingError, requests.exceptions.ChunkedEncodingError):
#             logger.warning("safe_request corpo incompleto %s (%d/%d)", url, tent, max_tries)
#             time.sleep(1.5 * tent)
#         except Exception as e:
#             logger.warning("safe_request falhou %s – %s", url, e)
#             time.sleep(1.5 * tent)
#     logger.error("safe_request esgotou tentativas %s", url)
#     return None

# # ────────────────────────────────────────────────────────────────────────────
# # HELPERS – OBS STORAGE
# # ────────────────────────────────────────────────────────────────────────────
# _obs_client: Optional[ObsClient] = None

# def get_obs_client() -> ObsClient:
#     """Inicializa o cliente OBS (uma vez)."""
#     global _obs_client
#     if _obs_client is not None:
#         return _obs_client
#     if ObsClient is None:
#         raise RuntimeError("Pacote 'esdk-obs-python' não instalado.")
#     if not OBS_ENDPOINT.startswith("http"):
#         # ObsClient aceita sem 'https://' também, mas deixamos claro
#         server = f"https://{OBS_ENDPOINT}"
#     else:
#         server = OBS_ENDPOINT
#     _obs_client = ObsClient(
#         access_key_id=OBS_AK or None,
#         secret_access_key=OBS_SK or None,
#         server=server,
#         security_token=OBS_TOKEN or None,
#     )
#     return _obs_client

# def obs_upload_bytes(bucket: str, key: str, data: bytes, content_type: str = "text/csv"):
#     client = get_obs_client()
#     resp = client.putContent(bucket, key, content=data, metadata={"Content-Type": content_type})
#     if resp.status < 200 or resp.status >= 300:
#         raise RuntimeError(f"OBS upload falhou: status={resp.status}, reason={getattr(resp, 'reason', '')}")

# def obs_get_bytes(bucket: str, key: str) -> tuple[Optional[bytes], Optional[dt]]:
#     client = get_obs_client()
#     try:
#         meta = client.getObjectMetadata(bucket, key)
#     except Exception as e:
#         logger.error("OBS metadata exception: %s", e)
#         return None, None

#     if meta.status == 404:
#         return None, None
#     if meta.status == 403:
#         logger.error("OBS metadata 403 (acesso negado). Verifique: AK/SK, agency/role no projeto, "
#                      "endpoint da região do bucket e horário do nó (NTP).")
#         return None, None
#     if meta.status < 200 or meta.status >= 300:
#         logger.error("OBS metadata falhou: status=%s reason=%s", meta.status, getattr(meta, 'reason', ''))
#         return None, None

#     last_modified = None
#     try:
#         lm = getattr(meta.body, "lastModified", None)
#         if lm:
#             last_modified = dt.strptime(lm, "%a, %d %b %Y %H:%M:%S %Z")
#     except Exception:
#         pass

#     obj = client.getObject(bucket, key, loadStreamInMemory=True)
#     if obj.status == 404:
#         return None, last_modified
#     if obj.status == 403:
#         logger.error("OBS getObject 403 (acesso negado).")
#         return None, last_modified
#     if obj.status < 200 or obj.status >= 300:
#         logger.error("OBS getObject falhou: status=%s", obj.status)
#         return None, last_modified

#     content = getattr(obj.body, "buffer", None)
#     return content, last_modified

# def salvar_csv(df: pd.DataFrame):
#     global LAST_CSV_TS
#     csv_bytes = df.to_csv(sep=";", index=False, encoding="utf-8").encode("utf-8")

#     if LOCAL_MODE:
#         with open(LOCAL_CSV_PATH, "wb") as f:
#             f.write(csv_bytes)
#         LAST_CSV_TS = dt.fromtimestamp(os.path.getmtime(LOCAL_CSV_PATH), tz=ZoneInfo("UTC"))
#         logger.info("CSV salvo localmente em %s", LOCAL_CSV_PATH)
#         return

#     obs_upload_bytes(OBS_BUCKET, OBS_OBJECT_KEY, csv_bytes, content_type="text/csv")
#     # Após upload, buscamos metadata para registrar LAST_CSV_TS
#     _, lm = obs_get_bytes(OBS_BUCKET, OBS_OBJECT_KEY)
#     LAST_CSV_TS = lm or dt.now(tz=ZoneInfo("UTC"))
#     logger.info("CSV enviado a obs://%s/%s", OBS_BUCKET, OBS_OBJECT_KEY)

# def carregar_csv() -> pd.DataFrame:
#     global LAST_CSV_TS
#     try:
#         if LOCAL_MODE:
#             if not os.path.exists(LOCAL_CSV_PATH):
#                 return pd.DataFrame()
#             df = pd.read_csv(LOCAL_CSV_PATH, sep=";", engine="python", dtype=str)
#             LAST_CSV_TS = dt.fromtimestamp(os.path.getmtime(LOCAL_CSV_PATH), tz=ZoneInfo("UTC"))
#             return df

#         content, last_modified = obs_get_bytes(OBS_BUCKET, OBS_OBJECT_KEY)
#         if not content:
#             # sem acesso ou ainda não existe: devolve vazio, a rotina de atualização fará upload
#             return pd.DataFrame()
#         df = pd.read_csv(io.BytesIO(content), sep=";", engine="python", dtype=str)
#         LAST_CSV_TS = (last_modified or dt.now(tz=ZoneInfo("UTC")))
#         if "Proposição" not in df.columns and {"siglaTipo","numero","ano"}.issubset(df.columns):
#             df["Proposição"] = df["siglaTipo"] + " " + df["numero"] + "/" + df["ano"]
#         return df
#     except Exception as e:
#         logger.error("Erro carregar CSV: %s", e)
#         return pd.DataFrame()

# def str_data_ultima_atualizacao() -> str:
#     if LAST_CSV_TS:
#         ts_local = LAST_CSV_TS.astimezone(ZoneInfo("America/Sao_Paulo"))
#         return ts_local.strftime("%d/%m/%Y às %H:%M")
#     return "Nenhum arquivo gerado ainda."

# # ────────────────────────────────────────────────────────────────────────────
# # COLETA – Câmara
# # ────────────────────────────────────────────────────────────────────────────
# def obter_partido_uf_deputado(uri: str) -> tuple[str, str]:
#     # curto-circuito se não houver URL válida
#     if not uri or not isinstance(uri, str) or not uri.startswith("http"):
#         return "", ""
#     max_tries = 3
#     for tent in range(1, max_tries + 1):
#         try:
#             r = safe_request(uri, timeout=20)
#             if not (r and r.status_code == 200):
#                 logger.warning("obter_partido tentativa %d – status inválido (%s)",
#                                tent, getattr(r, "status_code", None))
#                 time.sleep(2)
#                 continue
#             dados = r.json().get("dados", {})
#             ultimo = dados.get("ultimoStatus")
#             if not ultimo:
#                 return "", ""
#             return (ultimo.get("siglaPartido", "") or "", ultimo.get("siglaUf", "") or "")
#         except Exception as e:
#             logger.warning("obter_partido tentativa %d – erro: %s", tent, e)
#             time.sleep(2)
#     return "", ""

# def fetch_autor(prop_id: str) -> str:
#     url = f"https://dadosabertos.camara.leg.br/api/v2/proposicoes/{prop_id}/autores"
#     try:
#         r = safe_request(url, timeout=20)
#         if r and r.status_code == 200:
#             autores = r.json().get("dados", [])
#             if not autores:
#                 return ""
#             principal = next((a for a in autores if a.get("proponente") == 1), autores[0])
#             nome = (principal.get("nome") or "").strip()
#             uri = principal.get("uri") or ""   # pode vir vazio
#             # só tenta partido/UF se houver uri válida
#             if uri.startswith("http"):
#                 partido, uf = obter_partido_uf_deputado(uri)
#                 return f"{nome} ({partido}/{uf})" if nome else ""
#             return nome
#     except Exception as e:
#         logger.warning("fetch_autor falhou %s – %s", prop_id, e)
#     return ""

# def fetch_and_filter(year: int) -> pd.DataFrame:
#     url = f"https://dadosabertos.camara.leg.br/arquivos/proposicoes/csv/proposicoes-{year}.csv"
#     r = safe_request(url, timeout=120)
#     if not (r and r.status_code == 200):
#         logger.warning("CSV %s não baixado (status: %s)", year, getattr(r, "status_code", "N/A"))
#         return pd.DataFrame()
#     if not r.content:
#         logger.warning("CSV %s baixado com sucesso, mas o conteúdo está vazio.", year)
#         return pd.DataFrame()
#     try:
#         df = pd.read_csv(io.BytesIO(r.content), sep=";", engine="python", dtype=str)
#     except pd.errors.ParserError as e:
#         logger.error("Erro de parsing no CSV do ano %s. Erro: %s", year, e)
#         return pd.DataFrame()

#     df = df[df['siglaTipo'].isin(TIPOS_PROP)]
#     df = df[
#         df['ultimoStatus_descricaoSituacao'].isin(SITUACOES_FILTER) &
#         df['ultimoStatus_siglaOrgao'].isin(ORGAO_SIGLAS)
#     ]
#     df['dataApresentacao']      = pd.to_datetime(df['dataApresentacao'], errors='coerce')
#     df['ultimoStatus_dataHora'] = pd.to_datetime(df['ultimoStatus_dataHora'], errors='coerce')
#     return df

# def coletar_dados() -> pd.DataFrame:
#     logger.info("Coletando proposições (%s–%s)…", ANOS_INICIO, ANOS_FIM)
#     dfs = [fetch_and_filter(ano) for ano in range(ANOS_INICIO, ANOS_FIM + 1)]
#     dfs = [d for d in dfs if not d.empty]
#     if not dfs:
#         return pd.DataFrame()
#     df = pd.concat(dfs, ignore_index=True)

#     # Busca de autores em paralelo
#     with ThreadPoolExecutor(MAX_WORKERS) as exe:
#         fut2pid = {exe.submit(fetch_autor, pid): pid for pid in df['id']}
#         for fut in as_completed(fut2pid):
#             pid = fut2pid[fut]
#             try:
#                 df.loc[df['id'] == pid, 'Autor'] = fut.result()
#             except Exception as e:
#                 logger.warning("autor thread falhou %s – %s", pid, e)

#     df['Proposição'] = df['siglaTipo'] + ' ' + df['numero'] + '/' + df['ano']
#     return df

# def atualizar_dados():
#     logger.info("Iniciando atualização…")
#     df = coletar_dados()
#     if df.empty:
#         logger.error("DataFrame vazio – atualização abortada.")
#         return
#     salvar_csv(df)
#     logger.info("Atualização concluída (%d registros).", len(df))

# def busca_inicial():
#     """Gera CSV inicial se não existir (local/OBS)."""
#     if LOCAL_MODE and os.path.exists(LOCAL_CSV_PATH):
#         return
#     if not LOCAL_MODE:
#         # checa existência no OBS via metadata
#         try:
#             content, _ = obs_get_bytes(OBS_BUCKET, OBS_OBJECT_KEY)
#             if content:
#                 return
#         except Exception:
#             pass
#     atualizar_dados()

# # ────────────────────────────────────────────────────────────────────────────
# # AGENDADOR INTERNO (opcional)
# # ────────────────────────────────────────────────────────────────────────────
# _scheduler = None
# def iniciar_agendador():
#     global _scheduler
#     if _scheduler is None:
#         _scheduler = BackgroundScheduler()
#         _scheduler.add_job(atualizar_dados, 'interval', minutes=30, id='update30')
#         _scheduler.start()
#         logger.info("Agendador interno ativo a cada 30 min.")

# # ────────────────────────────────────────────────────────────────────────────
# # ENDPOINT  /atualizar  (Cloud Scheduler chama aqui)
# # ────────────────────────────────────────────────────────────────────────────
# @server.route("/atualizar", methods=["POST"])
# def endpoint_atualizar():
#     try:
#         atualizar_dados()
#         return "Atualização concluída", 200
#     except Exception as e:
#         logger.exception("Erro /atualizar: %s", e)
#         return f"Erro: {e}", 500
    
# @server.route("/obs-health")
# def obs_health():
#     try:
#         c = get_obs_client()
#         # tenta listar 1 objeto no prefixo (precisa List/Read no bucket)
#         r = c.listObjects(OBS_BUCKET, prefix="comissoes_cd/", max_keys=1)
#         return {
#             "bucket": OBS_BUCKET,
#             "endpoint": OBS_ENDPOINT,
#             "list_status": getattr(r, "status", None),
#             "list_count": len(getattr(r.body, "contents", []) or []),
#         }, 200
#     except Exception as e:
#         logger.exception("OBS health error")
#         return {"error": str(e)}, 500

# import tempfile

# @server.route("/healthz")
# def healthz():
#     try:
#         if LOCAL_MODE:
#             # garante que o diretório existe
#             if not os.path.isdir(BASE_DIR):
#                 return "base-dir-missing", 500

#             # teste de escrita sem condição de corrida
#             with tempfile.NamedTemporaryFile(dir=BASE_DIR,
#                                              prefix=".rwtest-",
#                                              delete=True) as tf:
#                 tf.write(b"ok")
#                 tf.flush()
#         return "ok", 200
#     except Exception as e:
#         logger.exception("healthz falhou: %s", e)
#         return "fail", 500

# @server.route("/busca-comissoes-cd/healthz")
# def healthz_prefixed():
#     return healthz()


# # ────────────────────────────────────────────────────────────────────────────
# # DASH – LAYOUT ORIGINAL
# # ────────────────────────────────────────────────────────────────────────────
# app = dash.Dash(
#     __name__,
#     server=server,
#     external_stylesheets=[dbc.themes.BOOTSTRAP,
#         "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css"],
#     title="Proposições Tramitando em Comissões da Câmara",
#     requests_pathname_prefix="/busca-comissoes-cd/",
#     routes_pathname_prefix="/busca-comissoes-cd/",
#     assets_url_path="/busca-comissoes-cd/assets",  # se tiver assets/
# )

# def _contagem_orgao(sub_df: pd.DataFrame):
#     if sub_df.empty:
#         return {}
#     return sub_df.groupby("ultimoStatus_siglaOrgao").size().to_dict()

# def layout_inicial():
#     df_init = carregar_csv()
#     if df_init.empty:
#         df_init = pd.DataFrame(columns=["siglaTipo","ultimoStatus_siglaOrgao","ultimoStatus_descricaoSituacao"])

#     tipos_unicos    = sorted(df_init["siglaTipo"].dropna().unique()) if not df_init.empty else []
#     orgao_unicos    = sorted(df_init["ultimoStatus_siglaOrgao"].dropna().unique()) if not df_init.empty else []
#     situacao_unicos = sorted(df_init["ultimoStatus_descricaoSituacao"].dropna().unique()) if not df_init.empty else []
#     cont_orgao_inicial = _contagem_orgao(df_init)

#     return dbc.Container(
#         fluid=True, style={"padding":"20px","fontFamily":"Verdana","color":"#000"},
#         children=[
#             html.H1("Proposições Tramitando em Comissões da Câmara dos Deputados",
#                     style={"color":"#183EFF","marginTop":"1rem","marginBottom":"0.5rem"}),
#             html.Hr(),

#             html.Div([
#                 html.P(f"Atualizado em {str_data_ultima_atualizacao()}",
#                        style={"fontStyle":"italic","fontSize":"11px","margin":"0"}),
#                 html.P("Dados obtidos via API da Câmara",
#                        style={"fontStyle":"italic","fontSize":"11px","margin":"0"})
#             ], style={"textAlign":"right","marginBottom":"1.5rem"}),

#             # Filtros
#             html.Div([
#                 html.Label("Tipo:", style={"fontWeight":"bold","fontSize":"16px"}),
#                 dcc.Checklist(id="filtro-tipo",
#                     options=[{"label":t,"value":t} for t in tipos_unicos],
#                     value=tipos_unicos, inline=True,
#                     inputStyle={"marginRight":"5px"},
#                     labelStyle={"marginRight":"22px","marginBottom":"6px"},
#                     style={"marginTop":"4px"})
#             ], style={"marginBottom":"30px"}),

#             html.Div([
#                 html.Label("Órgão:", style={"fontWeight":"bold","fontSize":"16px"}),
#                 dcc.Checklist(id="filtro-orgao",
#                     options=[{"label":f"{o} ({cont_orgao_inicial.get(o,0)})","value":o} for o in orgao_unicos],
#                     value=orgao_unicos, inline=True,
#                     inputStyle={"marginRight":"5px"},
#                     labelStyle={"marginRight":"22px","marginBottom":"6px"},
#                     style={"marginTop":"4px"})
#             ], style={"marginBottom":"30px"}),

#             html.Div([
#                 html.Label("Situação:", style={"fontWeight":"bold","fontSize":"16px"}),
#                 dcc.Checklist(id="filtro-situacao",
#                     options=[{"label":s,"value":s} for s in situacao_unicos],
#                     value=situacao_unicos, inline=True,
#                     inputStyle={"marginRight":"5px"},
#                     labelStyle={"marginRight":"22px","marginBottom":"6px"},
#                     style={"marginTop":"4px"})
#             ], style={"marginBottom":"40px"}),

#             dbc.Button("Exportar XLSX", id="btn-exportar", color="primary", className="mb-3"),
#             dcc.Download(id="download-xlsx"),

#             dash_table.DataTable(
#                 id="tabela",
#                 columns=[
#                     {"name":"Proposição","id":"Proposição"},
#                     {"name":"Autor","id":"Autor"},
#                     {"name":"Ementa","id":"ementa"},
#                     {"name":"Situação Atual","id":"ultimoStatus_descricaoSituacao"},
#                     {"name":"Inteiro Teor Inicial","id":"urlInteiroTeor","presentation":"markdown"},
#                     {"name":"Ficha de Tramitação","id":"fichaTramitacao","presentation":"markdown"}
#                 ],
#                 data=[],
#                 sort_action='native', filter_action='native',
#                 sort_mode='multi', page_action='native', page_size=50,
#                 fixed_rows={"headers":True},
#                 markdown_options={"link_target":"_blank"},
#                 css=[{"selector":".dash-spreadsheet","rule":"table-layout:fixed;width:100%;"}],
#                 style_table={"width":"100%","maxHeight":"600px","overflowX":"hidden"},
#                 style_cell={
#                     "textAlign":"left","whiteSpace":"normal","overflowWrap":"anywhere",
#                     "wordBreak":"break-word","height":"auto","padding":"4px",
#                     "fontFamily":"Verdana","fontSize":"14px"
#                 },
#                 style_cell_conditional=[
#                     {"if":{"column_id":"Proposição"}, "width":"90px","minWidth":"90px","maxWidth":"100px"},
#                     {"if":{"column_id":"Autor"},      "width":"140px","minWidth":"130px","maxWidth":"150px"},
#                     {"if":{"column_id":"ementa"},     "width":"340px","minWidth":"320px","maxWidth":"380px"},
#                     {"if":{"column_id":"ultimoStatus_descricaoSituacao"},
#                                                     "width":"180px","minWidth":"160px","maxWidth":"200px"},
#                     {"if":{"column_id":"urlInteiroTeor"},
#                                                     "width":"150px","minWidth":"140px","maxWidth":"170px"},
#                     {"if":{"column_id":"fichaTramitacao"},
#                                                     "width":"170px","minWidth":"150px","maxWidth":"190px"},
#                 ],
#                 style_header={
#                     "backgroundColor":"#183EFF","fontWeight":"bold",
#                     "color":"#FFFFFF","fontFamily":"Verdana"},
#                 style_data_conditional=[{"if":{"row_index":"odd"},"backgroundColor":"#F2F2F2"}],
#             )
#         ]
#     )

# app.layout = layout_inicial

# # ──────────────────────────────── CALLBACKS ────────────────────────────────
# @app.callback(
#     Output("tabela","data"),
#     Input("filtro-tipo","value"),
#     Input("filtro-orgao","value"),
#     Input("filtro-situacao","value")
# )
# def atualizar_tabela(tipos_sel, orgaos_sel, situacoes_sel):
#     df = carregar_csv()
#     if df.empty:
#         return []
#     dff = df[
#         df['siglaTipo'].isin(tipos_sel) &
#         df['ultimoStatus_siglaOrgao'].isin(orgaos_sel) &
#         df['ultimoStatus_descricaoSituacao'].isin(situacoes_sel)
#     ].copy()

#     dff['urlInteiroTeor'] = dff['urlInteiroTeor'].apply(
#         lambda u: f"[📄 Inteiro Teor]({u})" if pd.notna(u) and u else "")
#     dff['fichaTramitacao'] = dff['id'].apply(
#         lambda pid: (f"[🔍 Tramitação]"
#                      f"(https://www.camara.leg.br/proposicoesWeb/"
#                      f"fichadetramitacao?idProposicao={pid})")
#                      if pd.notna(pid) and pid else "")
#     return dff[['Proposição','Autor','ementa',
#                 'ultimoStatus_descricaoSituacao',
#                 'urlInteiroTeor','fichaTramitacao']].to_dict("records")

# @app.callback(
#     Output("filtro-orgao","options"),
#     Input("filtro-tipo","value"),
#     Input("filtro-situacao","value")
# )
# def atualizar_opcoes_orgao(tipos_sel, situacoes_sel):
#     df = carregar_csv()
#     if df.empty:
#         return []
#     dff = df[
#         df['siglaTipo'].isin(tipos_sel) &
#         df['ultimoStatus_descricaoSituacao'].isin(situacoes_sel)
#     ]
#     cont = _contagem_orgao(dff)
#     orgaos = sorted(df['ultimoStatus_siglaOrgao'].dropna().unique())
#     return [{"label":f"{o} ({cont.get(o,0)})","value":o} for o in orgaos]

# @app.callback(
#     Output("download-xlsx","data"),
#     Input("btn-exportar","n_clicks"),
#     State("tabela","data"),
#     prevent_initial_call=True
# )
# def exportar_xlsx(n_clicks, tabela_data):
#     df_exp = pd.DataFrame(tabela_data)
#     df_exp['Inteiro Teor Inicial'] = df_exp['urlInteiroTeor'].apply(
#         lambda m: (f'=HYPERLINK("{m[m.find("(")+1:-1]}", "📄 Inteiro Teor")') if m else "")
#     df_exp['Ficha de Tramitação'] = df_exp['fichaTramitacao'].apply(
#         lambda m: (f'=HYPERLINK("{m[m.find("(")+1:-1]}", "🔍 Tramitação")') if m else "")
#     df_exp = df_exp.drop(columns=['urlInteiroTeor','fichaTramitacao'], errors="ignore")

#     buffer = io.BytesIO()
#     with pd.ExcelWriter(buffer, engine="xlsxwriter") as w:
#         df_exp.to_excel(w, sheet_name="Proposições", index=False)
#     buffer.seek(0)
#     nome = f"proposicoes_{dt.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
#     return dcc.send_bytes(buffer.read(), nome)

# # ────────────────────────────────────────────────────────────────────────────
# # MAIN - CORRIGIDO
# # ────────────────────────────────────────────────────────────────────────────
# def run_initial_search_in_background():
#     """
#     Função para ser executada em uma thread separada.
#     Verifica se os dados iniciais são necessários e os busca.
#     """
#     # Adiciona uma pequena espera para garantir que o servidor suba primeiro
#     time.sleep(5)
#     logger.info("Thread de busca inicial iniciada em segundo plano.")
#     try:
#         # A lógica para decidir se a busca é necessária permanece a mesma
#         busca_inicial()
#     except Exception as e:
#         logger.exception("Busca inicial em segundo plano falhou: %s", e)

# # O Gunicorn/servidor de produção não executa o bloco __name__ == "__main__",
# # então movemos a lógica para o escopo global para garantir a execução.
# # Porém, para o `flask run` local funcionar, mantemos o __main__.

# logger.info("=== Inicialização da aplicação (LOCAL_MODE=%s) ===", LOCAL_MODE)

# # Validação rápida do OBS em produção
# if not LOCAL_MODE:
#     try:
#         _ = get_obs_client()
#         logger.info("OBS pronto: bucket=%s endpoint=%s", OBS_BUCKET, OBS_ENDPOINT)
#     except Exception as e:
#         logger.error("Falha ao iniciar OBS: %s", e)

# # Inicia a busca de dados inicial em uma thread separada para não bloquear o servidor.
# # Isso garante que o servidor suba imediatamente e responda aos health checks.
# initial_search_thread = threading.Thread(target=run_initial_search_in_background)
# initial_search_thread.daemon = True  # Permite que a aplicação finalize mesmo se a thread estiver rodando
# initial_search_thread.start()


# # Para execução local, o `app.run` ainda é útil.
# # Em produção, um servidor WSGI como Gunicorn ou uWSGI chamará o objeto `server`.
# if __name__ == "__main__":
#     app.run(host="0.0.0.0", port=PORT, debug=False)