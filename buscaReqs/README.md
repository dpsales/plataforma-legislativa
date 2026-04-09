# Busca de Requerimentos

Módulo Django que coleta, armazena e exibe requerimentos de interesse da Câmara e Senado.

## Funcionalidades

✅ Consulta APIs da Câmara e Senado  
✅ Filtra requerimentos por termos configuráveis  
✅ Armazena em banco SQLite  
✅ Interface web com tabela responsiva  
✅ Configuração dinâmica de filtros  
✅ Admin Django para gerenciamento  

## Instalação Rápida

```bash
# 1. Construir a imagem Docker
docker-compose up --build -d buscareqs

# 2. Acessar em: http://localhost:8015
```

## Uso

### Teste Rápido com Dados de Exemplo

```bash
# Popula a base com dados de teste
docker-compose exec buscareqs python manage.py seed_requerimentos

# Agora acesse http://localhost:8015 para ver os dados
```

### Importar Requerimentos de um CSV ou Excel

Os dados de entrada podem vir de buscaReqs/proposicoesAutores_csv (autores) ou de um arquivo
CSV/XLSX com as colunas completas. O importador reconhece automaticamente o formato.

```bash
# Dentro do container
docker-compose exec buscareqs python manage.py import_requerimentos_csv proposicoesAutores_csv/proposicoesAutores-2025.csv

# Excel (.xlsx)
docker-compose exec buscareqs python manage.py import_requerimentos_csv dados.xlsx --sheet "Planilha1"

# Ou com limpeza prévia
docker-compose exec buscareqs python manage.py import_requerimentos_csv proposicoesAutores_csv/proposicoesAutores-2025.csv --clear

# Com delimitador diferente (CSV)
docker-compose exec buscareqs python manage.py import_requerimentos_csv dados.csv --delimiter ","
```

### Executar o Script de Coleta

O script `buscaReqs15.py` coleta dados das APIs do Congresso:

```bash
# Dentro do container
docker-compose exec buscareqs python buscaReqs15.py --api --timeout 45

# Com multiple opções
docker-compose exec buscareqs python buscaReqs15.py \
    --api \
    --from-sqlite \
    --start 2024-01-01 \
    --end 2025-12-31 \
    --verbose
```

### Configurar Filtros

1. Acesse o painel em http://localhost:8015
2. Clique em "Configurar filtros"
3. Selecione:
   - Tipos de proposição (REQ, RIC, INC, etc.)
   - Anos de apresentação
   - Unidades/Cargos monitorados
   - Assuntos priorizados

## Estrutura

```
buscaReqs/
├── requisicoes/              # App Django
│   ├── models.py            # Configuration e Requerimento
│   ├── views.py             # Views da aplicação
│   ├── admin.py             # Admin Django
│   ├── importador.py        # Importador de dados
│   ├── management/commands/ # Comandos Django
│   └── forms.py             # Formulários
├── templates/               # Templates HTML
├── buscaReqs15.py          # Script de coleta de dados
├── proposicoesAutores_csv/ # Dados em CSV
└── data/                    # Banco SQLite
```

## API

### `Configuration` Model

Armazena a configuração de filtros aplicados.

```python
Configuration.load()  # Carrega configuração padrão
```

### `Requerimento` Model

Representa um requerimento ou proposição.

```python
Requerimento.objects.filter(casa='Câmara')
Requerimento.objects.filter(data_apresentacao__year=2025)
```

### ImportadorRequerimentos

Classe utilitária para importar dados:

```python
from requisicoes.importador import ImportadorRequerimentos

# Importar um requerimento
prop_dict = {...}
ImportadorRequerimentos.from_proposition(prop_dict)

# Importar lista
propositions = [...]
criados, atualizados = ImportadorRequerimentos.from_propositions(propositions)

# Limpar antigos (90+ dias)
ImportadorRequerimentos.limpar_antigos(dias=90)
```

## Campos do Requerimento

- `titulo`: Título da proposição
- `autor`: Autor/Autores
- `ementa`: Resumo da proposição
- `situacao`: Situação atual (aprovado, em tramitação, etc.)
- `data_apresentacao`: Data que foi apresentado
- `data_ultima_tramitacao`: Última movimentação
- `casa`: Câmara ou Senado
- `termos_encontrados`: Termos de interesse encontrados
- `assuntos_encontrados`: Assuntos relacionados
- `link_ficha`: Link para ficha técnica
- `link_inteiro_teor`: Link para texto completo

## Troubleshooting

### Nenhum requerimento aparece

1. Verifique se há dados no banco: `docker-compose exec buscareqs python manage.py shell`
   ```python
   from requisicoes.models import Requerimento
   Requerimento.objects.count()
   ```

2. Execute o script de coleta: `python buscaReqs15.py --api`

3. Ou importe um CSV: `python manage.py import_requerimentos_csv arquivo.csv`

### Erro ao importar CSV

- Verifique se o delimitador está correto (padrão: `;`)
- Confirme que as colunas estão nomeadas corretamente
- Veja os logs: `docker logs buscareqs`

### Dados desatualizados

Execute periodicamente (via cron ou container):
```bash
docker-compose exec buscareqs python buscaReqs15.py --api --from-sqlite
```

## Performance

Para melhor performance com grandes volumes:

1. **Indexação**: Os campos principais já possuem índices
2. **Paginação**: Implemente paginação no template se > 1000 registros
3. **Cache**: Use Django cache para listagem frequente
4. **Coleta assíncrona**: Considere Celery para coleta em background

## Notas

- O campo `codigo_material` é único e evita duplicatas
- Registros são marcados com `data_atualizacao` automática
- O admin Django permite busca e filtro avançado
