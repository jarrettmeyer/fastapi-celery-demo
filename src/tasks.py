"""
Simplified task management module.

This module provides task management functionality using ONLY Celery's inspect() API
for listing tasks. Completed tasks are NOT included in list views, keeping the code
maximally simple for educational purposes.

Key simplifications:
- NO Redis scanning for task history
- NO TaskMetadata dataclass
- NO dynamic endpoint registration
- Shows only active (STARTED) and queued (PENDING) tasks
- Individual task queries still work for ALL states via AsyncResult
"""

import logging
from celery.result import AsyncResult

from .worker import celery_app
from .config import settings
from .models import TaskResponse

logger = logging.getLogger(__name__)


def list_tasks() -> list[TaskResponse]:
    """
    List active and queued tasks from inspect() API only.

    Returns only:
    - Active tasks (currently running on workers)
    - Reserved tasks (queued, waiting to execute)

    Completed tasks are NOT included in this list.
    Use get_task(task_id) to check individual task status.

    Returns:
        List of TaskResponse objects for active and queued tasks
    """
    tasks: list[TaskResponse] = []

    inspect = celery_app.control.inspect(timeout=settings.inspect_timeout)
    if not inspect:
        logger.warning("No workers available for inspect()")
        return []

    # Get active (running) tasks
    active = inspect.active() or {}
    for worker_name, task_list in active.items():
        for task_info in task_list:
            tasks.append(
                TaskResponse(
                    task_id=task_info["id"],
                    state="STARTED",
                    name=task_info.get("name"),
                    worker=worker_name,
                )
            )

    # Get reserved (queued) tasks
    reserved = inspect.reserved() or {}
    for worker_name, task_list in reserved.items():
        for task_info in task_list:
            tasks.append(
                TaskResponse(
                    task_id=task_info["id"],
                    state="PENDING",
                    name=task_info.get("name"),
                    worker=worker_name,
                )
            )

    return tasks


def get_task(task_id: str) -> TaskResponse:
    """
    Get detailed status of a specific task by ID.

    Uses Celery's AsyncResult which queries the Redis backend.
    This works for tasks in ANY state (pending, running, completed).

    Args:
        task_id: Unique task identifier

    Returns:
        TaskResponse with current task state and metadata
    """
    result = AsyncResult(task_id, app=celery_app)

    response = TaskResponse(
        task_id=task_id,
        state=result.state,
        name=result.name,
    )

    # Add result for successful tasks
    if result.successful():
        response.date_done = result.date_done

    # Add progress for running tasks
    if result.state == "PROGRESS":
        info: dict = result.info if isinstance(result.info, dict) else {}
        response.progress = info.get("progress") if info else None

    return response


def cancel_task(task_id: str) -> None:
    """
    Cancel a task by ID.

    Sends revoke signal to workers. The task will be terminated
    if it's currently running.

    Args:
        task_id: Unique task identifier to cancel
    """
    celery_app.control.revoke(task_id, terminate=True)


def delete_task(task_id: str) -> None:
    """
    Delete/cancel a task.

    For this simplified demo, delete is the same as cancel.
    In production, you might want to clean up Redis metadata here.

    Args:
        task_id: Unique task identifier to delete
    """
    cancel_task(task_id)
