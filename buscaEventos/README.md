# Módulo de Busca de Eventos (Agenda da Semana)

O serviço de Agenda da Semana agora é uma aplicação Django que consolida os eventos legislativos publicados pela Câmara dos Deputados e Senado Federal. O catálogo completo de proposições fica disponível para consulta e os perfis **admin** e **normal** podem definir quais itens devem ser monitorados continuamente.

## 🌟 Funcionalidades Principais

*   **Catálogo unificado:** estrutura tabelada (`agenda_proposition`, `agenda_event`) com todas as proposições encontradas nas pautas.
*   **Seleção de monitoramento:** interface web dedicada para que operadores indiquem prioridades, destaques e observações, replicando o fluxo antes realizado no Dash.
*   **Histórico de tramitação:** tabela `agenda_tramitacao` preparada para armazenar a linha do tempo das proposições monitoradas.
*   **Importação do legado:** comando `import_agenda_snapshot` importa o banco SQLite `agendaSemana.db` criado pelo antigo `codunif17.py`, preservando as marcações existentes.

## 🏗️ Arquitetura e Tecnologias

*   **Aplicação Web:** Django 5 + Bootstrap (templates server-side).
*   **Dados:** Banco SQLite por padrão (configurável via `DATABASE_URL`).
*   **Agendamento:** O módulo `agenda.services.sync` oferece utilitários para sincronizar novos dados coletados via scripts ou tarefas Celery/APScheduler.
*   **Containerização:** Docker com Gunicorn + WhiteNoise, alinhado aos demais microserviços da plataforma.

## 🛠️ Fluxo Básico

1.  Execute as migrações (`python manage.py migrate`).
2.  Opcional: importe o snapshot legado executando `python manage.py import_agenda_snapshot`.
3.  Acesse `/busca-eventos/` para ver o painel e `/busca-eventos/gerenciar/` (perfis admin/normal) para ajustar os monitoramentos.

## 📄 Estrutura Atualizada

*   `busca_eventos/`: configurações do projeto Django.
*   `agenda/`: app com models, views, forms e serviços de sincronização.
*   `agenda/management/commands/import_agenda_snapshot.py`: comando para migrar o banco SQLite legado.
*   `templates/agenda/`: páginas HTML da listagem e da tela de gerenciamento.
*   `codUnificado/`: diretório original preservado como referência histórica (não é mais executado pelo container).

## 🚀 Execução Local

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py import_agenda_snapshot  # opcional
python manage.py runserver 0.0.0.0:8080
```

O serviço fica disponível em `http://localhost:8080/busca-eventos/` quando executado junto ao `docker-compose` da plataforma.
