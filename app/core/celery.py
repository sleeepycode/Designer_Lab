from celery import Celery
from app.core.config import settings

celery_app = Celery(
    'document_service',
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=['app.workers.tasks'],
)

celery_app.autodiscover_tasks(['app.workers'])

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,
    result_expires=3600,
    # SQLAlchemy-specific settings
    broker_engine_options={
        'pool_pre_ping': True,
        'pool_recycle': 3600,
    },
)

