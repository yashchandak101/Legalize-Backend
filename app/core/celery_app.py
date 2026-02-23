import os
from celery import Celery
from .config import Config


def make_celery(app_name=__name__):
    """Create Celery instance."""
    
    # Get Redis URL from environment or use default
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    broker_url = os.getenv("CELERY_BROKER_URL", redis_url)
    result_backend = os.getenv("CELERY_RESULT_BACKEND", redis_url)
    
    celery = Celery(
        app_name,
        broker=broker_url,
        backend=result_backend,
        include=['app.tasks']
    )
    
    # Configure Celery
    celery.conf.update(
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='UTC',
        enable_utc=True,
        task_track_started=True,
        task_time_limit=30 * 60,  # 30 minutes
        task_soft_time_limit=25 * 60,  # 25 minutes
        worker_prefetch_multiplier=1,
        worker_max_tasks_per_child=1000,
        beat_schedule={
            'send-appointment-reminders': {
                'task': 'app.tasks.send_appointment_reminders',
                'schedule': 3600.0,  # Every hour
            },
        },
    )
    
    return celery


# Create Celery instance
celery_app = make_celery('legalize')
