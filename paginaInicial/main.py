import os
from pathlib import Path
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
import uvicorn
import base64
import httpx

app = FastAPI()

secret_key = os.environ.get("SECRET_KEY", "SUA_CHAVE_SECRETA_AQUI")

# Adiciona o middleware de sessões (necessário para autenticação)
app.add_middleware(SessionMiddleware, secret_key=secret_key)

# Obtém o diretório base onde main.py está localizado
BASE_DIR = Path(__file__).resolve().parent

# Define os diretórios de static e templates (assumindo que estão no mesmo nível de main.py)
static_dir = BASE_DIR / "static"
templates_dir = BASE_DIR / "templates"

# Monta a pasta de arquivos estáticos
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Configura os templates
templates = Jinja2Templates(directory=str(templates_dir))

# Funções de codificação/decodificação para mascarar URLs
def encode_url(url: str) -> str:
    return base64.urlsafe_b64encode(url.encode()).decode()

def decode_url(encoded: str) -> str:
    return base64.urlsafe_b64decode(encoded.encode()).decode()

# Dicionário de usuários válidos com perfil (email: { token, profile })
#linha vazia:

#"e-mail": {"token": "", "profile": "normal"},

#profile "admin" -> enxerga todos os botões

valid_users = {
    #gabinete
    "daianapaulasales@gmail.com": {"token": "12345", "profile": "admin"},
    "cmota.dev@gmail.com": {"token": "12345", "profile": "admin"},
    #secretarias
}

# Lista das páginas (dados reais)
paginas = [
    {"titulo": "Informativo MPO no Congresso", "url": "/redirect/informativo"},
    {"titulo": "Agenda da Semana (em atualização)", "url": "/redirect/agenda"},
    {"titulo": "Requerimentos", "url": "/redirect/requerimentos"},
    {"titulo": "Matérias em Tramitação nas Comissões (Senado)", "url": "/redirect/comissoes_senado"},
    {"titulo": "Matérias em Tramitação nas Comissões (Câmara)", "url": "/redirect/comissoes_camara"},
    {"titulo": "Matérias Prioritárias", "url": "/redirect/materias_prioritarias"},
    {"titulo": "Busca Avançada em Proposições", "url": "/redirect/busca_avancada"},
    {"titulo": "Nuvem de Palavras", "url": ""},
    {"titulo": "Análise de Votações", "url": ""},
    {"titulo": "Classificação Automatizada de Proposições", "url": ""},
    {"titulo": "Acompanhamento de Sanção e Veto", "url": ""}
]

# Página de Login (GET)
@app.get("/login", response_class=HTMLResponse)
async def get_login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

# Página de Login (POST)
@app.post("/login")
async def post_login(request: Request, email: str = Form(...), token: str = Form(...)):
    if email in valid_users and valid_users[email]["token"] == token:
        request.session["authenticated"] = True
        request.session["email"] = email
        request.session["profile"] = valid_users[email]["profile"]
        return RedirectResponse(url="/", status_code=303)
    else:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Email ou token inválidos"})

# Rota de Logout
@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=303)

# Página principal – requer autenticação e filtra as páginas de acordo com o perfil
@app.get("/", response_class=HTMLResponse)
async def portal(request: Request):
    if not request.session.get("authenticated"):
        return RedirectResponse(url="/login", status_code=303)
    user_profile = request.session.get("profile", "normal")
    # Filtra: se o usuário for "normal", remove o botão "Agenda da Semana"
    filtered_paginas = [p for p in paginas if not (user_profile != "admin" and p["titulo"] == "Agenda da Semana")]
    return templates.TemplateResponse("portal_index.html", {"request": request, "paginas": filtered_paginas})

# Rota de redirecionamento para mascarar os links (irá redirecionar para a URL externa)
@app.get("/redirect/{page_name}", response_class=RedirectResponse)
async def redirect(page_name: str):
    urls = {
        "informativo": "https://sites.google.com/view/mpo-seai-links/in%C3%ADcio",
        "agenda": "https://busca-eventos-xmfmknifxq-rj.a.run.app/",
        "requerimentos": "https://busca-reqs-xmfmknifxq-rj.a.run.app",
        "comissoes_senado": "https://busca-comissoes-sf-xmfmknifxq-rj.a.run.app/",
        "comissoes_camara": "https://busca-comissoes-cd-xmfmknifxq-rj.a.run.app/",
        "materias_prioritarias": "https://busca-materias-senado-xmfmknifxq-rj.a.run.app",
        "busca_avancada": "https://base-pl-xmfmknifxq-rj.a.run.app/"
    }
    url = urls.get(page_name, "/")
    return RedirectResponse(url=url)

# Página de Manual
@app.get("/manual", response_class=HTMLResponse)
async def read_manual(request: Request):
    if not request.session.get("authenticated"):
        return RedirectResponse(url="/login", status_code=303)
    manual_conteudo = """
    <p>Aqui você encontrará informações essenciais para utilizar a Plataforma MPO no Congresso</p>
    <ul>
        <li><strong>Navegação:</strong> Utilize o menu superior para acessar a página inicial, o manual e a documentação.</li>
        <li><strong>Informativo MPO no Congresso:</strong> Link para o site de acompanhamento das proposições e votações.</li>
        <li><strong>Agenda da Semana:</strong> Veja os eventos e proposições previstos para a semana.</li>
        <li><strong>Requerimentos:</strong> Consulte os requerimentos apresentados na Câmara e no Senado.</li>
        <li><strong>Matérias em Tramitação (Senado):</strong> Consulte as matérias prontas para pauta.</li>
        <li><strong>Matérias em Tramitação (Câmara):</strong> Consulte as matérias prontas para pauta.</li>
        <li><strong>Matérias Prioritárias:</strong> Consulte o status das matérias de interesse do MPO.</li>
        <li><strong>Busca Avançada em Proposições:</strong> Base de matérias em tramitação na Câmara.</li>
    </ul>
    """
    return templates.TemplateResponse("manual.html", {"request": request, "manual_conteudo": manual_conteudo})

# Página de Documentação
@app.get("/documentacao", response_class=HTMLResponse)
async def read_documentacao(request: Request):
    if not request.session.get("authenticated"):
        return RedirectResponse(url="/login", status_code=303)
    doc_conteudo = """
    <h2>Documentação do Sistema</h2>
    <p>Aqui você encontrará a documentação técnica e funcional da Plataforma Legislativa.</p>
    <h3>Principais Endpoints</h3>
    <ul>
        <li><strong>/</strong>: Página inicial com links para as aplicações.</li>
        <li><strong>/manual</strong>: Manual do Usuário.</li>
        <li><strong>/documentacao</strong>: Documentação técnica do sistema.</li>
    </ul>
    <h3>Atualizações e Versionamento</h3>
    """
    return templates.TemplateResponse("documentacao.html", {"request": request, "doc_conteudo": doc_conteudo})

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
