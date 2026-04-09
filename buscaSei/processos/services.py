import os
import time
import logging
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    NoSuchElementException, 
    TimeoutException, 
    StaleElementReferenceException
)
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService
from lxml import html as lxml_html
from .models import ProcessoSEI, AndamentoProcesso, DocumentoProcesso

logger = logging.getLogger(__name__)

# URL do SEI para busca de processos
URL_SEI_BUSCA = 'https://colaboragov.sei.gov.br/sip/modulos/MF/login_especial/login_especial.php?sigla_orgao_sistema=MGI&sigla_sistema=SEI&url_destino=/sip/modulos/pesquisa/md_pesq_documento_lista.php?acao=pesquisar'


class ExtratorDadosSEI:
    """
    Classe responsável por extrair dados de processos do SEI via web scraping
    """
    
    def __init__(self, numero_processo):
        self.numero_processo = numero_processo
        self.driver = None
        self.dados_processo = {}
        self.andamentos = []
        
    def _inicializar_driver(self):
        """Inicializa o WebDriver do Selenium"""
        try:
            options = webdriver.ChromeOptions()
            # Adicione --no-sandbox se rodando em container
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            
            service = ChromeService(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            self.driver.implicitly_wait(10)
            return True
        except Exception as e:
            logger.error(f"Erro ao inicializar WebDriver: {str(e)}")
            return False
    
    def _fechar_driver(self):
        """Fecha o WebDriver"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
    
    def buscar_processo(self):
        """
        Busca o processo no SEI usando a pesquisa rápida
        Retorna True se encontrado, False caso contrário
        """
        if not self._inicializar_driver():
            return False
        
        try:
            logger.info(f"Iniciando busca do processo {self.numero_processo}")
            
            # Navegar para página de busca
            self.driver.get(URL_SEI_BUSCA)
            time.sleep(2)
            
            # Executar a busca pela pesquisa rápida
            self._executar_pesquisa_rapida()
            
            # Extrair informações do processo
            self._extrair_informacoes_processo()
            
            # Extrair andamentos/histórico
            self._extrair_andamentos()
            
            return True
        
        except Exception as e:
            logger.error(f"Erro ao buscar processo: {str(e)}")
            return False
        
        finally:
            self._fechar_driver()
    
    def _executar_pesquisa_rapida(self):
        """
        Executa a pesquisa rápida pelo número do processo
        Simula o clique na pesquisa rápida e preenchimento do formulário
        """
        try:
            wait = WebDriverWait(self.driver, 10)
            
            # Encontra o campo de pesquisa rápida (protocolo)
            campo_protocolo = wait.until(
                EC.presence_of_element_located((By.ID, "txtProtocoloPesquisaRapida"))
            )
            
            # Limpa e preenche o campo com o número do processo
            campo_protocolo.clear()
            campo_protocolo.send_keys(self.numero_processo)
            time.sleep(1)
            
            # Submete o formulário de pesquisa rápida
            form_pesquisa = self.driver.find_element(By.ID, "frmProtocoloPesquisaRapida")
            form_pesquisa.submit()
            
            # Aguarda a página carregar
            wait.until(EC.presence_of_element_located((By.ID, "divConsultarAndamento")))
            
            logger.info(f"Pesquisa rápida executada para {self.numero_processo}")
        
        except TimeoutException:
            logger.warning("Timeout ao executar pesquisa rápida")
            raise
        except Exception as e:
            logger.error(f"Erro ao executar pesquisa: {str(e)}")
            raise
    
    def _extrair_informacoes_processo(self):
        """
        Extrai as informações básicas do processo da página
        """
        try:
            wait = WebDriverWait(self.driver, 5)
            
            # Clica no botão de consultar andamento
            botao_andamento = wait.until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="divConsultarAndamento"]/a'))
            )
            botao_andamento.click()
            time.sleep(2)
            
            # Aguarda o histórico aparecer
            wait.until(EC.presence_of_element_located((By.ID, "tblHistorico")))
            
            # Extrai dados visíveis da página
            page_html = self.driver.page_source
            tree = lxml_html.fromstring(page_html)
            
            # Tenta extrair informações básicas
            try:
                # Pode haver metadados na página que identificam o processo
                assunto_elem = tree.xpath('//div[@class="infoProcesso"]//tr[contains(td, "Assunto")]/td[2]')
                if assunto_elem:
                    self.dados_processo['assunto'] = assunto_elem[0].text_content().strip()
            except:
                pass
            
            logger.info("Informações básicas do processo extraídas")
        
        except Exception as e:
            logger.error(f"Erro ao extrair informações do processo: {str(e)}")
    
    def _extrair_andamentos(self):
        """
        Extrai a tabela de histórico/andamentos do processo
        Clica em 'Tipo de Histórico' e extrai a tabela
        """
        try:
            wait = WebDriverWait(self.driver, 5)
            
            # Clica na aba de tipo de histórico
            botao_tipo_historico = wait.until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="ancTipoHistorico"]'))
            )
            botao_tipo_historico.click()
            time.sleep(2)
            
            # Aguarda a tabela de histórico aparecer
            tabela_historico = wait.until(
                EC.presence_of_element_located((By.ID, "tblHistorico"))
            )
            
            # Extrai HTML para parsing
            page_html = self.driver.page_source
            tree = lxml_html.fromstring(page_html)
            
            # Extrai linhas da tabela
            linhas = tree.xpath('//table[@id="tblHistorico"]//tbody//tr')
            
            for linha in linhas:
                colunas = linha.xpath('.//td')
                if len(colunas) >= 3:
                    andamento = {
                        'data': colunas[0].text_content().strip() if len(colunas) > 0 else None,
                        'tipo_movimentacao': colunas[1].text_content().strip() if len(colunas) > 1 else None,
                        'setor': colunas[2].text_content().strip() if len(colunas) > 2 else None,
                        'responsavel': colunas[3].text_content().strip() if len(colunas) > 3 else None,
                    }
                    self.andamentos.append(andamento)
            
            logger.info(f"Extraídos {len(self.andamentos)} andamentos do processo")
        
        except Exception as e:
            logger.warning(f"Erro ao extrair andamentos: {str(e)}")
            # Continua mesmo se não conseguir extrair andamentos
    
    def salvar_no_banco(self):
        """
        Salva os dados extraídos no banco de dados
        """
        try:
            # Busca ou cria o processo
            processo, criado = ProcessoSEI.objects.update_or_create(
                numero_processo=self.numero_processo,
                defaults={
                    'assunto': self.dados_processo.get('assunto', ''),
                    'status': 'Processado',
                    'dados_brutos': self.dados_processo,
                }
            )
            
            # Limpa andamentos antigos
            processo.andamentos.all().delete()
            
            # Salva novos andamentos
            for andamento_data in self.andamentos:
                try:
                    data_andamento = self._parse_data(andamento_data.get('data'))
                    AndamentoProcesso.objects.create(
                        processo=processo,
                        data_andamento=data_andamento,
                        tipo_movimentacao=andamento_data.get('tipo_movimentacao', ''),
                        setor=andamento_data.get('setor', ''),
                        responsavel=andamento_data.get('responsavel', ''),
                    )
                except Exception as e:
                    logger.warning(f"Erro ao salvar andamento: {str(e)}")
            
            logger.info(f"Processo {self.numero_processo} salvo com sucesso")
            return processo
        
        except Exception as e:
            logger.error(f"Erro ao salvar processo no banco: {str(e)}")
            raise
    
    @staticmethod
    def _parse_data(data_str):
        """
        Converte string de data em objeto date
        """
        if not data_str:
            return None
        
        try:
            # Tenta múltiplos formatos
            for fmt in ['%d/%m/%Y', '%d/%m/%Y %H:%M:%S', '%Y-%m-%d']:
                try:
                    return datetime.strptime(data_str.strip(), fmt).date()
                except ValueError:
                    continue
            return None
        except:
            return None


class AutomacaoSEI:
    """
    Classe que coordena a automação completa de busca de processos no SEI
    """
    
    def __init__(self, usuario=None, senha=None, orgao=None):
        self.usuario = usuario
        self.senha = senha
        self.orgao = orgao or 'MGI'
    
    def buscar_processo(self, numero_processo):
        """
        Principal: busca um processo no SEI e salva os dados
        """
        extrator = ExtratorDadosSEI(numero_processo)
        
        if extrator.buscar_processo():
            return extrator.salvar_no_banco()
        
        return None
