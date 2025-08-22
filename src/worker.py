import time
from typing import cast

from celery import Celery, Task

from . import config

worker = Celery(__name__)
worker.conf.update(
    broker_url=config.REDIS_URL,
    enable_utc=True,
    result_backend=config.REDIS_URL,
    result_serializer="json",
    task_serializer="json",
    task_track_started=True,
)


@worker.task()
def _start_task(duration: int) -> bool:
    print(f"Starting task with duration {duration} seconds...")
    time.sleep(duration)
    print(f"Completed task after {duration} seconds.")
    return True


def revoke_task(task_id: str):
    worker.control.revoke(task_id, terminate=True)


start_task = cast(Task, _start_task)
