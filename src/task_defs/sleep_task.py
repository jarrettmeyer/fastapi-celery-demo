"""Sleep task implementation - sleeps for a specified duration with progress updates."""

import logging
import time
from pydantic import BaseModel, Field

from ..config import settings
from ..worker import celery_app

logger: logging.Logger = logging.getLogger(__name__)


class CreateSleepTaskRequest(BaseModel):
    """Request model for creating a sleep task."""

    duration: int = Field(..., gt=0, le=300, description="Task duration in seconds")


@celery_app.task(name="sleep_task", bind=True)
def sleep_task(self, duration: int) -> dict[str, object]:
    """
    Task that sleeps for specified duration with progress updates.

    Args:
        duration: Sleep duration in seconds

    Returns:
        dict with task completion info

    Raises:
        ValueError: If duration exceeds worker_max_timeout
    """
    logger.info(f"Task {self.request.id} starting: sleeping for {duration} seconds")

    # Track progress with direct state updates
    for i in range(duration):
        # Check if we've exceeded the worker max timeout threshold
        if i >= settings.worker_max_timeout:
            error_msg = f"Task duration {duration}s exceeds worker max timeout of {settings.worker_max_timeout}s"
            logger.error(f"Task {self.request.id} failed: {error_msg}")
            raise ValueError(error_msg)

        time.sleep(1)
        progress = ((i + 1) / duration) * 100

        self.update_state(
            state="PROGRESS",
            meta={
                "current": i + 1,
                "total": duration,
                "progress": progress,
            },
        )
        logger.debug(f"Task progress: {progress:.1f}%")

    logger.info(f"Task {self.request.id} completed after {duration} seconds")

    return {"status": "ok"}
