import asyncio

from celery.result import AsyncResult
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, status
from fastapi.responses import JSONResponse

from .models import (
    CreateTaskRequest,
    CreateTaskResponse,
    GetTaskResponse,
    GetTaskWebsocketResponse,
)
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
    result = AsyncResult(id=task_id)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found",
        )

    response = GetTaskResponse(
        task_id=str(result.id),
        state=result.state,
        date_done=str(result.date_done) if result.date_done else None,
    )
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=response.model_dump(),
    )


@app.websocket("/tasks/{task_id}/ws")
async def get_task_websocket(ws: WebSocket, task_id: str):
    await ws.accept()
    last_known_state = None

    try:
        while True:
            result = AsyncResult(id=task_id)
            if result.state != last_known_state:
                print(f"Task {task_id} state changed from {last_known_state} to {result.state}")
                response = GetTaskWebsocketResponse(
                    task_id=str(result.id),
                    state=result.state,
                    date_done=str(result.date_done) if result.date_done else None,
                )
                await ws.send_json(response.model_dump())
                last_known_state = result.status
            if result.status in ("SUCCESS"):
                break
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        pass
