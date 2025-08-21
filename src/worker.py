import time
from typing import cast
from celery import Celery, Task

from . import config

app = Celery(__name__, backend=config.REDIS_URL, broker=config.REDIS_URL)

@app.task()
def _start_task(duration: int) -> bool:
    time.sleep(duration)
    return True

start_task = cast(Task, _start_task)
