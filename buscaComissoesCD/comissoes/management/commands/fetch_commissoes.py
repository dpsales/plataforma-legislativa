from django.core.management.base import BaseCommand

from comissoes.services import refresh_dataset


class Command(BaseCommand):
    help = "Atualiza as proposições tramitando em comissões da Câmara"

    def handle(self, *args, **options):
        created = refresh_dataset()
        if created:
            self.stdout.write(self.style.SUCCESS(f"Atualização concluída ({created} novas proposições)."))
        else:
            self.stdout.write(self.style.WARNING("Atualização concluída sem novos registros."))
