# Busca Matérias Prioritárias (Django)

Este serviço expõe, em formato web, a lista de proposições prioritárias acompanhadas pelo time, permitindo filtros, exportação e gerenciamento da fonte JSON de monitoramento.

## Estrutura

- `monitoramento/` – aplicativo Django com models, serviços de coleta e views.
- `scripts/start-web.sh` – script de inicialização utilizado no container (migrações, coleta de estáticos e sincronização opcional).
- `proposicoes_ids.json` – exemplo de documento de entrada a ser importado (opcional).

## Configuração local

```bash
# instalar dependências
pip install -r requirements.txt

# aplicar migrações
django-admin migrate --settings=busca_materias.settings

# carregar documento inicial (opcional)
django-admin import_document proposicoes_ids.json --settings=busca_materias.settings

# executar sincronização com as APIs oficiais
django-admin sync_proposicoes --settings=busca_materias.settings

# iniciar servidor de desenvolvimento
python manage.py runserver 0.0.0.0:8080
```

## Fluxo de operação

1. Importe um documento JSON (pela interface `/configurar/` ou via comando `import_document`).
2. Execute `sync_proposicoes` para buscar dados atualizados nas APIs da Câmara e do Senado.
3. A listagem em `/` permite filtrar por casa, secretaria, prioridade e texto, além de exportar planilhas e relatórios.
4. Usuários com perfil **admin** ou **normal** podem adicionar ou remover proposições manualmente; perfis **viewer** apenas consomem a listagem.
