import time
from typing import cast

from celery import Celery, Task

from . import config

worker = Celery(__name__, backend=config.REDIS_URL, broker=config.REDIS_URL)


@worker.task()
def _start_task(duration: int) -> bool:
    print(f"Starting task with duration {duration} seconds...")
    time.sleep(duration)
    print(f"Completed task after {duration} seconds.")
    return True


start_task = cast(Task, _start_task)
