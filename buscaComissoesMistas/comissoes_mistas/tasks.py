from celery import shared_task

from .services import refresh_dataset


@shared_task(bind=True)
def refresh_propositions(self) -> int:
    """Atualiza o conjunto de proposições monitoradas."""
    return refresh_dataset()
