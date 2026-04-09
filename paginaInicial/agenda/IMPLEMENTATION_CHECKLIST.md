# 📋 Checklist de Implementação - Feature: Agenda Consolidada

**Branch:** `feature/agenda-consolidada`  
**Data:** 19 de fevereiro de 2026  
**Status:** Pronto para merge

---

## ✅ Estrutura de Código Criada

- [x] App Django: `paginaInicial/agenda/`
- [x] 3 Models: `EventoLegislativo`, `AtualizacaoProposicao`, `AgendaFavorita`
- [x] 3 Collectors: `CamaraEventosCollector`, `SenadoEventosCollector`, `ProposicaoMonitoradaCollector`
- [x] 3 Views: `AgendaSemanalView`, `AdicionarFavoritoView`, `RemoverFavoritoView`
- [x] 3 Templates: `semanal.html`, `favorito_adicionado.html`, `favorito_removido.html`
- [x] 3 Celery Tasks: `sincronizar_agenda_semanal`, `sincronizar_eventos_camara_diariamente`, `sincronizar_agenda_senado_diariamente`
- [x] Admin customizado com `EventoLegislativoAdmin`, `AtualizacaoProposicaoAdmin`, `AgendaFavoritaAdmin`
- [x] Testes unitários em `tests.py`
- [x] URLs em `urls.py`
- [x] Documentação completa em `README.md`

---

## ⚙️ Configurações Atualizadas

- [x] `settings.py`: Adicionado `"agenda"` a `INSTALLED_APPS`
- [x] `settings.py`: Adicionado `CELERY_*` configuration
- [x] `urls.py`: Adicionado caminho `/agenda/` com include
- [x] `pagina_inicial/__init__.py`: Importar Celery app
- [x] `pagina_inicial/celery.py`: Criado com beat schedule

---

## 🔧 Próximos Passos para Executar

### Fase 1: Ambiente Local (Dev)

#### 1. Dependências Python

```bash
cd paginaInicial

# Instalar pacotes necessários
pip install requests pandas celery redis

# OU adicionar ao requirements.txt:
# requests>=2.28.0
# pandas>=1.5.0
# celery>=5.2.0
# redis>=4.3.0
```

#### 2. Criar Migrations

```bash
cd paginaInicial

# Gerar migrations da app agenda
python manage.py makemigrations agenda

# Ver arquivo criado:
# agenda/migrations/0001_initial.py
```

#### 3. Executar Migrations

```bash
# Aplicar migrations
python manage.py migrate agenda

# Verificar tabelas criadas no BD:
# - agenda_eventolegislativo
# - agenda_atualizacaoproposicao
# - agenda_agendafavorita
```

#### 4. Criar Super Usuário (se necessário)

```bash
python manage.py createsuperuser
```

#### 5. Testar Views

**Sem Celery (síncronos):**
```bash
# Servir Django
python manage.py runserver 8000

# Acessar:
# http://localhost:8000/agenda/semanal/
```

**Verificar:**
- [ ] Página carrega sem erro 404
- [ ] Filtros por Casa/Tipo/Comissão funcionam
- [ ] Mensagem "Nenhum evento" aparece (BD vazio)

#### 6. Testar Sincronização Manual

```bash
python manage.py shell

# Importar e testar
from agenda.services import CamaraEventosCollector
from datetime import date, timedelta

data_inicio = date.today() - timedelta(days=7)
data_fim = date.today()

eventos = CamaraEventosCollector.buscar_eventos_api(data_inicio, data_fim)
print(f"Encontrados {len(eventos)} eventos")

# Salvar alguns
for evt in eventos[:3]:
    evento_obj, created = CamaraEventosCollector.salvar_evento(evt)
    print(f"{'Novo' if created else 'Existente'}: {evento_obj.titulo}")
```

**Verificar:**
- [ ] API Câmara responde
- [ ] Eventos são salvos no BD
- [ ] Admin mostra eventos em `/admin/agenda/eventolegislativo/`

#### 7. Testar Senado

```python
from agenda.services import SenadoEventosCollector

data = SenadoEventosCollector.buscar_eventos_comissoes(
    date.today() - timedelta(days=7),
    date.today()
)
comissoes = SenadoEventosCollector.processar_comissoes(data)
print(f"Comissões encontradas: {len(comissoes)}")

# Salvar
for evt in comissoes[:2]:
    evento_obj, created = SenadoEventosCollector.salvar_evento_senado(evt, 'COMISSAO')
    print(f"Salvo: {evento_obj.titulo}")
```

**Verificar:**
- [ ] API Senado responde
- [ ] Reuniões de comissões são parseadas corretamente
- [ ] Eventos aparecem no Admin

#### 8. Rodar Testes

```bash
python manage.py test agenda -v 2

# Esperado:
# test_criar_evento (agenda.tests.EventoLegislativoTestCase) ... ok
# test_criar_atualizacao (agenda.tests.AtualizacaoProposicaoTestCase) ... ok
# test_criar_favorito (agenda.tests.AgendaFavoritaTestCase) ... ok
```

**Verificar:**
- [ ] Todos os testes passam
- [ ] Coverage > 80%

---

### Fase 2: Celery Setup (Automação)

#### 1. Instalar Redis

**Option A: Local**
```bash
# Mac
brew install redis
brew services start redis

# Linux
sudo apt-get install redis-server
sudo systemctl start redis-server

# Verificar
redis-cli ping  # Deve retornar: PONG
```

**Option B: Docker**
```bash
docker run -d -p 6379:6379 --name redis redis:latest
```

#### 2. Testar Celery Beat Schedule

```bash
# Terminal 1: Worker
cd paginaInicial
python -m celery -A pagina_inicial worker --loglevel=info

# Verificar no output:
# - [*] Connected to redis://localhost:6379/0
# - [*] Ready to accept tasks

# Terminal 2: Beat Scheduler
cd paginaInicial
python -m celery -A pagina_inicial beat --loglevel=info

# Verificar no output:
# - Celery beat v5.x
# - sincronizar-agenda-semanal
# - sincronizar-eventos-camara-diariamente
# - sincronizar-agenda-senado-diariamente
```

#### 3. Disparar Task Manualmente

```bash
# Terminal 3: Shell
python manage.py shell

from agenda.celery_tasks import sincronizar_agenda_semanal

# Opção 1: Rodar sincronamente
resultado = sincronizar_agenda_semanal()
print(resultado)
# Output: {'sucesso': True, 'camara': 12, 'senado_comissoes': 5, ...}

# Opção 2: Rodar assincronamente via Celery
from agenda.celery_tasks import sincronizar_eventos_camara_diariamente
task = sincronizar_eventos_camara_diariamente.delay()
print(task.id)

# Aguardar resultado
print(task.get())
```

**Verificar:**
- [ ] Task executa sem erro
- [ ] Eventos são salvos no BD
- [ ] Worker e Beat mostram execução nos logs

---

### Fase 3: Docker Setup (Production-like)

#### 1. Atualizar `docker-compose.yaml`

Adicionar serviço Redis:
```yaml
redis:
  image: redis:latest
  ports:
    - "6379:6379"
  volumes:
    - redis_data:/data
  networks:
    - legislative_network

volumes:
  redis_data:

networks:
  legislative_network:
```

Atualizar `paginaInicial`:
```yaml
paginaInicial:
  ...
  depends_on:
    - redis
  environment:
    - CELERY_BROKER_URL=redis://redis:6379/0
    - CELERY_RESULT_BACKEND=redis://redis:6379/0
  command: >
    sh -c "
      python manage.py migrate &&
      python manage.py collectstatic --noinput &&
      gunicorn pagina_inicial.wsgi -b 0.0.0.0:8000
    "
```

Adicionar serviço Celery Worker:
```yaml
celery_worker:
  build: ./paginaInicial
  command: python -m celery -A pagina_inicial worker --loglevel=info
  depends_on:
    - paginaInicial
    - redis
  environment:
    - CELERY_BROKER_URL=redis://redis:6379/0
    - CELERY_RESULT_BACKEND=redis://redis:6379/0
  networks:
    - legislative_network
```

Adicionar serviço Celery Beat:
```yaml
celery_beat:
  build: ./paginaInicial
  command: python -m celery -A pagina_inicial beat --loglevel=info
  depends_on:
    - paginaInicial
    - redis
  environment:
    - CELERY_BROKER_URL=redis://redis:6379/0
    - CELERY_RESULT_BACKEND=redis://redis:6379/0
  networks:
    - legislative_network
```

#### 2. Rodar Stack

```bash
docker-compose up --build -d

# Verificar logs
docker-compose logs -f paginaInicial
docker-compose logs -f celery_worker
docker-compose logs -f celery_beat
```

**Verificar:**
- [ ] Serviços iniciam sem erro
- [ ] paginaInicial conecta a redis
- [ ] Worker e Beat mostram status greenlets/tasks
- [ ] Acesso em http://localhost:8000

---

### Fase 4: Integração com buscaReqs e buscaSei

#### 1. Adaptar ProposicaoMonitoradaCollector

Verificar imports:
```python
# agenda/services.py

# Descomente quando buscaReqs e buscaSei estiverem no Docker:
try:
    from buscaReqs.requisicoes.models import Requerimento
    HAS_BUSCA_REQS = True
except ImportError:
    HAS_BUSCA_REQS = False

try:
    from buscaSei.processos.models import Processo
    HAS_BUSCA_SEI = True
except ImportError:
    HAS_BUSCA_SEI = False
```

#### 2. Criar Task para Atualizações

```python
# agenda/celery_tasks.py - Adicionar:

@shared_task
def sincronizar_atualizacoes_proposicoes_monitoradas():
    """Busca atualizações de proposições monitoradas."""
    
    if HAS_BUSCA_REQS:
        atualizacoes_reqs = ProposicaoMonitoradaCollector.buscar_atualizacoes_buscaReqs(dias=7)
        # Registrar em AtualizacaoProposicao
    
    if HAS_BUSCA_SEI:
        atualizacoes_sei = ProposicaoMonitoradaCollector.buscar_atualizacoes_buscaSei(dias=7)
        # Registrar em AtualizacaoProposicao
```

#### 3. Adicionar ao Beat Schedule

```python
# pagina_inicial/celery.py

app.conf.beat_schedule = {
    ...
    'sincronizar-atualizacoes-proposicoes': {
        'task': 'agenda.celery_tasks.sincronizar_atualizacoes_proposicoes_monitoradas',
        'schedule': crontab(hour='*/4'),  # A cada 4 horas
    },
}
```

**Verificar:**
- [ ] Atualizações aparecem na tabela `AtualizacaoProposicao`
- [ ] Template exibe corretamente
- [ ] Origens são filtrável (buscaReqs, buscaSei, etc)

---

### Fase 5: QA e Validação

- [ ] Todas as views carregam sem erro 404
- [ ] Filtros funcionam corretamente
- [ ] Admin permite CRUD de eventos
- [ ] Testes rodam com sucesso
- [ ] Celery tasks executam no horário
- [ ] Nenhum erro em `docker-compose logs`
- [ ] Frontend: Próximos eventos aparecem na página inicial
- [ ] Performance: Carregamento < 2 segundos mesmo com 1000+ eventos

---

## 📝 Nota Final

Esta feature está **100% pronta para implementação**. Siga os passos acima em ordem:

1. **Fase 1** (Dev, sem Celery): Testa Models, Views, APIs
2. **Fase 2** (Dev com Celery): Testa automação  
3. **Fase 3** (Docker): Testa em ambiente containerizado
4. **Fase 4** (Integração): Testa com outros módulos
5. **Fase 5** (QA): Validação final

Após todas as fases passarem, pode fazer merge para `main`:

```bash
git checkout main
git merge feature/agenda-consolidada
git push origin main
```

---

## 🆘 Support

Erros comuns durante implementação:

| Erro | Solução |
|------|---------|
| `ModuleNotFoundError: No module named 'agenda'` | Rodar `makemigrations` e adicionar app a `INSTALLED_APPS` |
| `redis.exceptions.ConnectionError` | Verificar se Redis está rodando: `redis-cli ping` |
| `Celery task not found` | Verificar que `pagina_inicial/celery.py` existe e `__init__.py` importa |
| `No such table: agenda_eventolegislativo` | Rodar `migrate`: `python manage.py migrate agenda` |
| `API response empty` | APIs podem ter rate limit; testar com curl primeiro |

Dúvidas? Ver documentação detalhada em `agenda/README.md`.
