"""Celery configuration for MindArena."""
import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('mindarena')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Periodic task schedule (requires celery beat)
app.conf.beat_schedule = {
    'cleanup-expired-tokens': {
        'task': 'apps.progression.tasks.cleanup_expired_tokens',
        'schedule': crontab(hour=3, minute=0),  # Daily at 3 AM UTC
    },
    'generate-daily-stats': {
        'task': 'apps.progression.tasks.generate_daily_stats',
        'schedule': crontab(hour=0, minute=5),  # Daily at 00:05 UTC
    },
}
