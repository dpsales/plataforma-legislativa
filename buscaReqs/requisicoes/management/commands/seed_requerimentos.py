"""
Management command que popula a base de dados com dados de teste.
Uso: python manage.py seed_requerimentos
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
import random

from requisicoes.models import Requerimento


class Command(BaseCommand):
    help = "Popula a base de dados com requerimentos de exemplo"

    PROPOSTAS_EXEMPLO = [
        {
            "codigo_material": "REQ 001/2025-CD",
            "titulo": "Requerimento de Comparecimento de Ministro do Planejamento",
            "autor": "Dweck, Esther (PT/SP)",
            "ementa": "Requerimento de Comparecimento à Câmara de discussão sobre transformação do estado",
            "situacao": "Em tramitação",
            "casa": "Câmara",
            "termos_encontrados": "Transformação do Estado",
            "link_ficha": "https://dadosabertos.camara.leg.br",
        },
        {
            "codigo_material": "RIC 002/2025-CD",
            "titulo": "Requerimento de Informações sobre Governo Digital",
            "autor": "Silva, João (PSD/MG)",
            "ementa": "Solicita informações ao Executivo sobre iniciativas de governo digital",
            "situacao": "Aprovado",
            "casa": "Câmara",
            "termos_encontrados": "Governo Digital, Identidade Digital",
            "link_ficha": "https://dadosabertos.camara.leg.br",
        },
        {
            "codigo_material": "REQ 003/2025-SF",
            "titulo": "Audiência Pública sobre Gestão de Pessoas no Setor Público",
            "autor": "Santos, Maria (PT/RJ)",
            "ementa": "Requerimento de audiência pública com gestores de recursos humanos",
            "situacao": "Em tramitação",
            "casa": "Senado",
            "termos_encontrados": "Servidor Público, Gestão de Pessoas",
            "link_ficha": "https://legis.senado.leg.br",
        },
        {
            "codigo_material": "RCP 004/2025-CD",
            "titulo": "Requerimento de Criação de Comissão Especial",
            "autor": "Costa, Pedro (MDB/SP)",
            "ementa": "Cria comissão especial para análise de políticas de sustentabilidade",
            "situacao": "Aprovado",
            "casa": "Câmara",
            "termos_encontrados": "Sustentabilidade, Compras Sustentáveis",
            "link_ficha": "https://dadosabertos.camara.leg.br",
        },
        {
            "codigo_material": "REQ 005/2025-CD",
            "titulo": "Requerimento de Inclusão de Matéria em Pauta",
            "autor": "Oliveira, Ana (PSOL/RJ)",
            "ementa": "Solicita inclusão de PL sobre LAI em pauta do plenário",
            "situacao": "Em tramitação",
            "casa": "Câmara",
            "termos_encontrados": "Acesso à Informação, Transparência",
            "link_ficha": "https://dadosabertos.camara.leg.br",
        },
    ]

    def handle(self, *args, **options):
        self.stdout.write("Iniciando seed de dados de teste...")

        # Limpa dados anteriores
        count = Requerimento.objects.all().delete()[0]
        self.stdout.write(f"  Removidos {count} registros anteriores")

        # Popula com dados de exemplo
        criados = 0
        for exemplo in self.PROPOSTAS_EXEMPLO:
            # Adiciona variações de data
            days_ago = random.randint(1, 60)
            data_apresentacao = timezone.now().date() - timedelta(days=days_ago)
            data_ultima_tramitacao = data_apresentacao + timedelta(days=random.randint(1, 30))

            requerimento = Requerimento.objects.create(
                codigo_material=exemplo["codigo_material"],
                titulo=exemplo["titulo"],
                autor=exemplo["autor"],
                ementa=exemplo["ementa"],
                situacao=exemplo["situacao"],
                casa=exemplo["casa"],
                data_apresentacao=data_apresentacao,
                data_ultima_tramitacao=data_ultima_tramitacao,
                descricao_ultima_tramitacao="Última ação: análise em comissão",
                termos_encontrados=exemplo["termos_encontrados"],
                assuntos_encontrados=exemplo.get("assuntos_encontrados", ""),
                local="Plenário da Câmara" if exemplo["casa"] == "Câmara" else "Plenário do Senado",
                link_ficha=exemplo.get("link_ficha", ""),
            )
            criados += 1
            self.stdout.write(f"  ✓ {requerimento.codigo_material}")

        self.stdout.write(
            self.style.SUCCESS(f"\n✓ Seed concluído: {criados} requerimentos criados")
        )
        self.stdout.write("Acesse http://localhost:8015 para visualizar os dados")
