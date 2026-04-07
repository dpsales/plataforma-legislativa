from django.core.management.base import BaseCommand

from comissoes.services import refresh_dataset


class Command(BaseCommand):
    help = "Atualiza as proposições tramitando nas comissões do Senado"

    def handle(self, *args, **options):
        quantidade = refresh_dataset()
        if quantidade:
            self.stdout.write(
                self.style.SUCCESS(f"Atualização concluída ({quantidade} proposições processadas).")
            )
        else:
            self.stdout.write(self.style.WARNING("Atualização finalizada sem novos registros."))
