## 📋 Sobre a Plataforma Legislativa

A **Plataforma Legislativa** é um sistema de código aberto projetado para coletar, organizar e apresentar dados do processo legislativo de forma acessível e transparente. A ferramenta permite que cidadãos, jornalistas e pesquisadores monitorem proposições, votações e a atividade de parlamentares em tempo real.

### 🎯 Missão

Facilitar o controle social e o engajamento cívico, fornecendo acesso simplificado e inteligente a dados legislativos abertos, promovendo a transparência e a accountability no setor público.

-----

## 🌟 Funcionalidades Principais

### 🔍 **Busca e Consulta Avançada**

  - **Motor de busca poderoso** com Elasticsearch para leis, projetos de lei e documentos.
  - **Filtros avançados** por status, autor, partido, data e tema.
  - **Visualização completa** do histórico e tramitação de proposições.
  - **Acesso a textos integrais** e documentos associados.

### 👤 **Perfis de Parlamentares**

  - **Página dedicada** para cada parlamentar com biografia e contatos.
  - **Histórico de votações** detalhado e classificado.
  - **Análise de presença** em sessões plenárias.
  - **Lista de proposições** de autoria do parlamentar.

### 📊 **Dashboard Analítico**

  - **Visualização de dados** sobre a produção legislativa.
  - **Gráficos interativos** sobre temas mais discutidos, partidos e autores.
  - **Métricas de produtividade** do legislativo e de parlamentares.
  - **Linha do tempo** de eventos importantes.

### 🔔 **Alertas e Notificações**

  - **Sistema de inscrição** para receber alertas sobre temas de interesse.
  - **Notificações por e-mail** sobre novas proposições ou mudanças de status.
  - **Funcionalidade "Favoritos"** para acompanhar parlamentares e projetos específicos.

### ⚙️ **API de Dados Abertos**

  - **Endpoints RESTful** para acesso a todos os dados da plataforma.
  - **Documentação completa** (Swagger/OpenAPI) para desenvolvedores.
  - **Chaves de API** para controle de acesso e rate limiting.

### 🛠️ **Painel Administrativo**

  - **Interface de gerenciamento** para administradores do sistema.
  - **Módulo de ingestão de dados** (via APIs de fontes oficiais ou upload).
  - **Monitoramento de saúde** dos serviços e logs do sistema.

-----

## 🏗️ Arquitetura Técnica

### **Stack Tecnológica (atual)**

```
🖥️ Backend
├── `paginaInicial/` (Django 4 + Gunicorn) — gateway de autenticação e roteamento
├── Microserviços Django independentes (`busca*`, `basePL/`) servindo dados e páginas específicas
└── Scripts de coleta assíncrona via Celery/Redis onde aplicável

🎨 Frontend
└── Templates Django + Dash (serviço `buscaEventos/`)

☁️ Infraestrutura
├── Docker + docker-compose
├── Redis (broker/result backend Celery)
└── Nginx (proxy reverso em `revProxy/`)

🧩 Serviços adicionais
└── `basePL/` — serviço de consulta/base de pesos; `buscaComissoesCD/`, `buscaComissoesSF/`, `buscaComissoesMistas/`, `buscaReqs/`, `buscaEventos/` etc.
```

### **Estrutura do Projeto**

---

Estrutura de diretórios principal
--------------------------------

```
plataforma-legislativa/
├── docker-compose.yaml        # Orquestra todos os serviços
├── revProxy/                  # Configuração Nginx para roteamento em 8080
├── paginaInicial/             # Gateway Django (login, menus, rotas internas)
│   ├── pagina_inicial/        # settings.py, urls.py, wsgi.py
│   ├── portal/                # Views/templates do portal principal
│   ├── basepl/                # App Django para busca/configuração BasePL
│   ├── static/                # CSS/JS do gateway
│   └── templates/             # Templates (login, portal, documentação, etc.)
├── basePL/                    # Serviço BasePL (pesos e busca unificada)
├── buscaComissoesCD/          # Django + Celery para comissões da Câmara
├── buscaComissoesSF/          # Django + Celery para comissões do Senado
├── buscaComissoesMistas/      # Django + Celery para comissões mistas
├── buscaEventos/              # Coleta + Dash para eventos legislativos
├── buscaMaterias/             # Coleta de matérias legislativas
├── buscaReqs/                 # Coleta de requerimentos e autores
└── .../data                   # Bancos SQLite/artefatos persistidos por serviço
```

Cada microserviço possui `Dockerfile`, `requirements.txt`, scripts e eventuais rotinas Celery próprias. O gateway `paginaInicial/` autentica o usuário e redireciona para os serviços publicados atrás do `revProxy` na mesma rede Docker. Dados persistidos em `*/data/` permanecem entre reinicializações.

---

## 🚀 Guia de Instalação

### 📋 **Pré-requisitos**

  - **Python 3.8+**
  - **Docker**
  - **Git**

### **1️⃣ Clone do Repositório**

```bash
git clone https://github.com/seu-usuario/plataforma-legislativa.git
cd plataforma-legislativa
```

### **2️⃣ Subindo com Docker Compose**

```bash
docker compose up --build
```

- Portal: http://localhost:8080 (via Nginx)
- Acesso direto ao Django/Gunicorn: http://localhost:8000

Para atualizar configurações, use variáveis no próprio comando ou em um `.env` na raiz:

```
PAGINA_INICIAL_SECRET_KEY=altere-essa-chave
PAGINA_INICIAL_DEBUG=True
```

-----

## 📚 Uso do Sistema

- **Autenticação:** `/login` usa usuários definidos em `paginaInicial/users/users.json`.
- **Portal:** `/` exibe o grid com cartões; cada botão redireciona para serviços externos (ex.: `comissoes_senado`, `requerimentos`).
- **Comissões da Câmara:** `/busca-comissoes-cd/` abre o novo painel web servido pelo microserviço Django (filtros avançados + exportação).
- **Logout:** `/logout` limpa a sessão.

-----

## 🔧 APIs Disponíveis

```http
# Proposições
GET /api/v1/proposicoes/                # Listar proposições
GET /api/v1/proposicoes/{id}/           # Detalhes de uma proposição

# Parlamentares
GET /api/v1/parlamentares/              # Listar parlamentares
GET /api/v1/parlamentares/{id}/         # Detalhes de um parlamentar
GET /api/v1/parlamentares/{id}/votos/   # Votos de um parlamentar

# Votações
GET /api/v1/votacoes/                   # Listar votações
```

-----

## 🌐 Deploy em Produção

### **🐳 Docker**

```bash
# Build das imagens
docker-compose build

# Execução com docker-compose
# Crie o arquivo .env e preencha com suas variaveis de produção
cp .env-sample .env
docker-compose up -d
```

### **🚆 Railway + Gunicorn (docker-compose)**

Use o compose dedicado para iniciar o Django com `gunicorn` em modo produção:

```bash
docker compose -f docker-compose.railway.yml up --build
```

Variáveis recomendadas no Railway:

```env
SECRET_KEY=sua-chave-forte
DEBUG=False
ALLOWED_HOSTS=.up.railway.app
CSRF_TRUSTED_ORIGINS=https://seu-servico.up.railway.app
DATABASE_URL=postgres://...
DATABASE_SSL_REQUIRE=true
PORT=$PORT
```

### **🚆 Railway (railway.toml)**

O repositório também inclui configuração pronta em `railway.toml`, com build por Dockerfile e start em Gunicorn na porta dinâmica do Railway.


### **☸️ Kubernetes**

```bash
# Aplique os manifestos no seu cluster
kubectl apply -f k8s/

# Verifique o status dos pods
kubectl get pods -n plataforma-legislativa
```

-----

## 🤝 Contribuindo

### **🔄 Processo de Contribuição**

1.  **Fork** do projeto.
2.  Crie uma **Branch** para sua feature: `git checkout -b feature/minha-feature`.
3.  Faça o **Commit** das suas mudanças: `git commit -m "feat: adiciona minha feature"`.
4.  Faça o **Push** para a branch: `git push origin feature/minha-feature`.
5.  Abra um **Pull Request**.

-----

## 📞 Suporte e Contato

### **👥 Equipe Responsável**

**Equipe de Desenvolvimento**:

  - Mario dos Santos M. Valverde Neto ASPAR/MPO
  - Daiana de Paula Sales CGINF/SEGES/MGI

### **📧 Contatos**

  - **Issues**: [Link para as Issues do GitHub]
  - **Documentação**: `/guides/` dentro do projeto.

-----

## 📜 Licença

Este projeto está licenciado sob a **Licença MIT** - veja o arquivo [LICENSE](https://www.google.com/search?q=LICENSE) para detalhes.
