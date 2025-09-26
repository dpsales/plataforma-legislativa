# Estrutura do Módulo `codUnificado`

Este diretório contém o código-fonte e os recursos essenciais para o funcionamento do **Módulo de Busca de Eventos (Agenda da Semana)**.

## Visão Geral

A aplicação principal, `codunif17.py`, é um painel de controle (dashboard) desenvolvido em Dash que busca, exibe e permite a análise de eventos legislativos. Os dados são armazenados em um banco de dados SQLite para persistência e as análises manuais são preservadas através de um mecanismo de backup.

## Estrutura dos Arquivos e Diretórios

*   **`codunif17.py`**: Coração da aplicação. Este script Python contém toda a lógica do dashboard Dash, incluindo:
    *   A interface do usuário (layout).
    *   As rotinas para buscar dados das APIs da Câmara e do Senado.
    *   O processamento e a formatação dos dados para exibição.
    *   A interação com o banco de dados SQLite para leitura e escrita.
    *   As funcionalidades de exportação para Excel e Word.

*   **`data/`**: Diretório que armazena os dados persistentes da aplicação.
    *   `agendaSemana.db`: O banco de dados SQLite que contém as tabelas `eventos` (com os dados da agenda) e `backup_pl` (com as análises manuais de impacto fiscal).

*   **`assets/`**: Contém arquivos estáticos que são automaticamente servidos pelo Dash.
    *   `dashAgGridComponentFunctions.js`: Funções JavaScript customizadas para a tabela AG Grid, como a renderização de links em Markdown.
    *   `markdown_link_renderer.js`: Componente específico para renderizar links formatados na tabela.

*   **`BackupPL.xlsx`**: Uma planilha Excel utilizada como fonte de dados para o backup das análises de impacto fiscal. Pode ser usada para uma carga inicial ou para atualizações em lote.

*   **`carga_inicial_backup_pl.py`** e **`carga_atualizacao_backup_pl.py`**: Scripts de utilidade para popular ou atualizar a tabela `backup_pl` no banco de dados a partir do arquivo `BackupPL.xlsx`. Eles garantem que as análises manuais feitas sobre as proposições não se percam quando a base de eventos é atualizada.

*   **`dicionarioDados.xlsx`**: Documento que provavelmente descreve as colunas e os tipos de dados utilizados no banco de dados e na aplicação (dicionário de dados).

*   **`requirements.txt`**: Lista as bibliotecas Python necessárias para que a aplicação funcione corretamente.

*   **`Dockerfile`**: Arquivo de configuração que permite criar uma imagem Docker da aplicação, facilitando o deploy em ambientes de contêineres como o Google Cloud Run.

*   **`mynotes.txt`**: Um arquivo de anotações do desenvolvedor, contendo exemplos de comandos `gcloud` para deploy e notas sobre a evolução do esquema de dados (nomes de colunas).

*   **`DB.Browser.for.SQLite-v3.13.1-win64/`**: Uma cópia do aplicativo "DB Browser for SQLite" para Windows, uma ferramenta útil para inspecionar e gerenciar o banco de dados `agendaSemana.db` diretamente.
