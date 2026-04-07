# Plataforma Legislativa de Apoio à Aspar

## Problema e Justificativa

O trabalho de uma Assessoria parlamentar envolve diversas atividades que dependem da obtenção de informações confiáveis e em tempo hábil para se tomaram as devidas providências. Dessa forma, há grande potencial em ferramentas que possibilitem a obtenção automatizada de dados, manipulação e apresentação destes dados e sua transformação em informações úteis para os usuários.

Para atender estas competências de forma tempestiva e assertiva, a ASPAR/MPO desenvolveu a Plataforma Legislativa MPO no Congresso, que objetiva facilitar o acesso aos assuntos/informações provenientes do Poder Legislativo, de interesse deste Ministério. Atualmente, a plataforma encontra-se em fase de testes, em servidor provisório, como um aplicativo conteinerizado (Docker), utilizando um ambiente gerenciado em servidor no modelo PaaS (Plataforma como Serviço). Contudo, dada a riqueza e qualidade das informações, estamos desde já disponibilizando o acesso a todas as secretarias deste Ministério. Em paralelo, desde agosto de 2025 iniciou-se a migração para ambiente fornecido pelo governo em parceria com a Dataprev/Huawei.nt
Simultaneamente, foi inciado a adaptações do código para que seja utilizado pelo pela ASPAR/MGI e adaptada para qualquer outra Assessoria Parlamentar, ou entidades que querem utilizar para obter informações sobre os assuntos parlamentares. 

## Objetivos e Resultados Esperados

Construir e manter plataforma que automatiza a busca, transformação e apresentação de dados Legislativos, além de análises de dados avançadas.

## 🌟 Funcionalidades Principais

* **Monitoramento Abrangente:** Acompanhamento contínuo das tramitações na Câmara dos Deputados, no Senado Federal e no Congresso Nacional.
* **Buscas Personalizadas:** Ferramentas de busca avançada e filtros customizáveis para encontrar proposições de interesse.
* **Análise de Dados:** Módulos para análise de votações, nuvem de palavras e classificação de proposições com uso de IA.
* **Alertas e Relatórios:** Geração de relatórios, mensagens e alertas para manter as assessorias parlamentares sempre atualizadas.
* **Interface Intuitiva:** Painel centralizado que facilita o acesso a todas as funcionalidades e informações relevantes.

## 🏗️ Arquitetura Técnica

A Plataforma Legislativa é construída sobre uma arquitetura de microserviços, projetada para ser modular, escalável e de fácil manutenção. Cada componente da plataforma opera como um serviço independente, containerizado com Docker.

A estrutura do projeto é organizada da seguinte forma:

*   **`docker-compose.yaml`**: Orquestra a inicialização e a comunicação entre os diferentes serviços da aplicação.
*   **`revProxy/`**: Atua como um proxy reverso, direcionando as requisições externas para os serviços internos apropriados, como a `paginaInicial` e as APIs de busca.
*   **`paginaInicial/`**: É o serviço de frontend da aplicação, responsável por renderizar a interface do usuário. Desenvolvido em Python com Flask/Dash, serve as páginas HTML, CSS e JavaScript aos usuários.
*   **Serviços de Backend (`basePL/`, `buscaComissoesCD/`, `buscaEventos/`, etc.)**: Cada um desses diretórios corresponde a um microserviço de backend. Eles são responsáveis por tarefas específicas, como a coleta de dados das casas legislativas, processamento e armazenamento das informações. Cada serviço possui seu próprio `Dockerfile` e `requirements.txt`, garantindo o isolamento de suas dependências.

Essa abordagem permite que cada funcionalidade da plataforma seja desenvolvida, atualizada e escalada de forma independente, sem impactar o restante do sistema.

## Funcionalidades

### Módulos Desenvolvidos e Previstos

| MÓDULO | ESCOPO | Funcionalidades desenvolvidas | Funcionalidades a desenvolver |
| --- | --- | --- | --- |
| **Agenda da Semana** | Este Módulo tem como escopo o levantamento semanal de todas as pautas e a automação da seleção das matérias a serem incluídas no Informe MPO no Congresso, mediante:<br>a) busca automatizada das pautas semanais das reunião dos Plenários da CD, SF e CN;<br>b) busca automatizada da pauta de reunião de todas as comissões temáticas, com foco nas comissões prioritárias para o MPO: CAE, CCJ e CTFC (SF), CFT, CCJC, CFFC (CD), CMO (CN). | - Busca na tela por datas<br>- Filtro por casa<br>- Filtro por Plenário / Comissão<br>- Salvamento automático das proposições já analisadas<br>- Importação de proposições já analisadas<br>- Possibilidade de editar na própria tabela<br>- Exportação em XLSX e DOCX | - Procedimentos para hospedar a nova versão no ambiente HCS/Huawei<br>- Incluir no relatório número do item da pauta<br>- Incluir coluna "Dispositivo"<br>- Incluir no checkbox congresso nacional e conferir o campo "Casa"<br>- Verificar como importar os relatórios da SE<br>Avaliar: datar a avaliação; colunas distintas para posição SE ou posição ASPAR<br>- Implementar lista de impacto fiscal padronizada (lista suspensa)<br>- Chamar o "Backup" de Lista de proposições analisadas<br>- Retirar PDL's de Radiodifusão (polui a base e o visual) |
| **Requerimentos** | Requerimentos (RICs, REQs, RQSs, INCs) apresentados nas comissões e em plenário (CD e SF), relativos a convites e/ou convocações da Ministra e de outros dirigentes do MPO, além de busca de termos-chave. | - Busca automática (de hora em hora) na Câmara e no Senado<br>- Filtro por situação atual; tipo de proposição; ano de apresentação; unidade/autoridade; assunto; casa<br>- Busca no inteiro teor do Senado<br>- Gerador de mensagem de texto | - Incluir busca no Inteiro Teor da Câmara<br>- Avaliar se inclui as proposições que já tiveram a tramitação encerrada (Senado)<br>- Ajustar ordenação da data de apresentação |
| **Matérias em Tramitação nas Comissões e no Plenário da Câmara** | Busca e apresentação das matérias prioritárias em tramitação na Câmara dos Deputados (CCJC, CFT e Plenário), identificando-se:<br>a) as que estão prontas para a pauta;<br>b)foram incluídas na pauta da reunião,<br>c) tiveram pedido de vista concedido na comissão; e,<br>d) as que estão prontas para deliberação em plenário. | - Busca automática (de 4 em 4h)<br>- Filtros por tipo; Órgão; Situação<br>- Exportação em XLSX | - Incluir rotina de backup e atualização dos PLs já analisados (importação)<br>- Incluir status: aguardando designação do relator e aguardando apresentação do relatório<br>- Implementar lista de impacto fiscal (padronizada) e campo da justificativa<br>- Incluir coluna "Dispositivo"<br>- Incluir coluna de tempo parado na Comissão<br>- Incluir busca na CFFC (CD)<br>- Avaliar: separar as comissões mais importantes (para busca mais rápida e não "poluir" a tela<br>- Integrar com a Agenda da Semana |
| **Matérias em Tramitação nas Comissões e no Plenário do Senado** | Busca e apresentação das matérias prioritárias em tramitação no Senado Federal (CCJ, CAE e Plenário), identificando-se:<br>a) as que estão prontas para a pauta;<br>b) foram incluídas na pauta da reunião,<br>c) tiveram pedido de vista concedido na comissão; e,<br>d) as que estão prontas para deliberação em plenário. | - Busca a cada requisição (ao abrir a página)<br>- Filtro por órgão; status<br>- exportação em XLSX | - Incluir busca na CTFC (SEN)<br>- Incluir rotina de backup e atualização dos PLs já analisados (importação)<br>- Incluir status: aguardando designação do relator e aguardando apresentação do relatório<br>- Implementar lista de impacto fiscal (padronizada) e campo da justificativa<br>- Incluir coluna "Dispositivo"<br>- Incluir coluna de tempo parado na Comissão<br>- Avaliar: separar as comissões mais importantes (para busca mais rápida e não "poluir" a tela<br>- Incluir título do filtro |
| **Matérias Prioritárias** | Acompanhamento da tramitação de matérias prioritárias para o MPO, selecionadas a partir de indicação das secretarias e dos projetos identificados pela ASPAR que impactam os temas e/ou as políticas públicas relacionadas às competências do Ministério. | - Atualização a cada requisição da página<br>- Filtro por casa; unidade<br>- Exportação em XLSX e DOCX<br>- Gerador de mensagem de texto | - Mecanismo de Agendamento (Scheduler) e Storage - Executar script de acompanhamento diariamente<br>- Funcionalidade do usuário adicionar ou remover um PL<br>- Verificar casos de tramitação bicameral<br>- Verificar o que fazer com as proposições transformadas em norma jurídica |
| **Busca Avançada em Proposições** | Relatório hierarquizado de proposições legislativas de interesse do MPO, construído a partir de pesquisa de termos/combinação de termos na ementa das 44.700 proposição apresentadas desde 1984 em tramitação (não arquivadas ou aprovadas).<br>A seleção é feita a partir de termos-chave, pontuação de relevância e data de tramitação recente. | - Mecanismo de agendador para atualização diária<br>- Campo de buscar na ementa<br>- Filtro por casa<br>- Exportação em XLSX | - Utilizar IA para classificar PLs de interesse do MPO<br>- Classificar em níveis de risco (3)<br>- Validar os pesos / Corrigir os pesos |
| **Página Inicial** | Tela que concentra os botões que direcionam para as funcionalidades | - Tela de login simples<br>- Inclusão de logos do MPO<br>- Diferenciação de perfis de acesso (dois perfis)<br>- Colocar botão que direciona para página com links úteis | - Verificar problema que ocorre quando aperta F5 (ele sai da página atual)<br>- Definir e inserir esquema de cores da página<br>- Implementar mecanismo de autenticação pelo próprio usuário (login e senha, com envio pela plataforma, possibilidade de alteração da senha, etc)<br>- Separar os logins e senha do código |
| **Análise de Votações** | Levantamento do perfil de votação individual de cada parlamentar desde 2023 e do grau de alinhamento com a orientação de governo. | - Votações com percentual de alinhamento da CD desde 2023<br>- Votações do SF com percentual de alinhamento desde 2024<br>- Gráfico de Gauge<br>- Alinhamento médio por estado (Deputados)<br>- Atualização diária dos dados | - Estudar novos indicadores<br>- Melhorar as cores da escala do mapa<br>- Ajustar para exportar a imagem sem a escala (ou próxima do mapa) sem a parte branca<br>- Verificar casos quando o parlamentar muda de partido (agrupar ou não) |
| **Nuvem de Palavras** | Representação gráfica dos termos mais frequentemente utilizados nos discursos dos parlamentares na tribuna da Câmara dos Deputados e do Senado Federal. | | |
| **Classificação Automatizada de Proposições** | Módulo que tem por objetivo treinar modelo de Inteligência Artificial visando identificar e classificar proposições com potencial impacto orçamentário e financeiro nas contas públicas. | | |
| **Sanção e Veto** | Acompanhamento do processo de tramitação interna no MPO da análise para sanção e/ou veto das proposições legislativas aprovadas pela Câmara, pelo Senado e pelo Congresso Nacional. | | |

### **Stack Tecnológica**
* 🖥️ **Backend:** Python, Flask, Dash, Pandas, SQLAlchemy
* 🎨 **Frontend:** HTML, CSS, JavaScript, Dash, Bootstrap
* ☁️ **Infraestrutura:** Docker, Docker Compose, Nginx, Huawei Cloud OBS

### **Estrutura do Projeto**

A estrutura do projeto é organizada da seguinte forma:

*   **`docker-compose.yaml`**: Orquestra a inicialização e a comunicação entre os diferentes serviços da aplicação.
*   **`revProxy/`**: Atua como um proxy reverso, direcionando as requisições externas para os serviços internos apropriados, como a `paginaInicial` e as APIs de busca.
*   **`paginaInicial/`**: É o serviço de frontend da aplicação, responsável por renderizar a interface do usuário. Desenvolvido em Python com Flask/Dash, serve as páginas HTML, CSS e JavaScript aos usuários.
*   **Serviços de Backend (`basePL/`, `buscaComissoesCD/`, `buscaEventos/`, etc.)**: Cada um desses diretórios corresponde a um microserviço de backend. Eles são responsáveis por tarefas específicas, como a coleta de dados das casas legislativas, processamento e armazenamento das informações. Cada serviço possui seu próprio `Dockerfile` e `requirements.txt`, garantindo o isolamento de suas dependências.

## 🚀 Guia de Instalação

### 📋 **Pré-requisitos**

*   Python 3.9+
*   Docker
*   Docker Compose

### **2️⃣ Ambiente Virtual**

É recomendado o uso de um ambiente virtual para isolar as dependências do projeto.

```bash
python -m venv venv
source venv/bin/activate
```

### **3️⃣ Instalação de Dependências**

Cada serviço possui seu próprio arquivo de dependências. Para instalar as dependências de todos os serviços, você pode executar o seguinte comando na raiz de cada serviço:

```bash
pip install -r requirements.txt
```

### **4️⃣ Configuração de Ambiente**

Crie um arquivo `.env` na raiz do projeto com as seguintes variáveis:

```env
# Exemplo de configuração para ambiente local
LOCAL_MODE=True
BUCKET_NAME=data
GCS_OBJECT_NAME=proposicoes_unificadas.xlsx
LOCAL_OUTPUT_FILE=data/proposicoes_unificadas.xlsx
DB_URL=sqlite:///data/agendaSemana.db
```

### **5️⃣ Configuração do Banco**

Alguns serviços podem necessitar de um banco de dados. A configuração da conexão com o banco de dados deve ser especificada na variável `DB_URL` no arquivo `.env`.

### **6️⃣ Execução do Sistema**

Para iniciar todos os serviços da plataforma, utilize o Docker Compose:

```bash
docker-compose up --build
```

# 📚 Uso do Sistema

Acesse a plataforma através do seu navegador no endereço `http://localhost:8080`.

### **🔐 Autenticação**

A plataforma possui uma tela de login simples com dois perfis de acesso.

## 🔧 APIs Disponíveis

A plataforma expõe diversas APIs para a coleta e atualização de dados. O acesso a essas APIs é gerenciado pelo proxy reverso.

## 🌐 Deploy em Produção

### **🐳 Docker**

Para fazer o deploy da aplicação em produção, você pode construir as imagens Docker de cada serviço e publicá-las em um registro de contêineres.

```bash
docker-compose build
docker-compose push
```

### **☸️ Kubernetes**

A aplicação pode ser implantada em um cluster Kubernetes. No entanto, os arquivos de configuração para o Kubernetes não estão incluídos neste repositório.
