import requests
import pandas as pd
from typing import List, Dict
from datetime import datetime, date, timedelta
from django.utils import timezone
from .models import EventoLegislativo, AtualizacaoProposicao


class CamaraEventosCollector:
    """Coleta eventos da Câmara via API e CSV."""
    
    BASE_URL = "https://dadosabertos.camara.leg.br/api/v2"
    CSV_URL_TEMPLATE = "http://dadosabertos.camara.leg.br/arquivos/eventos/csv/eventos-{ano}.csv"
    CSV_ORGAOS_URL_TEMPLATE = "http://dadosabertos.camara.leg.br/arquivos/eventosOrgaos/csv/eventosOrgaos-{ano}.csv"
    
    @staticmethod
    def buscar_eventos_api(data_inicio: date, data_fim: date) -> List[Dict]:
        """
        Busca eventos da Câmara via API.
        
        Args:
            data_inicio: Data inicial (YYYY-MM-DD)
            data_fim: Data final (YYYY-MM-DD)
        """
        url = f"{CamaraEventosCollector.BASE_URL}/eventos"
        params = {
            "dataInicio": data_inicio.isoformat(),
            "dataFim": data_fim.isoformat(),
            "ordem": "ASC",
            "ordenarPor": "dataHoraInicio"
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json().get("dados", [])
        except Exception as e:
            print(f"Erro ao buscar eventos Câmara (API): {e}")
            return []
    
    @staticmethod
    def buscar_eventos_csv(ano: int) -> pd.DataFrame:
        """Busca eventos de arquivo CSV."""
        try:
            url = CamaraEventosCollector.CSV_URL_TEMPLATE.format(ano=ano)
            df = pd.read_csv(url)
            return df
        except Exception as e:
            print(f"Erro ao buscar CSV eventos {ano}: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def buscar_eventos_orgaos_csv(ano: int) -> pd.DataFrame:
        """Busca eventos de órgãos de arquivo CSV."""
        try:
            url = CamaraEventosCollector.CSV_ORGAOS_URL_TEMPLATE.format(ano=ano)
            df = pd.read_csv(url)
            return df
        except Exception as e:
            print(f"Erro ao buscar CSV eventosOrgaos {ano}: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def salvar_evento(evento_dict: Dict, casa: str = 'Câmara'):
        """Salva evento no BD."""
        
        codigo = f"{evento_dict.get('id', '')}"
        
        evento, created = EventoLegislativo.objects.update_or_create(
            codigo_evento=codigo,
            casa='Câmara',
            defaults={
                'titulo': evento_dict.get('titulo', evento_dict.get('descricao', ''))[:500],
                'descricao': evento_dict.get('descricao', ''),
                'tipo': CamaraEventosCollector._mapear_tipo(evento_dict.get('tipo', '')),
                'local': evento_dict.get('local', ''),
                'data_evento': evento_dict.get('dataHoraInicio', '')[:10],
                'hora_inicio': CamaraEventosCollector._extrair_hora(evento_dict.get('dataHoraInicio', '')),
                'url_evento': evento_dict.get('urlRegistro', ''),
            }
        )
        
        return evento, created
    
    @staticmethod
    def _mapear_tipo(tipo_str: str) -> str:
        """Mapeia tipo de evento da Câmara."""
        tipo_lower = str(tipo_str).lower()
        
        if 'votação' in tipo_lower or 'votada' in tipo_lower:
            return 'VOTACAO'
        elif 'sessão' in tipo_lower or 'plenária' in tipo_lower:
            return 'SESSAO'
        elif 'comissão' in tipo_lower:
            return 'COMISSAO'
        elif 'plenário' in tipo_lower:
            return 'PLENARIO'
        else:
            return 'OUTRA'
    
    @staticmethod
    def _extrair_hora(data_hora_str: str) -> str:
        """Extrai hora de string ISO 8601."""
        if not data_hora_str or len(data_hora_str) < 11:
            return None
        try:
            return data_hora_str[11:16]  # HH:MM
        except:
            return None


class SenadoEventosCollector:
    """Coleta eventos do Senado (Comissões + Plenário)."""
    
    BASE_URL_COMISSOES = "https://legis.senado.leg.br/dadosabertos/comissao/agenda"
    BASE_URL_PLENARIO = "https://legis.senado.leg.br/dadosabertos/plenario/agenda/cn"
    
    @staticmethod
    def buscar_eventos_comissoes(data_inicio: date, data_fim: date) -> Dict:
        """
        Busca agenda de comissões do Senado.
        
        Args:
            data_inicio: Data inicial (YYYYMMDD)
            data_fim: Data final (YYYYMMDD)
        """
        data_inicio_str = data_inicio.strftime("%Y%m%d")
        data_fim_str = data_fim.strftime("%Y%m%d")
        
        url = f"{SenadoEventosCollector.BASE_URL_COMISSOES}/{data_inicio_str}/{data_fim_str}"
        params = {"v": "2"}
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Erro ao buscar comissões Senado: {e}")
            return {}
    
    @staticmethod
    def buscar_eventos_plenario(data_inicio: date, data_fim: date) -> Dict:
        """
        Busca agenda do plenário do Senado.
        
        Args:
            data_inicio: Data inicial (YYYYMMDD)
            data_fim: Data final (YYYYMMDD)
        """
        data_inicio_str = data_inicio.strftime("%Y%m%d")
        data_fim_str = data_fim.strftime("%Y%m%d")
        
        url = f"{SenadoEventosCollector.BASE_URL_PLENARIO}/{data_inicio_str}/{data_fim_str}"
        params = {"v": "2"}
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Erro ao buscar plenário Senado: {e}")
            return {}
    
    @staticmethod
    def processar_comissoes(data: Dict) -> List[Dict]:
        """Processa resposta de comissões para list de eventos."""
        eventos = []
        
        # Estrutura: {"Comissoes": [{"Comissao": {...}, "Reunioes": [...]}]}
        comissoes = data.get("Comissoes", {}).get("Comissao", [])
        
        if not isinstance(comissoes, list):
            comissoes = [comissoes]
        
        for comissao_data in comissoes:
            comissao_nome = comissao_data.get("Nome", "")
            reunioes = comissao_data.get("Reunioes", {}).get("Reuniao", [])
            
            if not isinstance(reunioes, list):
                reunioes = [reunioes]
            
            for reuniao in reunioes:
                evento = {
                    'id': reuniao.get("Codigo", ""),
                    'titulo': f"Reunião - {comissao_nome}",
                    'descricao': reuniao.get("Assunto", ""),
                    'comissao': comissao_nome,
                    'local': reuniao.get("Local", ""),
                    'data': reuniao.get("Data", ""),
                    'hora': reuniao.get("Hora", ""),
                    'tipo': 'COMISSAO',
                }
                eventos.append(evento)
        
        return eventos
    
    @staticmethod
    def processar_plenario(data: Dict) -> List[Dict]:
        """Processa resposta de plenário para list de eventos."""
        eventos = []
        
        # Estrutura: {"Ordens": {"Ordem": [...]}}
        ordens = data.get("Ordens", {}).get("Ordem", [])
        
        if not isinstance(ordens, list):
            ordens = [ordens]
        
        for ordem in ordens:
            evento = {
                'id': ordem.get("Codigo", ""),
                'titulo': f"Sessão Plenária - {ordem.get('Data', '')}",
                'descricao': f"Ordem do dia: {ordem.get('Objeto', '')}",
                'local': 'Plenário - Senado Federal',
                'data': ordem.get("Data", ""),
                'hora': ordem.get("Hora", ""),
                'tipo': 'PLENARIO',
                'url_transmissao': ordem.get("UrlTexto", ""),
            }
            eventos.append(evento)
        
        return eventos
    
    @staticmethod
    def salvar_evento_senado(evento_dict: Dict, tipo: str = 'COMISSAO'):
        """Salva evento do Senado no BD."""
        
        codigo = f"SENADO_{evento_dict.get('id', '')}"
        
        # Montar datetime
        try:
            data_str = evento_dict.get('data', '')
            hora_str = evento_dict.get('hora', '00:00')
            data_obj = datetime.strptime(f"{data_str} {hora_str}", "%d/%m/%Y %H:%M").date()
            hora_obj = datetime.strptime(hora_str, "%H:%M").time()
        except:
            data_obj = timezone.now().date()
            hora_obj = None
        
        evento, created = EventoLegislativo.objects.update_or_create(
            codigo_evento=codigo,
            casa='Senado',
            defaults={
                'titulo': evento_dict.get('titulo', '')[:500],
                'descricao': evento_dict.get('descricao', ''),
                'tipo': tipo,
                'local': evento_dict.get('local', ''),
                'comissao': evento_dict.get('comissao', ''),
                'data_evento': data_obj,
                'hora_inicio': hora_obj,
                'url_transmissao': evento_dict.get('url_transmissao', ''),
            }
        )
        
        return evento, created


class ProposicaoMonitoradaCollector:
    """Coleta atualizações de proposições monitoradas."""
    
    @staticmethod
    def buscar_atualizacoes_buscaReqs(dias: int = 7) -> List[Dict]:
        """Busca atualizações de proposições de interesse MGI."""
        
        from datetime import timedelta
        from django.utils import timezone
        
        try:
            from buscaReqs.requisicoes.models import Requerimento
            
            data_limite = timezone.now() - timedelta(days=dias)
            
            atualizados = Requerimento.objects.filter(
                atualizado_em__gte=data_limite
            ).values('codigo_material', 'titulo', 'situacao', 'atualizado_em')
            
            return list(atualizados)
        except ImportError:
            return []
    
    @staticmethod
    def buscar_atualizacoes_buscaSei(dias: int = 7) -> List[Dict]:
        """Busca atualizações de processos SEI."""
        
        from datetime import timedelta
        from django.utils import timezone
        
        try:
            from buscaSei.processos.models import Processo
            
            data_limite = timezone.now() - timedelta(days=dias)
            
            atualizados = Processo.objects.filter(
                atualizado_em__gte=data_limite
            ).values('codigo_material', 'titulo', 'situacao', 'atualizado_em')
            
            return list(atualizados)
        except ImportError:
            return []
    
    @staticmethod
    def registrar_atualizacao(codigo: str, casa: str, tipo: str, descricao: str, origem: str):
        """Registra atualização de proposição."""
        
        AtualizacaoProposicao.objects.create(
            codigo_material=codigo,
            casa=casa,
            tipo=tipo,
            descricao=descricao,
            situacao_atual=descricao,
            data_atualizacao=timezone.now(),
            origem=origem
        )
