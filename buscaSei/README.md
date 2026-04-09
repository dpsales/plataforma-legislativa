# Busca de Processos SEI

Este módulo implementa a busca de processos no SEI (Sistema Eletrônico de Informações) através de pesquisa rápida pelo número do processo.

## Funcionalidades

- ✅ Busca de processos por número através da pesquisa rápida do SEI
- ✅ Extração automática de andamentos/histórico dos processos
- ✅ Armazenamento em banco de dados para consultas posteriores
- ✅ Interface web para consulta e visualização de detalhes
- 🔄 Funcionalidade de download de processos (em desenvolvimento)

## Requisitos

- Python 3.11+
- Django 5.1+
- Selenium
- Chrome/Chromium browser

## Instalação

1. Construa a imagem Docker:

```bash
docker-compose up --build -d buscasei
```

## Uso

Acesse a aplicação através de: `http://localhost:8018`

### Buscar um Processo

1. Preencha o número do processo no formulário de busca
2. A aplicação usará a pesquisa rápida do SEI para buscar o processo
3. Os andamentos serão extraídos e exibidos
4. Os dados serão armazenados para consulta posterior

## Estrutura

```
buscaSei/
├── processos/              # Aplicação Django
│   ├── models.py          # Models de Processo, Andamento, Documento
│   ├── views.py           # Views para exibir e processar dados
│   ├── forms.py           # Formulários
│   ├── services.py        # Lógica de automação Selenium
│   └── urls.py            # URLs
├── templates/             # Templates HTML
├── static/                # Arquivos estáticos
├── data/                  # Dados (banco de dados SQLite)
└── scripts/               # Scripts de inicialização
```

## API

### POST /api/busca/

Busca um processo de forma assíncrona.

**Request:**
```json
{
    "numero_processo": "00000.000000/0000-00"
}
```

**Response:**
```json
{
    "sucesso": true,
    "processo_id": 1,
    "numero_processo": "00000.000000/0000-00",
    "criado": true
}
```

## Troubleshooting

Se tiver problemas com o Selenium:

1. Verifique se há Chrome/Chromium instalado no container
2. Verifique os logs: `docker logs buscasei`
3. Ajuste as opções de Selenium em `services.py` se necessário

## Notas

- A automação usa Selenium com Chrome headless
- Os dados são armazenados em SQLite para rápido acesso
- A pesquisa é realizada em tempo real contra o servidor do SEI
