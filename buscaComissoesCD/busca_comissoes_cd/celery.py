import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "busca_comissoes_cd.settings")

app = Celery("busca_comissoes_cd")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

app.conf.beat_schedule = {
    "refresh-propositions": {
        "task": "comissoes.tasks.refresh_propositions",
        "schedule": crontab(minute="*/30"),
    }
}
app.conf.timezone = os.getenv("CELERY_TIMEZONE", "America/Sao_Paulo")
