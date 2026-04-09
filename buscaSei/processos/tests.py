from django.test import TestCase
from .models import ProcessoSEI, AndamentoProcesso


class ProcessoSEITestCase(TestCase):
    def setUp(self):
        self.processo = ProcessoSEI.objects.create(
            numero_processo="00000.000000/0000-00",
            assunto="Teste",
            status="Processado"
        )
    
    def test_processo_criacao(self):
        """Testa a criação de um processo"""
        self.assertEqual(self.processo.numero_processo, "00000.000000/0000-00")
        self.assertEqual(self.processo.status, "Processado")
    
    def test_andamento_criacao(self):
        """Testa a criação de um andamento"""
        andamento = AndamentoProcesso.objects.create(
            processo=self.processo,
            tipo_movimentacao="Recebimento",
            descricao="Documento recebido"
        )
        self.assertEqual(andamento.processo, self.processo)
        self.assertIn(andamento, self.processo.andamentos.all())
