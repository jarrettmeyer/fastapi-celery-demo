import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from .config import settings
from .logging_config import setup_logging
from .models import (
    TaskResponse,
    HealthResponse,
    WorkerResponse,
    ConfigResponse,
)
from . import tasks
from .task_defs.sleep_task import CreateSleepTaskRequest
from .task_defs.calculation_task import CreateCalculationTaskRequest
from .worker import celery_app

# Configure logging
setup_logging(debug=settings.debug)
logger: logging.Logger = logging.getLogger(__name__)

# Create FastAPI app
app: FastAPI = FastAPI(
    title="FastAPI + Celery Demo",
    description="Demonstration of FastAPI with Celery background tasks",
    version="0.1.0",
)

# Mount static files
static_dir: Path = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/", response_class=HTMLResponse)
async def get_index() -> HTMLResponse:
    """Serve the main UI"""
    templates_dir: Path = Path(__file__).parent / "templates"
    index_file: Path = templates_dir / "index.html"

    if not index_file.exists():
        return HTMLResponse(content="<h1>Template not found</h1>", status_code=404)

    return HTMLResponse(content=index_file.read_text())


@app.get("/health", response_model=HealthResponse)
async def get_health() -> HealthResponse:
    """Health check endpoint"""
    return HealthResponse()


@app.get("/config", response_model=ConfigResponse)
async def get_config() -> ConfigResponse:
    """Get application configuration for frontend"""
    return ConfigResponse(terminal_states=settings.terminal_states)


@app.get("/workers", response_model=list[WorkerResponse])
async def get_workers() -> list[WorkerResponse]:
    """Get detailed information about all available workers"""
    try:
        inspect = celery_app.control.inspect(timeout=settings.inspect_timeout)
        stats_data = inspect.stats()

        if not stats_data:
            logger.warning("No worker stats available")
            return []

        # Fetch registered tasks for all workers
        registered_data = None
        try:
            registered_data = inspect.registered()
            if not registered_data:
                logger.warning("No registered tasks data available")
        except Exception as e:
            logger.warning(f"Error getting registered tasks: {e}")

        workers: list[WorkerResponse] = []
        for worker_name, worker_data in stats_data.items():
            try:
                pool_data = worker_data.get("pool", {})

                # Get registered tasks for this worker, default to empty list
                registered_tasks = []
                if registered_data and worker_name in registered_data:
                    registered_tasks = registered_data[worker_name]

                worker = WorkerResponse(
                    worker_name=worker_name,
                    uptime=worker_data.get("uptime", 0),
                    max_concurrency=pool_data.get("max-concurrency", 0),
                    registered_tasks=registered_tasks,
                )
                workers.append(worker)
            except Exception as e:
                logger.warning(f"Error parsing stats for worker {worker_name}: {e}")
                continue

        logger.debug(f"Retrieved stats for {len(workers)} workers")
        return workers

    except Exception as e:
        logger.warning(f"Error getting worker stats: {e}")
        return []


# Explicit task creation endpoints
@app.post("/tasks/sleep_task", response_model=TaskResponse, status_code=201)
async def create_sleep_task(request: CreateSleepTaskRequest) -> TaskResponse:
    """
    Create a new sleep task.

    Args:
        request: Task parameters (duration in seconds)

    Returns:
        TaskResponse with task_id and initial state
    """
    result = celery_app.send_task(
        "sleep_task", kwargs={"duration": request.duration}
    )

    return TaskResponse(
        task_id=result.id,
        state=result.state,
        name="sleep_task",
    )


@app.post("/tasks/calculation_task", response_model=TaskResponse, status_code=201)
async def create_calculation_task(
    request: CreateCalculationTaskRequest,
) -> TaskResponse:
    """
    Create a new calculation task.

    Args:
        request: Task parameters (numbers and operation)

    Returns:
        TaskResponse with task_id and initial state
    """
    result = celery_app.send_task(
        "calculation_task",
        kwargs={
            "numbers": request.numbers,
            "operation": request.operation,
        },
    )

    return TaskResponse(
        task_id=result.id,
        state=result.state,
        name="calculation_task",
    )


@app.get("/tasks", response_model=list[TaskResponse])
async def list_tasks() -> list[TaskResponse]:
    """
    List all tasks from all sources.

    Combines:
    - Active/reserved tasks from Celery inspect() API
    - Completed tasks from Redis scanning

    Returns tasks sorted by task_id (newest first).
    """
    try:
        return tasks.list_tasks()
    except Exception as e:
        logger.error(f"Error listing tasks: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve task list: {str(e)}",
        )


@app.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str) -> TaskResponse:
    """Get status of a specific task"""
    return tasks.get_task(task_id)


@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: str) -> None:
    """Cancel/revoke a running task or delete a completed task"""
    tasks.delete_task(task_id)
    return None
