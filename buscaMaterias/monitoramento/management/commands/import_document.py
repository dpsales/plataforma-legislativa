from __future__ import annotations

from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from ...services.sync import sync_document
from ...utils import load_document_from_json


class Command(BaseCommand):
    help = "Importa um documento JSON de monitoramento para a base de dados."

    def add_arguments(self, parser) -> None:
        parser.add_argument("caminho", help="Caminho para o arquivo JSON a ser importado.")
        parser.add_argument(
            "--profile",
            dest="profile",
            default="admin",
            help="Perfil a ser registrado como responsável pela importação (admin/normal).",
        )

    def handle(self, *args, **options):
        caminho = Path(options["caminho"])
        if not caminho.exists():
            raise CommandError(f"Arquivo '{caminho}' não encontrado.")
        with caminho.open("rb") as arquivo:
            documento = load_document_from_json(arquivo.read(), options.get("profile", ""))
        sync_document(documento)
        self.stdout.write(self.style.SUCCESS("Documento importado e sincronizado com sucesso."))
