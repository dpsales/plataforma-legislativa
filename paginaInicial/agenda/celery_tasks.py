from celery import shared_task
from django.utils import timezone
from datetime import timedelta, date
from .models import EventoLegislativo
from .services import (
    CamaraEventosCollector,
    SenadoEventosCollector,
    ProposicaoMonitoradaCollector
)
import logging

logger = logging.getLogger(__name__)


@shared_task
def sincronizar_agenda_semanal():
    """Sincroniza agenda completa da semana anterior."""
    
    hoje = timezone.now().date()
    data_inicio = hoje - timedelta(days=hoje.weekday() + 7)  # Segunda semana anterior
    data_fim = data_inicio + timedelta(days=6)  # Domingo semana anterior
    
    resultado = {
        'sucesso': True,
        'camara': 0,
        'senado_comissoes': 0,
        'senado_plenario': 0,
        'total': 0,
        'periodo': f"{data_inicio} a {data_fim}"
    }
    
    try:
        # Sincronizar Câmara
        logger.info(f"[AGENDA] Sincronizando eventos Câmara ({data_inicio} a {data_fim})")
        eventos_camara = CamaraEventosCollector.buscar_eventos_api(data_inicio, data_fim)
        
        for evt in eventos_camara:
            evento_obj, created = CamaraEventosCollector.salvar_evento(evt)
            if created:
                resultado['camara'] += 1
        
        logger.info(f"[AGENDA] {resultado['camara']} eventos Câmara sincronizados")
    except Exception as e:
        logger.error(f"[AGENDA] Erro sincronizando Câmara: {e}")
        resultado['sucesso'] = False
    
    try:
        # Sincronizar Senado - Comissões
        logger.info(f"[AGENDA] Sincronizando comissões Senado ({data_inicio} a {data_fim})")
        data_comissoes = SenadoEventosCollector.buscar_eventos_comissoes(data_inicio, data_fim)
        eventos_comissoes = SenadoEventosCollector.processar_comissoes(data_comissoes)
        
        for evt in eventos_comissoes:
            evento_obj, created = SenadoEventosCollector.salvar_evento_senado(evt, 'COMISSAO')
            if created:
                resultado['senado_comissoes'] += 1
        
        logger.info(f"[AGENDA] {resultado['senado_comissoes']} comissões Senado sincronizadas")
    except Exception as e:
        logger.error(f"[AGENDA] Erro sincronizando comissões Senado: {e}")
        resultado['sucesso'] = False
    
    try:
        # Sincronizar Senado - Plenário
        logger.info(f"[AGENDA] Sincronizando plenário Senado ({data_inicio} a {data_fim})")
        data_plenario = SenadoEventosCollector.buscar_eventos_plenario(data_inicio, data_fim)
        eventos_plenario = SenadoEventosCollector.processar_plenario(data_plenario)
        
        for evt in eventos_plenario:
            evento_obj, created = SenadoEventosCollector.salvar_evento_senado(evt, 'PLENARIO')
            if created:
                resultado['senado_plenario'] += 1
        
        logger.info(f"[AGENDA] {resultado['senado_plenario']} sessões plenárias Senado sincronizadas")
    except Exception as e:
        logger.error(f"[AGENDA] Erro sincronizando plenário Senado: {e}")
        resultado['sucesso'] = False
    
    resultado['total'] = resultado['camara'] + resultado['senado_comissoes'] + resultado['senado_plenario']
    
    logger.info(f"[AGENDA] Sincronização completa. Total: {resultado['total']} eventos salvos")
    
    return resultado


@shared_task
def sincronizar_eventos_camara_diariamente():
    """Task diária para sincronizar eventos Câmara (roda todo dia às 2h da manhã)."""
    
    logger.info("[AGENDA] Task diária: sincronizando eventos Câmara")
    
    try:
        # Buscar eventos dos últimos 30 dias
        data_fim = timezone.now().date()
        data_inicio = data_fim - timedelta(days=30)
        
        eventos = CamaraEventosCollector.buscar_eventos_api(data_inicio, data_fim)
        criados = 0
        
        for evt in eventos:
            evento_obj, created = CamaraEventosCollector.salvar_evento(evt)
            if created:
                criados += 1
        
        logger.info(f"[AGENDA] {criados} eventos Câmara sincronizados (período: {data_inicio} a {data_fim})")
        return {'sucesso': True, 'criados': criados}
    except Exception as e:
        logger.error(f"[AGENDA] Erro na task diária Câmara: {e}")
        return {'sucesso': False, 'erro': str(e)}


@shared_task
def sincronizar_agenda_senado_diariamente():
    """Task diária para sincronizar agenda Senado (roda todo dia às 3h da manhã)."""
    
    logger.info("[AGENDA] Task diária: sincronizando agenda Senado")
    
    try:
        # Buscar eventos dos últimos 30 dias
        data_inicio = timezone.now().date() - timedelta(days=30)
        data_fim = timezone.now().date()
        
        resultado = {
            'comissoes': 0,
            'plenario': 0,
            'total': 0
        }
        
        # Comissões
        data_comissoes = SenadoEventosCollector.buscar_eventos_comissoes(data_inicio, data_fim)
        eventos_comissoes = SenadoEventosCollector.processar_comissoes(data_comissoes)
        
        for evt in eventos_comissoes:
            evento_obj, created = SenadoEventosCollector.salvar_evento_senado(evt, 'COMISSAO')
            if created:
                resultado['comissoes'] += 1
        
        # Plenário
        data_plenario = SenadoEventosCollector.buscar_eventos_plenario(data_inicio, data_fim)
        eventos_plenario = SenadoEventosCollector.processar_plenario(data_plenario)
        
        for evt in eventos_plenario:
            evento_obj, created = SenadoEventosCollector.salvar_evento_senado(evt, 'PLENARIO')
            if created:
                resultado['plenario'] += 1
        
        resultado['total'] = resultado['comissoes'] + resultado['plenario']
        
        logger.info(f"[AGENDA] Senado sincronizado: {resultado['comissoes']} comissões + {resultado['plenario']} plenário")
        return {'sucesso': True, **resultado}
    except Exception as e:
        logger.error(f"[AGENDA] Erro na task diária Senado: {e}")
        return {'sucesso': False, 'erro': str(e)}
