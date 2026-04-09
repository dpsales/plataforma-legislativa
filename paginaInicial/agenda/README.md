# App Agenda - paginaInicial

Funcionalidade de consolidação de agenda legislativa com dados de Câmara (API + CSV) e Senado (APIs de comissões e plenário).

## 📋 Estrutura

```
agenda/
├── models.py          # 3 modelos: EventoLegislativo, AtualizacaoProposicao, AgendaFavorita
├── views.py           # 3 views: AgendaSemanalView, AdicionarFavoritoView, RemoverFavoritoView
├── services.py        # 3 collectors: CamaraEventosCollector, SenadoEventosCollector, ProposicaoMonitoradaCollector
├── celery_tasks.py    # 3 tasks Celery: sincronizar automáticas
├── urls.py            # URLs da app
├── admin.py           # Admin customizado
├── tests.py           # Testes unitários
├── templates/agenda/  # Templates HTML (semanal, favoritos)
└── migrations/        # Migrações Django
```

## 🚀 Instalação

### 1. Dependências Python

Adicione ao `paginaInicial/requirements.txt`:

```
requests>=2.28.0
pandas>=1.5.0
celery>=5.2.0
redis>=4.3.0
```

### 2. Registrar App

O arquivo `settings.py` já foi atualizado com:
```python
INSTALLED_APPS = [
    ...
    "agenda",
]
```

### 3. Registrar URLs

O arquivo `urls.py` já foi atualizado com:
```python
urlpatterns = [
    ...
    path("agenda/", include("agenda.urls", namespace="agenda")),
]
```

### 4. Criar Migrations

```bash
cd paginaInicial
python manage.py makemigrations agenda
python manage.py migrate agenda
```

### 5. Configurar Celery (Opcional mas recomendado)

O arquivo `pagina_inicial/celery.py` já foi criado com beat schedule.

#### a) Instalar Redis (como broker)

**Mac:**
```bash
brew install redis
brew services start redis
```

**Linux:**
```bash
sudo apt-get install redis-server
sudo systemctl start redis-server
```

**Docker:**
```bash
docker run -d -p 6379:6379 redis:latest
```

#### b) Iniciar Celery Worker

```bash
cd paginaInicial
python -m celery -A pagina_inicial worker --loglevel=info
```

#### c) Iniciar Celery Beat (Scheduler)

Em outro terminal:
```bash
cd paginaInicial
python -m celery -A pagina_inicial beat --loglevel=info
```

## 🧪 Testes

### Rodar testes da app

```bash
cd paginaInicial
python manage.py test agenda
```

### Testes de sincronização manual

#### 1. Via Django Shell

```bash
cd paginaInicial
python manage.py shell
```

```python
from agenda.services import CamaraEventosCollector, SenadoEventosCollector
from datetime import date, timedelta

# Testar API Câmara
data_inicio = date.today() - timedelta(days=30)
data_fim = date.today()

eventos = CamaraEventosCollector.buscar_eventos_api(data_inicio, data_fim)
print(f"Encontrados {len(eventos)} eventos Câmara")

# Testar API Senado (Comissões)
data_com = SenadoEventosCollector.buscar_eventos_comissoes(data_inicio, data_fim)
comissoes = SenadoEventosCollector.processar_comissoes(data_com)
print(f"Encontradas {len(comissoes)} reuniões de comissões")

# Testar API Senado (Plenário)
data_ple = SenadoEventosCollector.buscar_eventos_plenario(data_inicio, data_fim)
plenario = SenadoEventosCollector.processar_plenario(data_ple)
print(f"Encontradas {len(plenario)} sessões plenárias")
```

#### 2. Via Tasks Celery

```python
from agenda.celery_tasks import sincronizar_agenda_semanal

# Rodar task sincronamente
resultado = sincronizar_agenda_semanal()
print(resultado)
# Output: {'sucesso': True, 'camara': 12, 'senado_comissoes': 5, 'senado_plenario': 2, ...}
```

## 🔗 URLs Disponíveis

| URL | View | Descrição |
|-----|------|-----------|
| `/agenda/semanal/` | AgendaSemanalView | Exibe agenda da semana anterior com filtros |
| `/agenda/favorito/adicionar/` | AdicionarFavoritoView | POST para adicionar comissão aos favoritos |
| `/agenda/favorito/remover/` | RemoverFavoritoView | POST para remover favorito |

## 📊 Models

### EventoLegislativo

```python
EventoLegislativo(
    codigo_evento: str          # ID único (ex: "EVENTO_001")
    casa: str                   # "Câmara" ou "Senado"
    titulo: str                 # Título do evento
    descricao: str              # Descrição detalhada
    tipo: str                   # VOTACAO, SESSAO, COMISSAO, PLENARIO, OUTRA
    local: str                  # Onde acontece (plenário, comissão, etc)
    comissao: str               # Nome da comissão (Senado)
    data_evento: date           # Data do evento
    hora_inicio: time           # Hora de início
    hora_fim: time              # Hora de término
    url_evento: str             # Link para detalhes
    url_transmissao: str        # Link para transmissão (Senado)
    proposicoes_relacionadas: list  # [PL 123/2024, PEC 45/2019]
)
```

### AtualizacaoProposicao

```python
AtualizacaoProposicao(
    codigo_material: str        # Ex: "PL 1234/2024"
    casa: str                   # Câmara/Senado
    tipo: str                   # PAUTA, VOTACAO, APROVACAO, REJEICAO, TRAMITACAO, etc
    descricao: str              # Detalhe da atualização
    situacao_anterior: str      # Status anterior
    situacao_atual: str         # Status novo
    data_atualizacao: datetime  # Quando mudou
    origem: str                 # buscaReqs, buscaSei, buscaMaterias, buscaComissoes
)
```

### AgendaFavorita

```python
AgendaFavorita(
    usuario: User               # FK para auth.User
    tipo: str                   # comissao_camara, comissao_senado, plenario_camara, plenario_senado
    nome: str                   # Nome da comissão/evento
    sigla: str                  # Ex: "CCJC"
)
```

## 🔄 Collectors

### CamaraEventosCollector

**Métodos:**
- `buscar_eventos_api(data_inicio, data_fim)` - API JSON
- `buscar_eventos_csv(ano)` - CSV download
- `buscar_eventos_orgaos_csv(ano)` - Eventos por órgãos
- `salvar_evento(evento_dict)` - Persistir no BD

**Exemplo:**
```python
from datetime import date
from agenda.services import CamaraEventosCollector

eventos = CamaraEventosCollector.buscar_eventos_api(
    date(2024, 1, 1), 
    date(2024, 1, 31)
)

for evt in eventos[:5]:
    evento_obj, created = CamaraEventosCollector.salvar_evento(evt)
    if created:
        print(f"Novo evento: {evento_obj.titulo}")
```

### SenadoEventosCollector

**Métodos:**
- `buscar_eventos_comissoes(data_inicio, data_fim)` - API de comissões
- `buscar_eventos_plenario(data_inicio, data_fim)` - API de plenário
- `processar_comissoes(data)` - Processar resposta
- `processar_plenario(data)` - Processar resposta
- `salvar_evento_senado(evento_dict, tipo)` - Persistir

**Exemplo:**
```python
from datetime import date
from agenda.services import SenadoEventosCollector

# Comissões
data = SenadoEventosCollector.buscar_eventos_comissoes(
    date(2024, 1, 1),
    date(2024, 1, 31)
)
eventos = SenadoEventosCollector.processar_comissoes(data)

for evt in eventos[:3]:
    evento_obj, created = SenadoEventosCollector.salvar_evento_senado(evt, 'COMISSAO')
```

## ⏰ Celery Beat Schedule

| Task | Horário | Período |
|------|---------|---------|
| sincronizar_agenda_semanal | 08:00 | Domingos |
| sincronizar_eventos_camara_diariamente | 02:00 | Diários |
| sincronizar_agenda_senado_diariamente | 03:00 | Diários |

## 📝 Integração com Página Inicial

O widget de próximos eventos já está integrado em `portal/templates/home.html`:

```html
<div class="card">
    <div class="card-header">
        <h5>Próximos Eventos</h5>
        <a href="{% url 'agenda:semanal' %}">Ver Agenda Completa</a>
    </div>
    <div class="card-body">
        {% for evento in proximos_eventos %}
            <!-- Listagem de próximos 7 dias -->
        {% endfor %}
    </div>
</div>
```

## 🐛 Troubleshooting

### "Module not found: agenda"
- Verificar se `agenda` está em `INSTALLED_APPS`
- Rodar: `python manage.py makemigrations agenda`

### "Celery tasks não rodando"
- Verificar se Redis está rodando: `redis-cli ping` → deve retornar "PONG"
- Verificar logs de Celery Worker
- Confirmar que `pagina_inicial/celery.py` foi criado

### "Erro conectando na API Câmara/Senado"
- Testar URLs manualmente (curl ou Postman)
- Verificar firewall/proxy
- Checar se a API está disponível

### "EventoLegislativo table not found"
- Rodar migrações: `python manage.py migrate agenda`

## 📚 Referências

- [Câmara API Aberta](https://dadosabertos.camara.leg.br/api/v2/)
- [Senado Dados Abertos](https://legis.senado.leg.br/dadosabertos/)
- [Celery Beat Documentation](https://docs.celeryproject.org/en/stable/userguide/periodic-tasks.html)
