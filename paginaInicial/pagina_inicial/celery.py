import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pagina_inicial.settings")

app = Celery("paginaInicial")

# Load config from Django settings, all celery configuration should start with `CELERY_`
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover tasks from all registered Django apps
app.autodiscover_tasks()

# Celery Beat Schedule - Configuração de tasks automáticas
app.conf.beat_schedule = {
    # Task semanal: sincroniza agenda completa da semana anterior
    # Roda todo domingo à 08:00
    'sincronizar-agenda-semanal': {
        'task': 'agenda.celery_tasks.sincronizar_agenda_semanal',
        'schedule': crontab(day_of_week=0, hour=8, minute=0),
    },
    
    # Task diária: sincroniza eventos Câmara
    # Roda todos os dias à 02:00
    'sincronizar-eventos-camara-diariamente': {
        'task': 'agenda.celery_tasks.sincronizar_eventos_camara_diariamente',
        'schedule': crontab(hour=2, minute=0),
    },
    
    # Task diária: sincroniza agenda Senado
    # Roda todos os dias à 03:00
    'sincronizar-agenda-senado-diariamente': {
        'task': 'agenda.celery_tasks.sincronizar_agenda_senado_diariamente',
        'schedule': crontab(hour=3, minute=0),
    },
}


@app.task(bind=True)
def debug_task(self):
    """Task de debug para testar configuração Celery."""
    print(f"Request: {self.request!r}")
