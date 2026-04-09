import os
import time
import logging
import getpass
import pandas as pd
import base64
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- 1. CONFIGURAÇÕES GERAIS ---

# Defina as pastas onde os arquivos serão salvos
PASTA_DOCUMENTOS_HTML = "documentos_mps_html"
PASTA_LISTAS_ARQUIVOS = "listas_de_arquivos_mps"
ARQUIVO_LOG = "automacao_sei.log"

# URL do SEI
URL_SEI = 'https://colaboragov.sei.gov.br/sip/modulos/MF/login_especial/login_especial.php?sigla_orgao_sistema=MGI&sigla_sistema=SEI'

def configurar_logging():
    """Configura o sistema de logging para registrar eventos em um arquivo e no console."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(ARQUIVO_LOG, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

def criar_pastas():
    """Garante que os diretórios de saída existam."""
    os.makedirs(PASTA_DOCUMENTOS_HTML, exist_ok=True)
    os.makedirs(PASTA_LISTAS_ARQUIVOS, exist_ok=True)
    logging.info(f"Pastas de saída '{PASTA_DOCUMENTOS_HTML}' e '{PASTA_LISTAS_ARQUIVOS}' estão prontas.")

# --- 2. FUNÇÕES DE AUTOMAÇÃO (SELENIUM) ---

def realizar_login(driver, url, usuario, senha, orgao):
    """
    Realiza o login no sistema SEI.

    Args:
        driver: Instância do WebDriver.
        url (str): URL do sistema SEI.
        usuario (str): Nome de usuário.
        senha (str): Senha.
        orgao (str): Sigla do órgão.

    Returns:
        bool: True se o login for bem-sucedido, False caso contrário.
    """
    try:
        logging.info(f"Acessando a página de login: {url}")
        driver.get(url)

        # Usar WebDriverWait para garantir que os elementos estejam prontos
        wait = WebDriverWait(driver, 10)
        
        logging.info("Preenchendo formulário de login.")
        wait.until(EC.presence_of_element_located((By.ID, 'txtUsuario'))).send_keys(usuario)
        wait.until(EC.presence_of_element_located((By.ID, 'pwdSenha'))).send_keys(senha)
        wait.until(EC.presence_of_element_located((By.ID, 'selOrgao'))).send_keys(orgao)
        
        acessar = driver.find_element(By.XPATH, '//*[@id="Acessar"]')
        acessar.click()
        wait = WebDriverWait(driver, 10)

        # Verifica se o login foi bem-sucedido procurando por um elemento da página principal
        # wait.until(EC.presence_of_element_located((By.ID, id ="lnkInfraMenuSistema")))
        logging.info("Login realizado com sucesso!")
        return True
        
    # except TimeoutException:
    #     logging.error("Falha no login: A página demorou muito para carregar ou um elemento não foi encontrado.")
    #     return False
    except Exception as e:
        logging.error(f"Erro inesperado durante o login: {e}")
        return False

def executar_busca(driver):
    """
    Navega até a tela de pesquisa e executa a busca com os critérios definidos.

    Args:
        driver: Instância do WebDriver.
    
    Returns:
        bool: True se a busca for executada, False caso contrário.
    """
    try:
        logging.info("Iniciando o processo de busca de documentos.")
        wait = WebDriverWait(driver, 5)

        # Acessa a área de busca
        searching = driver.find_element(By.XPATH, '//*[@id="infraMenu"]/li[14]/a/span')
        searching.click()
        time.sleep(1)

        # Preenche o formulário de busca
        logging.info("Preenchendo os critérios de busca.")

        # Restringe busca ao órgão específico
        sel_orgao = driver.find_element(By.XPATH, '//*[@id="divSinRestringirOrgao"]/div')
        sel_orgao.click()
        time.sleep(1)

        # Especifica os termos de pesquisa
        espec_pesq = driver.find_element(By.XPATH, '//*[@id="q"]')
        espec_pesq.send_keys('MPS não "SIC" não "Ficha" não "Nota Fiscal" não "REQUERIMENTO DE DISPENSA" não "Termo de Responsabilidade" não "Capacitação" não "Avaliação de Reação" não "Controle de Acesso" não "de Cessão" não "ANUÊNCIA" não "Neopostismo"')
        wait 

        #colocar como tramitação dentro do orgão
        chktram = driver.find_element(By.XPATH, '//*[@id="divSinTramitacao"]/div')
        chktram.click()
        time.sleep(1)
        
        
        # colocar as datas
        data_inicio = driver.find_element(By.XPATH, '//*[@id="txtDataInicio"]')
        data_inicio.clear()
        data_inicio.send_keys('30/07/2024')
        data_fim = driver.find_element(By.XPATH, '//*[@id="txtDataFim"]')
        data_fim.clear()
        data_fim.send_keys(datetime.now().strftime('%d/%m/%Y'))


        # Clica no botão de pesquisar
        b_pesq = driver.find_element(By.XPATH, '//*[@id="sbmPesquisar"]')
        b_pesq.click()
        
        # Aguarda a tabela de resultados aparecer
        wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="conteudo"]/table')))
        logging.info("Busca realizada com sucesso.")
        return True

    except TimeoutException:
        logging.error("Falha na busca: A página demorou muito para carregar ou um elemento não foi encontrado.")
        # return False
    except Exception as e:
        logging.error(f"Erro inesperado durante a busca: {e}")
        # return False


def extrair_dados(driver):
    """
    Extrai dados da página atual do SEI.
    """
    def remove_items(lista, item): 
        return [i for i in lista if i != item]

    tree_elements = driver.find_elements(By.XPATH, '//*[@class="pesquisaTituloEsquerda"]/a')
    list_tree = [element.text for element in tree_elements]
    trees = remove_items(list_tree, '')

    abts = driver.find_elements(By.XPATH, '//*[@class="pesquisaSnippet"]')
    list_abts = [element.text for element in abts]

    unidades = driver.find_elements(By.XPATH, '//*[@class="pesquisaMetatag"]')
    list_uni = [element.text.split(':') for element in unidades]
    info = [sub[1].strip() for sub in list_uni if len(sub) > 1]

    rows = driver.find_elements(By.XPATH, '//*[@id="conteudo"]/table/tbody/tr')
    links = []
    for i in range(1, len(rows), 3):
        try:
            # CAPTURA O LINK (string) ANTES DE MEXER EM ABA
            link_element = driver.find_element(By.XPATH, f'//*[@id="conteudo"]/table/tbody/tr[{i}]/td[1]/a[1]')
            link = link_element.get_attribute('href')
            links.append(link)

            # PREPARA O NOME DO PDF
            idx = len(links)
            nome_documento = trees[2*(idx-1)+1] if 2*(idx-1)+1 < len(trees) else f"doc_sem_nome_{idx}"
            nome_base = f"{idx:03d}_{nome_documento}".replace('/', '-')
            nome_limpo = "".join(c for c in nome_base if c.isalnum() or c in " _-").rstrip()
            caminho_pdf = os.path.join(PASTA_DOCUMENTOS_HTML, f"{nome_limpo}.pdf")

            # SALVA O PDF COM LINK DIRETO
            salvar_documento_como_pdf(driver, link, caminho_pdf)
            time.sleep(2)

        except Exception as e:
            logging.warning(f"Erro ao extrair ou baixar documento da linha {i}: {e}")
            links.append(None)

    dados = {
        "Número do Processo": trees[::2],
        "Documento": trees[1::2],
        "Resumo": list_abts,
        "Unidade": info[::3],
        "Usuário": info[1::3],
        "Data de Inclusão": info[2::3],
        "Link Completo": links
    }

    return pd.DataFrame(dados)


def navegar_paginas(driver, caminho_csv):
    """
    Navega por todas as páginas de resultado e salva os dados em CSV.
    """
    logging.info("Iniciando navegação pelas páginas de resultados.")
    dados_consolidados = pd.DataFrame()
    pagina = 1

    while True:
        logging.info(f"Extraindo dados da página {pagina}")
        df_pagina = extrair_dados(driver)
        dados_consolidados = pd.concat([dados_consolidados, df_pagina], ignore_index=True)

        try:
            proxima = driver.find_element(By.XPATH, "//a[text()='Próxima']")
            href = proxima.get_attribute('href')
            if not href:
                break
            proxima.click()
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="conteudo"]/table'))
            )
            pagina += 1
        except NoSuchElementException:
            logging.info("Não há mais páginas.")
            break
        except Exception as e:
            logging.error(f"Erro durante a navegação: {e}")
            break

    logging.info(f"Salvando dados extraídos em: {caminho_csv}")
    dados_consolidados.to_csv(caminho_csv, sep=';', encoding='utf-8-sig', index=False)
    logging.info("CSV salvo com sucesso.")


def salvar_documento_como_pdf(driver, url, nome_arquivo_pdf):
    """
    Abre o link do documento e salva como PDF usando o protocolo DevTools.
    """
    try:
        driver.get(url)
        time.sleep(5)  # Aguarda o carregamento

        # Acessa o protocolo DevTools
        result = driver.execute_cdp_cmd("Page.printToPDF", {
            "printBackground": True,
            "paperWidth": 8.27,  # A4 em polegadas
            "paperHeight": 11.69,
            "scale": 1
        })

        # Decodifica e salva o PDF
        with open(nome_arquivo_pdf, "wb") as f:
            f.write(base64.b64decode(result['data']))
        logging.info(f"Documento salvo como PDF: {nome_arquivo_pdf}")

    except Exception as e:
        logging.error(f"Erro ao salvar PDF '{nome_arquivo_pdf}': {e}")


def baixar_documentos_em_pdf(driver, caminho_csv):
    """
    Lê os links do CSV gerado e salva cada documento como PDF.
    """
    df = pd.read_csv(caminho_csv, sep=';', encoding='utf-8')
    total = len(df)

    for idx, row in df.iterrows():
        nome_base = f"{idx+1:03d}_{row['Documento']}".replace('/', '-')
        nome_limpo = "".join(c for c in nome_base if c.isalnum() or c in " _-").rstrip()
        caminho_pdf = os.path.join(PASTA_DOCUMENTOS_HTML, f"{nome_limpo}.pdf")
        link = row['Link Completo']

        if pd.isna(link):
            logging.warning(f"Link vazio para documento {idx}. Pulando.")
            continue

        salvar_documento_como_pdf(driver, link, caminho_pdf)
        time.sleep(2)  # Pequena pausa entre documentos

# --- 3. FUNÇÃO PRINCIPAL (MAIN) ---

def main():
    """
    Função principal que orquestra todo o processo de automação.
    """
    configurar_logging()
    logging.info("==== INICIANDO AUTOMAÇÃO DE CAPTURA DE DOCUMENTOS DO SEI ====")
    
    criar_pastas()

    # Solicita as credenciais de forma segura
    usuario = input("Digite seu usuário do SEI: ")
    try:
        senha = getpass.getpass("Digite sua senha do SEI: ")
    except Exception as error:
        logging.error(f"Não foi possível ler a senha: {error}")
        return
        
    orgao = input("Digite a sigla do Órgão (ex: MGI): ")

    driver = None
    try:
        # Inicializa o WebDriver
        logging.info("Inicializando o navegador Chrome.")
        service = ChromeService(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service)
        driver.implicitly_wait(5) # Espera implícita

        # Etapa 1: Login
        if not realizar_login(driver, URL_SEI, usuario, senha, orgao):
            logging.error("Processo encerrado devido a falha no login.")
            return

        # Etapa 2: Busca
        if not executar_busca(driver):
            logging.error("Processo encerrado devido a falha na busca.")
            return

        # Etapa 3: Navegação e extração dos dados
        today = datetime.now().strftime('%Y-%m-%d')
        caminho_csv = os.path.join(PASTA_LISTAS_ARQUIVOS, f'documentos_extraidos_{today}.csv')
        navegar_paginas(driver, caminho_csv)
        # Etapa 4: Salvar documentos como PDF
        logging.info("Salvando documentos como PDF.")
        baixar_documentos_em_pdf(driver, caminho_csv)

        logging.info("==== PROCESSO DE AUTOMAÇÃO CONCLUÍDO COM SUCESSO ====")

    except Exception as e:
        logging.critical(f"Ocorreu um erro fatal na automação: {e}")
    finally:
        # Garante que o navegador seja fechado no final
        if driver:
            logging.info("Fechando o navegador.")
            driver.quit()

if __name__ == "__main__":
    main()

