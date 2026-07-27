from celery import Celery

from src.core.config import settings

celery_app = Celery(
    'cafe_booking',
    broker=settings.effective_celery_broker_url,
    backend=settings.effective_celery_result_backend,
    include=('src.celery_app.tasks.booking_notif_tasks'),
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Europe/Moscow',
    enable_utc=True,
    task_track_started=True,
    worker_prefetch_multiplier=1,
)
