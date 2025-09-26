# Módulo de Busca de Eventos (Agenda da Semana)

Este módulo é uma aplicação web desenvolvida com Dash para monitorar, consolidar e analisar a agenda de eventos legislativos da Câmara dos Deputados e do Senado Federal. Ele permite que o usuário visualize as pautas das comissões e plenários, analise as proposições e exporte relatórios formatados.

## 🌟 Funcionalidades Principais

*   **Coleta de Dados Automatizada:** Busca eventos (reuniões, sessões deliberativas, etc.) e suas respectivas pautas diretamente das APIs de dados abertos da Câmara e do Senado para um intervalo de datas selecionado.
*   **Interface Interativa:** Uma aplicação web com uma tabela de dados avançada (AG Grid) que permite:
    *   Filtrar os eventos por casa legislativa (Câmara/Senado) e tipo (Comissão/Plenário).
    *   Visualizar detalhes das proposições, incluindo ementa, autor e link para o inteiro teor.
    *   Editar e classificar as proposições manualmente quanto ao seu potencial "Impacto Fiscal".
*   **Persistência de Dados:** Armazena os dados coletados em um banco de dados SQLite (`agendaSemana.db`), permitindo que as análises manuais (como a classificação de impacto fiscal) sejam preservadas entre as atualizações.
*   **Exportação de Relatórios:** Gera relatórios customizados nos formatos:
    *   **Excel (.xlsx):** Exporta os dados exibidos na tabela.
    *   **Word (.docx):** Cria um documento formatado com a agenda da semana, agrupando as proposições por casa legislativa e comissão/plenário, ideal para distribuição e análise.

## 🏗️ Arquitetura e Tecnologias

*   **Aplicação Web:** Python, com o framework Dash para a interface de usuário.
*   **Manipulação de Dados:** Pandas para processamento e estruturação dos dados.
*   **Tabela de Dados:** `dash-ag-grid` para uma experiência de usuário rica e interativa.
*   **Banco de Dados:** SQLite para armazenamento local dos eventos e das análises.
*   **Containerização:** O serviço é projetado para ser executado em um contêiner Docker.

## 🛠️ Como Funciona

1.  **Seleção de Período:** O usuário escolhe um intervalo de datas na interface web.
2.  **Busca de Dados:** Ao clicar em "Buscar Novos Dados", a aplicação consulta as APIs da Câmara e do Senado.
3.  **Processamento e Armazenamento:** Os dados dos eventos e suas pautas são coletados, formatados e inseridos no banco de dados `agendaSemana.db`. As análises de impacto fiscal salvas anteriormente são recuperadas e mescladas com os novos dados.
4.  **Visualização e Análise:** A tabela é populada com os dados consolidados, onde o usuário pode filtrar, ordenar e editar as informações.
5.  **Exportação:** O usuário pode exportar a seleção atual para um arquivo Excel ou gerar um relatório completo em Word.

## 📄 Estrutura dos Arquivos

*   `codUnificado/codunif17.py`: O arquivo principal que contém a lógica da aplicação Dash, incluindo a coleta, o processamento e a exibição dos dados.
*   `codUnificado/data/agendaSemana.db`: O banco de dados SQLite onde os dados dos eventos são armazenados.
*   `geraSite3_dataBase.py`: Um script utilitário que pode ser usado para gerar o relatório em Word diretamente a partir do banco de dados.
*   `requirements.txt`: Lista as dependências Python necessárias para executar o módulo.
*   `dockerfile`: Arquivo de configuração para criar a imagem Docker do serviço.

## 🚀 Execução

1.  **Instale as dependências:**
    ```bash
    pip install -r requirements.txt
    pip install -r codUnificado/requirements.txt
    ```
2.  **Execute a aplicação:**
    ```bash
    python codUnificado/codunif17.py
    ```
3.  Acesse a aplicação no seu navegador, geralmente em `http://127.0.0.1:8081`.
