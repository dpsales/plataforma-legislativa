# Copilot Instructions for Plataforma Legislativa

This document provides instructions for AI coding agents to effectively contribute to the Plataforma Legislativa project.

## 1. Architecture Overview

The Plataforma Legislativa is a microservices-based system designed to collect, process, and display legislative data from the Brazilian Congress (Câmara dos Deputados and Senado Federal). The services are containerized with Docker and orchestrated via `docker-compose.yaml`.

The main components are:

-   **`paginaInicial/`**: Django gateway that implements login and exposes links to the external services (comissões, requerimentos, etc.). All users and menus are configured here.
     
-   **Data Services**: Conjunto de microserviços responsáveis por coletar e expor dados legislativos.
    -   `buscaPL/`: apresentar as buscas tanto na camara como no senado, para as proposições de acordo com os pesos.
    -   `buscaMaterias/`: Fetches legislative proposals, de acordo com o arquivo dado. 
    -   `buscaComissoesCD/`: Django + Celery; coleta proposições em comissões da Câmara, persiste em banco SQL e expõe UI HTML/JS.
    -   `buscaComissoesSF/`: Fetches committee information from the Senado.
    -   `buscaEventos/`: Fetches legislative events and includes a **Dash** application (`codUnificado/codunif17.py`) for data analysis and visualization. Aonde apareça a agenda do mês anterior, a semana atual e os eventos da próxima semana. 
    -   `buscaReqs/`: Fetches requirements and author information, visualizar as requisções de acordo com as configurações. 
-   **`revProxy/`**: An **Nginx** reverse proxy that routes incoming traffic to the appropriate service. The routing logic is in `revProxy/conf/default.conf`.
-   **`docker-compose.yaml`**: The main file that defines and connects all the services. Refer to this file to understand service names, ports, and network configurations.

## 2. Development Workflow

The primary development workflow relies on Docker.

### Running the Full Stack

To run the entire platform, use Docker Compose from the project root:

```bash
# Build and start all services in detached mode
docker-compose up --build -d
```

### Working with the Django Application (`paginaInicial`)

If you need to work specifically on the Django application (e.g., ajustar usuários, templates ou URLs), execute comandos dentro do container `paginaInicial`:

```bash
# Abrir um shell dentro do serviço Django
docker compose exec paginaInicial bash

# Rodar um manage.py (ex.: coletar arquivos estáticos)
docker compose exec paginaInicial python manage.py collectstatic --noinput
```

### Data Scraping Scripts

The data scraping scripts are designed to be run as standalone services. They typically read from and write to shared volumes or databases. When modifying these scripts, you will need to rebuild the specific service's Docker image.

```bash
# Rebuild and restart a specific service
docker-compose up --build -d <service_name>

# Example: rebuild the buscaEventos service
docker-compose up --build -d buscaEventos
```

## 3. Key Conventions and Patterns

-   **Microservice per Directory**: Each top-level directory (e.g., `buscaComissoesCD`, `paginaInicial`) represents a distinct microservice with its own `Dockerfile` and `requirements.txt`.
-   **Data Persistence**: While the Django app uses a database (SQLite in dev, PostgreSQL in prod), some services like `buscaEventos` use their own local SQLite database (`data/agendaSemana.db`) for persistence. Be mindful of where data is being stored for each service.
-   **Asynchronous Tasks**: Os scrapers (`busca*/`) executam processos longos. `buscaComissoesCD` usa Celery + Redis para agendamentos; o gateway `paginaInicial` apenas redireciona usuários para os serviços ativos.
-   **Environment Configuration**: The Django application is configured via environment variables, as documented in the root `README.md`. For local development with `docker-compose`, these are often set in the `docker-compose.yaml` file.

## 4. Frontend

The frontend is a mix of:
- Django templates localizados em `paginaInicial/templates/`.
- O portal em `paginaInicial/` serve a página de login e o grid de links, utilizando as credenciais de `paginaInicial/users/users.json`. Os perfis `admin`, `normal` e `viewer` controlam a visibilidade do menu e o acesso ao dashboard de configuração (`/configuracao`).
- A Dash application for data visualization in `buscaEventos/`.

When making frontend changes, ensure you are editing the files in the correct service directory.
