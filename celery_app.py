"""
Celery application configuration for background tasks and scheduled jobs.

Usage:
    # Start the worker:
    celery -A celery_app.celery worker --loglevel=info

    # Start the beat scheduler (for periodic tasks):
    celery -A celery_app.celery beat --loglevel=info

    # Or run both together (development only):
    celery -A celery_app.celery worker --beat --loglevel=info
"""
from celery import Celery
from celery.schedules import crontab
from config import Config


def make_celery(app_name: str = __name__) -> Celery:
    """Create and configure Celery instance."""
    celery = Celery(
        app_name,
        broker=Config.CELERY_BROKER_URL,
        backend=Config.CELERY_RESULT_BACKEND,
        include=['app.tasks.notification_tasks']
    )

    # Celery configuration
    celery.conf.update(
        timezone=Config.CELERY_TIMEZONE,
        enable_utc=Config.CELERY_ENABLE_UTC,
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        task_track_started=True,
        task_time_limit=300,  # 5 minutes max per task
        worker_prefetch_multiplier=1,
        worker_concurrency=4,
    )

    # Beat schedule for periodic tasks
    celery.conf.beat_schedule = {
        # Check for low credit wallets every night at 6 AM
        'check-low-credit-daily': {
            'task': 'app.tasks.notification_tasks.check_low_credit_wallets',
            'schedule': crontab(hour=6, minute=0),
            'options': {'queue': 'notifications'}
        },
        # Analyze high usage patterns every night at 7 AM
        'analyze-high-usage-daily': {
            'task': 'app.tasks.notification_tasks.analyze_high_usage',
            'schedule': crontab(hour=7, minute=0),
            'options': {'queue': 'notifications'}
        },
        # Check for critical credit levels every 4 hours
        'check-critical-credit': {
            'task': 'app.tasks.notification_tasks.check_critical_credit_wallets',
            'schedule': crontab(hour='*/4', minute=30),
            'options': {'queue': 'notifications'}
        },
    }

    celery.conf.task_routes = {
        'app.tasks.notification_tasks.*': {'queue': 'notifications'},
    }

    return celery


# Create the Celery instance
celery = make_celery('quantify_metering')


def init_celery(app):
    """Initialize Celery with Flask application context."""
    celery.conf.update(app.config)

    class ContextTask(celery.Task):
        """Task that runs within Flask application context."""
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery
