from celery.result import AsyncResult
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse

from .models import CreateTaskRequest, CreateTaskResponse, GetTaskResponse
from .worker import start_task

app = FastAPI()


@app.post("/tasks", response_model=CreateTaskResponse)
async def create_task(request: CreateTaskRequest):
    # Start the celery task asynchronously
    result = start_task.delay(duration=request.duration)
    response = CreateTaskResponse(task_id=result.id, duration=request.duration)
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content=response.model_dump(),
        headers={"Location": f"/tasks/{result.id}"},
    )


@app.get("/tasks/{task_id}", response_model=GetTaskResponse)
async def get_task(task_id: str):
    result = AsyncResult(
        id=task_id,
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found",
        )

    response = GetTaskResponse(
        task_id=task_id,
        status=result.status,
        date_done=result.date_done,
    )
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=response.model_dump(),
    )
