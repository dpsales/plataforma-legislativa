Projeto **"Plataforma Legislativa"**.

-----

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

### **Stack Tecnológica**

```
🖥️ Backend
├── Django 5.2+ (Framework web)
├── PostgreSQL 13+ (Banco de dados relacional)
├── Elasticsearch 7.10+ (Motor de busca e indexação)
├── Redis (Cache e Filas de tarefas)
└── Celery (Processamento assíncrono de dados)

🎨 Frontend
├── HTML5 + CSS3 + JavaScript
├── Bootstrap (Componentes e responsividade)
├── Chart.js (Gráficos e visualizações)
└── Design System Gov.br (Opcional)

☁️ Infraestrutura
├── Kubernetes (Orquestração de contêineres)
├── Docker (Containerização)
├── GitHub Actions (CI/CD)
├── Nginx (Servidor web e proxy reverso)
└── Persistent Volumes (Armazenamento)
```

### **Estrutura do Projeto**

```
plataforma-legislativa/
├── src/                         # Código-fonte Django
│   ├── legislativo/             # App principal: proposições, votações
│   │   ├── models.py            # Models: Proposicao, Votacao, Documento
│   │   ├── views.py             # Views: Busca, Detalhes, APIs
│   │   ├── tasks.py             # Tarefas Celery para coleta de dados
│   │   └── services/            # Lógica de integração com Elasticsearch
│   ├── parlamentares/           # App para perfis de parlamentares
│   ├── usuarios/                # Sistema de autenticação e alertas
│   ├── core/                    # Configurações Django
│   ├── staticfiles/             # Assets estáticos
│   └── templates/               # Templates HTML
├── k8s/                         # Configurações Kubernetes
├── guides/                      # Documentação técnica
└── requirements.txt             # Dependências Python
```

-----

## 🚀 Guia de Instalação

### 📋 **Pré-requisitos**

  - **Python 3.8+**
  - **PostgreSQL 13+**
  - **Elasticsearch 7.10+**
  - **Redis 6+**
  - **Git**

### **1️⃣ Clone do Repositório**

```bash
git clone https://github.com/seu-usuario/plataforma-legislativa.git
cd plataforma-legislativa/src
```

### **2️⃣ Ambiente Virtual**

```bash
python -m venv venv
source venv/bin/activate
```

### **3️⃣ Instalação de Dependências**

```bash
pip install -r requirements.txt
```

### **4️⃣ Configuração de Ambiente**

Crie o arquivo `.env` na pasta `src/`:

```env# Configurações de Email (para alertas e notificações)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.seuservidor.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=seu_email@dominio.com
EMAIL_HOST_PASSWORD=sua_senha_de_email

# Configurações de Cache (Redis)
CACHES_DEFAULT_LOCATION=127.0.0.1:6379:1

# Configurações Django
SECRET_KEY=sua-chave-secreta-django
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Banco de dados PostgreSQL
POSTGRES_DB=legislativo
POSTGRES_USER=seu_usuario
POSTGRES_PASSWORD=sua_senha_segura
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# Elasticsearch
ELASTICSEARCH_URL=http://localhost:9200

# Redis
REDIS_URL=redis://localhost:6379/0
```

### **5️⃣ Configuração do Banco**

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

### **6️⃣ Execução do Sistema**

```bash
# Em um terminal, inicie o worker Celery
celery -A core worker -l info

# Em outro terminal, inicie o servidor de desenvolvimento
python manage.py runserver
```

-----

## 📚 Uso do Sistema

### **🔐 Autenticação**

1.  Acesse `/usuarios/login/` para fazer login.
2.  Crie uma conta ou use as credenciais de superusuário.

### **🔍 Navegação**

1.  **Página Inicial**: Dashboard com destaques e busca principal.
2.  **Busca**: `/busca/` - Utilize filtros para encontrar proposições.
3.  **Parlamentares**: `/parlamentares/` - Navegue e encontre perfis.

### **🛠️ Administração**

1.  **Painel Admin**: Acesse `/admin/`.
2.  **Funcionalidades**:
      - Gerenciar fontes de dados.
      - Monitorar tarefas de importação.
      - Visualizar logs e métricas de uso.

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

**Gabin/SEGES/MGI**

**Responsável Técnico**: 


**Equipe de Desenvolvimento**:

  - Mario dos Santos M. Valverde Neto ASPAR/MPO
  - Daiana de Paula Sales GABIN/SEGES/MGI

### **📧 Contatos**

  - **Issues**: [Link para as Issues do GitHub]
  - **Documentação**: `/guides/` dentro do projeto.

-----

## 📜 Licença

Este projeto está licenciado sob a **Licença MIT** - veja o arquivo [LICENSE](https://www.google.com/search?q=LICENSE) para detalhes.
