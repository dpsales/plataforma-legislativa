from django.test import TestCase
from django.utils import timezone
from datetime import date, timedelta
from .models import EventoLegislativo, AtualizacaoProposicao, AgendaFavorita
from django.contrib.auth.models import User


class EventoLegislativoTestCase(TestCase):
    """Testes para modelo EventoLegislativo."""
    
    def setUp(self):
        """Criar evento de teste."""
        self.evento = EventoLegislativo.objects.create(
            codigo_evento='EVENTO_001',
            casa='Câmara',
            titulo='Votação de Projeto de Lei',
            tipo='VOTACAO',
            data_evento=date.today(),
            hora_inicio='14:00'
        )
    
    def test_criar_evento(self):
        """Testar criação de evento."""
        self.assertEqual(self.evento.codigo_evento, 'EVENTO_001')
        self.assertEqual(self.evento.casa, 'Câmara')
    
    def test_obter_agenda_semana_anterior(self):
        """Testar busca de eventos da semana anterior."""
        eventos = EventoLegislativo.obter_agenda_semana_anterior()
        self.assertIsNotNone(eventos)
    
    def test_str_representation(self):
        """Testar representação em string."""
        expected = f"{self.evento.titulo} ({self.evento.casa}) - {self.evento.data_evento}"
        self.assertEqual(str(self.evento), expected)


class AtualizacaoProposicaoTestCase(TestCase):
    """Testes para modelo AtualizacaoProposicao."""
    
    def setUp(self):
        """Criar atualização de teste."""
        self.atualizacao = AtualizacaoProposicao.objects.create(
            codigo_material='PL 1234/2024',
            casa='Câmara',
            tipo='PAUTA',
            descricao='Adicionada à pauta de votação',
            data_atualizacao=timezone.now(),
            origem='buscaReqs'
        )
    
    def test_criar_atualizacao(self):
        """Testar criação de atualização."""
        self.assertEqual(self.atualizacao.codigo_material, 'PL 1234/2024')
        self.assertEqual(self.atualizacao.origem, 'buscaReqs')
    
    def test_obter_atualizacoes_semana_anterior(self):
        """Testar busca de atualizações da semana anterior."""
        atualizacoes = AtualizacaoProposicao.obter_atualizacoes_semana_anterior()
        self.assertIsNotNone(atualizacoes)


class AgendaFavoritaTestCase(TestCase):
    """Testes para modelo AgendaFavorita."""
    
    def setUp(self):
        """Criar usuário e favorito de teste."""
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.favorito = AgendaFavorita.objects.create(
            usuario=self.user,
            tipo='comissao_senado',
            nome='Comissão de Orçamento'
        )
    
    def test_criar_favorito(self):
        """Testar criação de favorito."""
        self.assertEqual(self.favorito.usuario.username, 'testuser')
        self.assertEqual(self.favorito.nome, 'Comissão de Orçamento')
    
    def test_unique_constraint(self):
        """Testar constraint único."""
        with self.assertRaises(Exception):
            AgendaFavorita.objects.create(
                usuario=self.user,
                tipo='comissao_senado',
                nome='Comissão de Orçamento'
            )
