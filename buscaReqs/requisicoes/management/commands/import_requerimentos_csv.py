"""
Management command para importar requerimentos de um CSV ou Excel.
Uso: python manage.py import_requerimentos_csv <arquivo_csv_ou_xlsx>
"""
import logging
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from requisicoes.importador import ImportadorRequerimentos

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Importa requerimentos de um arquivo CSV ou Excel"

    def add_arguments(self, parser):
        parser.add_argument(
            "arquivo",
            type=str,
            help="Caminho do arquivo CSV ou Excel a importar",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Limpa a tabela antes de importar",
        )
        parser.add_argument(
            "--delimiter",
            type=str,
            default=";",
            help="Delimitador do CSV (padrão: ;)",
        )
        parser.add_argument(
            "--sheet",
            type=str,
            default="",
            help="Nome da aba do Excel (opcional)",
        )
        parser.add_argument(
            "--sleep",
            type=float,
            default=0.1,
            help="Pausa entre chamadas à API (segundos)",
        )

    def handle(self, *args, **options):
        arquivo_path = Path(options["arquivo"])

        if not arquivo_path.exists():
            raise CommandError(f"Arquivo não encontrado: {arquivo_path}")

        if arquivo_path.suffix.lower() not in {".csv", ".xlsx", ".xls"}:
            raise CommandError("O arquivo deve ser CSV ou Excel (.xlsx/.xls)")

        if options["clear"]:
            from requisicoes.models import Requerimento

            count = Requerimento.objects.all().count()
            Requerimento.objects.all().delete()
            self.stdout.write(
                self.style.SUCCESS(f"✓ {count} requerimentos removidos")
            )

        delimiter = options.get("delimiter", ";")
        sheet = options.get("sheet", "")
        sleep_seconds = float(options.get("sleep", 0.1))

        try:
            with open(arquivo_path, "rb") as file_obj:
                criados, atualizados, erros = ImportadorRequerimentos.from_file(
                    file_obj,
                    arquivo_path.name,
                    delimiter=delimiter,
                    sheet=sheet,
                    sleep_seconds=sleep_seconds,
                )
        except Exception as e:
            raise CommandError(f"Erro ao ler arquivo: {e}")

        total = criados + atualizados
        self.stdout.write(
            self.style.SUCCESS(
                f"✓ Importação concluída: {total} registros processados, {erros} erros"
            )
        )
