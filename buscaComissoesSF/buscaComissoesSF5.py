import requests
import dash
import dash_bootstrap_components as dbc
from dash import dash_table, html, dcc, Input, Output, State
import pandas as pd
import datetime
import io
import re
import os
import xlsxwriter
from zoneinfo import ZoneInfo
from werkzeug.middleware.proxy_fix import ProxyFix


###############################################################################
# 1. BUSCA BÁSICA DAS MATÉRIAS EM CAE, CCJ E PLENÁRIO
###############################################################################
def buscar_materias_comissao(comissao_sigla, situacao=None):
    """
    Busca matérias de uma comissão específica, opcionalmente filtrando por situação.
    Usa HTTPS para evitar bloqueio de conteúdo misto no navegador.
    """
    url = f"https://legis.senado.leg.br/dadosabertos/materia/lista/comissao?comissao={comissao_sigla}"
    if situacao:
        url += f"&situacao={situacao}"
    headers = {"Accept": "application/json"}
    try:
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
        return resp.json()
    except (requests.exceptions.RequestException, ValueError) as e:
        print(f"Erro ao buscar matérias para {comissao_sigla}: {e}")
        return None


def formatar_autor(autor_str):
    """
    Formata o nome do autor. Se houver múltiplos autores separados por ',',
    retorna o primeiro autor seguido de 'e outros'.
    """
    if not autor_str:
        return "Autor não informado"
    autores = [a.strip() for a in autor_str.split(',') if a.strip()]
    if len(autores) == 1:
        return autores[0]
    elif len(autores) > 1:
        return f"{autores[0]} e outros"
    return "Autor não informado"


def obter_lista_colegiados():
    """Busca a lista de todos os colegiados (comissões, etc.) do Senado."""
    url = "https://legis.senado.leg.br/dadosabertos/comissao/lista/colegiados"
    headers = {"Accept": "application/json"}
    try:
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        colegiados = data.get("ListaColegiados", {}).get("Colegiados", {}).get("Colegiado", [])
        # Extrai apenas o que é necessário (label e value) para o dropdown
        return [{"label": f"{c['Sigla']} - {c['Nome']}", "value": c['Sigla']} for c in colegiados]
    except (requests.exceptions.RequestException, ValueError) as e:
        print(f"Erro ao buscar lista de colegiados: {e}")
        return []

def obter_dados_senado_comissoes(comissoes_interesse):
    # comissoes_interesse = ["cae", "ccj"] # Removido para receber como argumento
    situacoes_desejadas_cc = ["PRONTPAUT", "PEDVISTA", "INPAUTA"]
    todas_materias = []

    # CAE e CCJ
    for comissao in comissoes_interesse:
        for situacao in situacoes_desejadas_cc:
            json_data = buscar_materias_comissao(comissao, situacao=situacao)
            if not json_data:
                continue
            lista = (json_data.get("ListaMateriasEmComissao", {})
                             .get("Comissoes", {})
                             .get("Comissao", []))
            for com_info in lista:
                sigla_c = com_info.get("Sigla", "")
                materias = (com_info.get("Materias", {})
                                  .get("Materia", []))
                for mat in materias:
                    todas_materias.append({
                        "Codigo": mat.get("Codigo", ""),
                        "Sigla": mat.get("Sigla", ""),
                        "Numero": mat.get("Numero", ""),
                        "Ano": mat.get("Ano", ""),
                        "Ementa": mat.get("Ementa", ""),
                        "Autor": formatar_autor(mat.get("Autor", "")),
                        "SiglaSituacao": mat.get("SituacaoAtualProcesso", {}).get("SiglaSituacao", ""),
                        "Situação": mat.get("SituacaoAtualProcesso", {}).get("DescricaoSituacao", ""),
                        "Comissão": sigla_c
                    })

    # Plenário (adicionado separadamente se 'PLEN' for selecionado)
    if "PLEN" in comissoes_interesse:
        json_data_plenario = buscar_materias_comissao("plen", situacao="PRONDEPLEN")
        if json_data_plenario:
            lista = (json_data_plenario.get("ListaMateriasEmComissao", {})
                                     .get("Comissoes", {})
                                     .get("Comissao", []))
            for com_info in lista:
                sigla_c = com_info.get("Sigla", "")
                materias = (com_info.get("Materias", {})
                              .get("Materia", []))
                for mat in materias:
                    todas_materias.append({
                        "Codigo": mat.get("Codigo", ""),
                        "Sigla": mat.get("Sigla", ""),
                        "Numero": mat.get("Numero", ""),
                        "Ano": mat.get("Ano", ""),
                        "Ementa": mat.get("Ementa", ""),
                        "Autor": formatar_autor(mat.get("Autor", "")),
                        "SiglaSituacao": mat.get("SituacaoAtualProcesso", {}).get("SiglaSituacao", ""),
                        "Situação": mat.get("SituacaoAtualProcesso", {}).get("DescricaoSituacao", ""),
                        "Comissão": sigla_c
                    })

    df = pd.DataFrame(todas_materias)
    df["Possível impacto fiscal"] = ""
    df["Justificativa"] = ""
    return df

###############################################################################
# 2. BUSCA DETALHES
###############################################################################
def buscar_detalhes_materia(codigo):
    if not codigo:
        return {"data_situacao_recente": "", "historico_situacoes": "", "textos_associados": ""}
    url = f"https://legis.senado.leg.br/dadosabertos/materia/movimentacoes/{codigo}.json"
    headers = {"Accept": "application/json"}
    try:
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
        data = resp.json()
    except:
        return {"data_situacao_recente": "", "historico_situacoes": "", "textos_associados": ""}

    materia = data.get("MovimentacaoMateria", {}).get("Materia", {})
    autuacoes = materia.get("Autuacoes", {}).get("Autuacao", [])
    if not autuacoes:
        return {"data_situacao_recente": "", "historico_situacoes": "", "textos_associados": ""}

    aut = autuacoes[0]
    hist = aut.get("HistoricoSituacoes", {}).get("Situacao", [])
    if not isinstance(hist, list):
        hist = []
    for s in hist:
        dt = s.get("DataSituacao", "")
        try:
            s["_dt"] = datetime.datetime.strptime(dt, "%Y-%m-%d %H:%M:%S")
        except:
            try:
                s["_dt"] = datetime.datetime.strptime(dt, "%Y-%m-%d")
            except:
                s["_dt"] = None
    hist = [s for s in hist if s["_dt"]]
    hist.sort(key=lambda x: x["_dt"], reverse=True)
    data_recente = hist[0].get("DataSituacao", "") if hist else ""

    informes = aut.get("InformesLegislativos", {}).get("InformeLegislativo", [])
    if not isinstance(informes, list):
        informes = []
    TIPOS = {
        "Relatório Legislativo",
        "Avulso inicial da matéria",
        "Projeto de Lei Ordinária",
        "Projeto de Lei Complementar",
        "Proposta de Emenda à Constituição"
    }
    textos = []
    for inf in informes:
        sig = inf.get("Colegiado", {}).get("SiglaColegiado", "")
        assoc = inf.get("TextosAssociados", {}).get("TextoAssociado", [])
        if not isinstance(assoc, list):
            assoc = []
        for tx in assoc:
            tipo = tx.get("DescricaoTipoTexto", "")
            url_txt = tx.get("UrlTexto", "") or ""
            if url_txt.startswith("http://"):
                url_txt = "https://" + url_txt[len("http://"):]
            if tipo in TIPOS and url_txt:
                lbl = f"{tipo} ({sig})" if sig else tipo
                textos.append(f"[{lbl}]({url_txt})")

    return {
        "data_situacao_recente": data_recente,
        "historico_situacoes": "\n".join(f"{s.get('DataSituacao','')} - {s.get('DescricaoSituacao','')}" for s in hist),
        "textos_associados": "\n".join(textos)
    }

def agregar_detalhes(df):
    if df.empty:
        df["DataSituacaoRecente"] = ""
        df["HistoricoSituacoes"] = ""
        df["TextosAssociados"] = ""
        return df

    ds, hs, ta = [], [], []
    for _, row in df.iterrows():
        det = buscar_detalhes_materia(row["Codigo"])
        ds.append(det["data_situacao_recente"])
        hs.append(det["historico_situacoes"])
        ta.append(det["textos_associados"])
    df["DataSituacaoRecente"] = ds
    df["HistoricoSituacoes"] = hs
    df["TextosAssociados"] = ta
    return df

###############################################################################
# 3. FILTRAR E AGRUPAR
###############################################################################
def filtrar_materias(df):
    if df.empty:
        return pd.DataFrame(columns=["Codigo","Título","Ementa","Autor","Situação","Comissão"])
    siglas = ["PL","PEC","PLP","PLC","PLS","PDL","PDS"]
    sit = ["PRONTPAUT","PEDVISTA","INPAUTA","PRONDEPLEN"]
    dff = df[(df["Sigla"].isin(siglas)) & (df["SiglaSituacao"].isin(sit))].copy()
    if dff.empty:
        return pd.DataFrame(columns=["Codigo","Título","Ementa","Autor","Situação","Comissão"])
    dff["Título"] = dff.apply(lambda r: f"{r['Sigla']} {r['Numero'].lstrip('0') or r['Numero']}/{r['Ano']}", axis=1)
    return dff

###############################################################################
# 4. CRIAR APLICAÇÃO DASH COM MENSAGEM DE ATUALIZAÇÃO E CABEÇALHO FIXO
###############################################################################
def criar_app_dash(lista_colegiados):
    # Timestamp de quando a busca foi executada
    agora = datetime.datetime.now(ZoneInfo("America/Sao_Paulo"))
    hora_atualizacao = f"Dados atualizados em {agora.strftime('%d/%m/%Y')} às {agora.strftime('%H:%M')}"

    
    app = dash.Dash(
        __name__,
        external_stylesheets=[dbc.themes.BOOTSTRAP],
        # Faça o Dash gerar todas as rotas com o prefixo
        requests_pathname_prefix="/busca-comissoes/",
        routes_pathname_prefix="/busca-comissoes/",
    )

    server = app.server
    # Corrige scheme/host quando há proxy (Ingress/NAT/ELB)
    server.wsgi_app = ProxyFix(server.wsgi_app, x_proto=1, x_host=1)

    # DataFrame inicial vazio
    df_inicial = pd.DataFrame(columns=[
        "Codigo", "Título", "Autor", "Ementa", "DataSituacaoRecente",
        "TextosAssociados", "Ficha de Tramitação", "Situação", "Comissão"
    ])

    colunas_tabela = [
        {"name": "Proposição", "id": "Título"},
        {"name": "Autor",       "id": "Autor"},
        {"name": "Ementa",      "id": "Ementa"},
        {"name": "Data último status", "id": "DataSituacaoRecente"},
        {"name": "Textos Associados",  "id": "TextosAssociados",   "presentation": "markdown"},
        {"name": "Ficha de Tramitação","id": "Ficha de Tramitação","presentation": "markdown"}
    ]

    app.layout = dbc.Container([
        html.H1("Proposições Tramitando em Comissões do Senado",
                style={"color": "#0a2242", "fontFamily": "Verdana"}),
        html.Hr(),
        html.Div(id="mensagem-atualizacao", style={"textAlign": "right", "fontStyle": "italic", "fontSize": "11px", "marginBottom": "10px"}),

        dbc.Row([
            dbc.Col(dcc.Dropdown(
                id='dropdown-comissoes',
                options=lista_colegiados,
                value=['CAE', 'CCJ', 'CTFC', 'CMO', 'CCDD', 'CAS'],  # Valores iniciais
                multi=True,
                placeholder="Selecione as comissões..."
            ), width=9),
            dbc.Col(dbc.Button("Buscar Matérias", id='btn-buscar', n_clicks=0, color="primary"), width=3),
        ]),
        html.Br(),
        dcc.Loading(id="loading-spinner", children=[
            dbc.Button("Exportar XLSX", id="btn-exportar", color="secondary", style={"display": "none"}),
            dcc.Download(id="download-xlsx"),
            html.Br(),
            dcc.Checklist(
                id="checklist_comissoes",
                labelStyle={"display": "inline-block", "margin-right": "15px", "fontFamily": "Verdana"},
                inputStyle={"margin-right": "5px"}
            ),
            html.Br(),
            dcc.Checklist(
                id="checklist_situacoes",
                labelStyle={"display": "inline-block", "margin-right": "15px", "fontFamily": "Verdana"},
                inputStyle={"margin-right": "5px"}
            ),
            html.Br(),
            dash_table.DataTable(
                id="tabela_proposicoes",
                columns=colunas_tabela,
                data=[], # Começa sem dados
                filter_action="native",
                sort_action="native",
                sort_mode="multi",
                page_action="none",
                fixed_rows={"headers": True},
                style_table={"overflowX": "visible", "maxHeight": "600px", "overflowY": "auto"},
                style_cell={
                    "whiteSpace": "pre-line", "height": "auto", "textAlign": "left",
                    "padding": "5px", "fontFamily": "Verdana", "fontSize": "14px", "color": "#000000"
                },
                style_cell_conditional=[
                    {"if": {"column_id": "Título"},             "width": "100px"},
                    {"if": {"column_id": "Autor"},               "width": "150px"},
                    {"if": {"column_id": "Ementa"},              "width": "400px"},
                    {"if": {"column_id": "DataSituacaoRecente"}, "width": "150px"},
                    {"if": {"column_id": "TextosAssociados"},    "width": "250px"},
                    {"if": {"column_id": "Ficha de Tramitação"}, "width": "100px"},
                ],
                style_header={"backgroundColor": "#0023b3", "fontWeight": "bold",
                              "color": "#FFFFFF", "fontFamily": "Verdana"},
                style_data_conditional=[{"if": {"row_index": "even"}, "backgroundColor": "#F2F2F2"}],
            )
        ], type="circle"),
        dcc.Store(id='dados-completos-store', data=df_inicial.to_dict('records'))
], fluid=True, style={"backgroundColor": "#FFFFFF", "color": "#000000", "fontFamily": "Verdana", "padding": "20px"})

    @app.callback(
        [Output('dados-completos-store', 'data'),
         Output('checklist_comissoes', 'options'),
         Output('checklist_comissoes', 'value'),
         Output('checklist_situacoes', 'options'),
         Output('checklist_situacoes', 'value'),
         Output('mensagem-atualizacao', 'children'),
         Output('btn-exportar', 'style')],
        [Input('btn-buscar', 'n_clicks')],
        [State('dropdown-comissoes', 'value')],
        prevent_initial_call=True
    )
    def buscar_dados(n_clicks, comissoes_selecionadas):
        if not n_clicks or not comissoes_selecionadas:
            raise dash.exceptions.PreventUpdate

        df_senado = obter_dados_senado_comissoes(comissoes_selecionadas)
        df_filtrado = filtrar_materias(df_senado)
        
        if df_filtrado.empty:
            df_final = pd.DataFrame(columns=df_inicial.columns)
            opts_com, val_com, opts_sit, val_sit = [], [], [], []
        else:
            df_final = agregar_detalhes(df_filtrado)
            if "Situação" not in df_final.columns: df_final["Situação"] = ""
            if "Comissão" not in df_final.columns: df_final["Comissão"] = ""
            df_final["Ficha de Tramitação"] = df_final["Codigo"].apply(
                lambda cod: f"[🔎 Ficha](https://www25.senado.leg.br/web/atividade/materias/-/materia/{cod})"
            )
            
            com_counts = df_final["Comissão"].value_counts().to_dict()
            opts_com = [{"label": f"{c}: {com_counts[c]}", "value": c} for c in sorted(com_counts)]
            val_com = [o["value"] for o in opts_com]

            uniq_sit = sorted(s for s in df_final["Situação"].unique() if isinstance(s, str) and s.strip())
            opts_sit = [{"label": s[0].upper() + s[1:].lower(), "value": s} for s in uniq_sit]
            val_sit = [o["value"] for o in opts_sit]

        agora = datetime.datetime.now(ZoneInfo("America/Sao_Paulo"))
        hora_atualizacao_msg = [
            html.Div(f"Dados atualizados em {agora.strftime('%d/%m/%Y')} às {agora.strftime('%H:%M')}"),
            html.Div("Dados obtidos via API do Senado")
        ]
        
        btn_style = {'display': 'inline-block'} if not df_final.empty else {'display': 'none'}

        return df_final.to_dict('records'), opts_com, val_com, opts_sit, val_sit, hora_atualizacao_msg, btn_style

    @app.callback(
        Output("tabela_proposicoes", "data"),
        [Input('dados-completos-store', 'data'),
         Input("checklist_comissoes", "value"),
         Input("checklist_situacoes", "value")]
    )
    def filtrar_tabela(dados_json, coms, sits):
        if not dados_json or not coms or not sits:
            return []
        df_f = pd.DataFrame(dados_json)
        df_filtrada = df_f[df_f["Comissão"].isin(coms) & df_f["Situação"].isin(sits)]
        return df_filtrada.to_dict("records")

    @app.callback(
        Output("download-xlsx", "data"),
        Input("btn-exportar", "n_clicks"),
        State("tabela_proposicoes", "data"),
        prevent_initial_call=True
    )
    def exportar_xlsx(n, data):
        if not n:
            raise dash.exceptions.PreventUpdate
        df_export = pd.DataFrame(data)
        def parse_links(md): return re.findall(r"\[([^\]]+)\]\(([^)]+)\)", md)
        def mk_link(fnd):
            if not fnd: return None
            formulas = [f'=HYPERLINK("{u}","{t}")' for t, u in fnd]
            if len(formulas) == 1:
                return formulas[0]
            return formulas[0] + f' & CHAR(10) & " +{len(formulas)-1} links..."'
        for col in ["TextosAssociados", "Ficha de Tramitação"]:
            if col in df_export:
                df_export[col] = df_export[col].apply(
                    lambda v: mk_link(parse_links(str(v))) if v else None
                )
        out = io.BytesIO()
        with pd.ExcelWriter(out, engine="xlsxwriter") as writer:
            df_export.to_excel(writer, sheet_name="Dados", index=False)
            ws = writer.sheets["Dados"]
            map_cols = {c: i for i, c in enumerate(df_export.columns)}
            for r in range(len(df_export)):
                for col in ["TextosAssociados", "Ficha de Tramitação"]:
                    if col in map_cols:
                        val = df_export.iat[r, map_cols[col]]
                        if isinstance(val, str) and val.startswith("=HYPERLINK"):
                            ws.write_formula(r+1, map_cols[col], val)
        return dcc.send_bytes(out.getvalue(), "proposicoes_senado.xlsx")

    return app

###############################################################################
# 5. MAIN
###############################################################################
if __name__ == "__main__":
    lista_colegiados = obter_lista_colegiados()
    app = criar_app_dash(lista_colegiados)
    port = int(os.environ.get("PORT", 8080))
    print(f"Acesse: http://0.0.0.0:{port}")
    app.run(debug=False, host="0.0.0.0", port=port)