from django.db import models
from django.utils import timezone
from datetime import timedelta, datetime


class EventoLegislativo(models.Model):
    """Evento legislativo (Câmara ou Senado)."""
    
    CASAS = [
        ('Câmara', 'Câmara dos Deputados'),
        ('Senado', 'Senado Federal'),
    ]
    
    TIPOS_EVENTO = [
        ('VOTACAO', 'Votação'),
        ('SESSAO', 'Sessão'),
        ('COMISSAO', 'Comissão'),
        ('PLENARIO', 'Plenário'),
        ('OUTRA', 'Outra'),
    ]
    
    # Identificação
    codigo_evento = models.CharField(max_length=100, unique=True, db_index=True)
    casa = models.CharField(max_length=20, choices=CASAS, db_index=True)
    
    # Informações
    titulo = models.CharField(max_length=500)
    descricao = models.TextField(blank=True, null=True)
    tipo = models.CharField(max_length=20, choices=TIPOS_EVENTO, blank=True)
    
    # Local/Comissão
    local = models.CharField(max_length=300, blank=True)
    comissao = models.CharField(max_length=300, blank=True)
    
    # Datas e horários
    data_evento = models.DateField(db_index=True)
    hora_inicio = models.TimeField(blank=True, null=True)
    hora_fim = models.TimeField(blank=True, null=True)
    
    # Links e documentos
    url_evento = models.URLField(blank=True, null=True)
    url_transmissao = models.URLField(blank=True, null=True)
    
    # Proposições relacionadas (JSONField com códigos)
    proposicoes_relacionadas = models.JSONField(default=list, blank=True)
    
    # Rastreamento
    importado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['casa', 'data_evento']),
            models.Index(fields=['-data_evento']),
        ]
        ordering = ['data_evento', 'hora_inicio']
    
    def __str__(self):
        return f"{self.titulo} ({self.casa}) - {self.data_evento}"
    
    @classmethod
    def obter_agenda_semana_anterior(cls):
        """Retorna eventos da semana anterior."""
        hoje = timezone.now().date()
        # Segunda da semana anterior
        inicio_semana = hoje - timedelta(days=hoje.weekday() + 7)
        # Domingo da semana anterior
        fim_semana = inicio_semana + timedelta(days=6)
        
        return cls.objects.filter(
            data_evento__gte=inicio_semana,
            data_evento__lte=fim_semana
        ).order_by('data_evento', 'hora_inicio')


class AtualizacaoProposicao(models.Model):
    """Atualização/movimentação de uma proposição monitorada."""
    
    TIPOS_ATUALIZACAO = [
        ('PAUTA', 'Adicionada à pauta'),
        ('VOTACAO', 'Votação'),
        ('APROVACAO', 'Aprovada'),
        ('REJEICAO', 'Rejeitada'),
        ('TRAMITACAO', 'Tramitação'),
        ('COMISSAO', 'Encaminhada à comissão'),
        ('ARQUIVO', 'Arquivada'),
        ('OUTRA', 'Outra'),
    ]
    
    ORIGENS = [
        ('buscaReqs', 'Busca de Requerimentos'),
        ('buscaSei', 'Busca de Processos SEI'),
        ('buscaMaterias', 'Busca de Matérias'),
        ('buscaComissoes', 'Busca de Comissões'),
    ]
    
    # Referência à proposição
    codigo_material = models.CharField(max_length=100, db_index=True)
    
    casa = models.CharField(max_length=20)
    
    # Informações da atualização
    tipo = models.CharField(max_length=20, choices=TIPOS_ATUALIZACAO)
    descricao = models.TextField()
    situacao_anterior = models.CharField(max_length=300, blank=True)
    situacao_atual = models.CharField(max_length=300, blank=True)
    
    # Data/hora
    data_atualizacao = models.DateTimeField(db_index=True)
    
    # Origem (qual módulo detectou)
    origem = models.CharField(max_length=50, choices=ORIGENS)
    
    # Rastreamento
    detectado_em = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-data_atualizacao']
        indexes = [
            models.Index(fields=['codigo_material', '-data_atualizacao']),
            models.Index(fields=['-data_atualizacao']),
        ]
    
    def __str__(self):
        return f"{self.codigo_material} - {self.tipo} ({self.data_atualizacao})"
    
    @classmethod
    def obter_atualizacoes_semana_anterior(cls):
        """Retorna atualizações da semana anterior."""
        hoje = timezone.now()
        # Segunda da semana anterior
        data_inicio = hoje - timedelta(days=hoje.weekday() + 7)
        # Domingo da semana anterior
        data_fim = data_inicio + timedelta(days=6, hours=23, minutes=59, seconds=59)
        
        return cls.objects.filter(
            data_atualizacao__gte=data_inicio,
            data_atualizacao__lte=data_fim
        ).order_by('-data_atualizacao')


class AgendaFavorita(models.Model):
    """Comissões/eventos favoritados por usuário."""
    
    TIPOS = [
        ('comissao_camara', 'Comissão Câmara'),
        ('comissao_senado', 'Comissão Senado'),
        ('plenario_camara', 'Plenário Câmara'),
        ('plenario_senado', 'Plenário Senado'),
    ]
    
    usuario = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='comissoes_favoritas')
    
    tipo = models.CharField(max_length=20, choices=TIPOS)
    
    nome = models.CharField(max_length=300)
    sigla = models.CharField(max_length=50, blank=True)
    
    criado_em = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['usuario', 'tipo', 'nome']
        ordering = ['tipo', 'nome']
    
    def __str__(self):
        return f"{self.usuario.username} - {self.nome}"
