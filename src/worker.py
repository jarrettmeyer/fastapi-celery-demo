import logging
from celery import Celery

from .config import settings
from .logging_config import setup_logging

# Configure logging
setup_logging()
logger: logging.Logger = logging.getLogger(__name__)

# Create Celery app
celery_app: Celery = Celery("worker")
celery_app.conf.update(
    broker_url=settings.redis_url,
    result_backend=settings.redis_url,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=settings.celery_task_track_started,
    task_send_sent_event=settings.celery_task_send_sent_event,
    result_expires=settings.celery_result_expires,
    result_extended=settings.celery_result_extended,
)

# Autodiscover tasks in task_defs package
celery_app.autodiscover_tasks(["src.task_defs"])
