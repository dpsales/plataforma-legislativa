from __future__ import annotations

from django.core.management.base import BaseCommand, CommandError

from ...models import TrackedDocument
from ...services.sync import sync_all_documents


class Command(BaseCommand):
    help = "Atualiza os dados das proposições monitoradas a partir das fontes oficiais."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--slug",
            dest="slug",
            help="Slug do documento monitorado (default=atualizar todos).",
        )

    def handle(self, *args, **options):
        slug = options.get("slug")
        queryset = TrackedDocument.objects.all()
        if slug:
            queryset = queryset.filter(slug=slug)
            if not queryset.exists():
                raise CommandError(f"Documento com slug '{slug}' não encontrado.")
        total = sync_all_documents(queryset)
        self.stdout.write(self.style.SUCCESS(f"Atualização concluída ({total} proposições processadas)."))
