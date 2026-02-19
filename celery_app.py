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
        include=[
            'app.tasks.notification_tasks',
            'app.tasks.prepaid_disconnect_tasks',
            'app.tasks.payment_tasks',
        ]
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
        # DISABLED: Automated credit control tasks — DO NOT enable until
        # proper testing with real meters is complete. Manual relay switching
        # is working and must not be disrupted. Code is ready in
        # app/tasks/prepaid_disconnect_tasks.py, gated behind feature flag.
        # Uncomment when ready for production testing:
        #
        # 'disconnect-zero-balance-meters': {
        #     'task': 'app.tasks.prepaid_disconnect_tasks.disconnect_zero_balance_meters',
        #     'schedule': crontab(hour=6, minute=0),
        #     'options': {'queue': 'prepaid'}
        # },
        # 'reconnect-topped-up-meters': {
        #     'task': 'app.tasks.prepaid_disconnect_tasks.reconnect_topped_up_meters',
        #     'schedule': crontab(minute='*/30'),
        #     'options': {'queue': 'prepaid'}
        # },
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
        # Expire stale pending PayFast transactions every 30 minutes
        'expire-stale-payfast': {
            'task': 'app.tasks.payment_tasks.expire_stale_payfast_transactions',
            'schedule': crontab(minute='*/30'),
            'options': {'queue': 'payments'}
        },
        # Reconcile PayFast transactions daily at midnight
        'reconcile-payfast-daily': {
            'task': 'app.tasks.payment_tasks.reconcile_payfast_transactions',
            'schedule': crontab(hour=0, minute=0),
            'options': {'queue': 'payments'}
        },
    }

    celery.conf.task_routes = {
        'app.tasks.notification_tasks.*': {'queue': 'notifications'},
        'app.tasks.prepaid_disconnect_tasks.*': {'queue': 'prepaid'},
        'app.tasks.payment_tasks.*': {'queue': 'payments'},
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
