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
    'expire-stale-arena-matches': {
        'task': 'apps.progression.tasks.expire_stale_arena_matches',
        'schedule': crontab(minute='*/5'),  # Every 5 minutes
    },
    'recalibrate-irt-params': {
        'task': 'apps.ai_engine.tasks.recalibrate_irt_params',
        'schedule': crontab(hour=3, minute=0),  # Daily at 3 AM UTC
    },
    'generate-learning-paths': {
        'task': 'apps.ai_engine.tasks.generate_learning_paths',
        'schedule': crontab(hour=4, minute=0),  # Daily at 4 AM UTC
    },
    'nightly-ai-learning': {
        'task': 'apps.ai_engine.tasks.nightly_ai_learning',
        'schedule': crontab(hour=5, minute=0),  # Daily at 5 AM UTC
    },
}
