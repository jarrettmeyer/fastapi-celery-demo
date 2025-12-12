from typing import Literal
from datetime import datetime
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"


class TaskResponse(BaseModel):
    """Unified response model for all task-related endpoints.

    Used by:
    - POST /tasks (create_task)
    - GET /tasks (list_tasks)
    - GET /tasks/{task_id} (get_task)
    """

    task_id: str
    state: str
    name: str | None = None
    worker: str | None = None  # Set for GET /tasks responses
    date_done: datetime | str | None = None  # datetime for list, str for detail
    progress: float | None = None  # Progress percentage (0-100)


class WorkerResponse(BaseModel):
    """Basic worker information"""

    worker_name: str
    uptime: int  # Uptime in seconds
    max_concurrency: int  # Maximum number of concurrent tasks
    registered_tasks: list[str] = []  # List of task names registered with this worker


class ConfigResponse(BaseModel):
    """Application configuration for frontend"""

    terminal_states: list[str] = Field(
        ..., description="List of task states considered terminal/final"
    )
