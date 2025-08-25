import asyncio

from celery.result import AsyncResult
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, status
from fastapi.responses import JSONResponse, Response

from .models import (
    CreateTaskRequest,
    CreateTaskResponse,
    GetIndexResponse,
    GetTaskResponse,
    GetTaskWebsocketResponse,
)
from .worker import revoke_task, start_task
from fastapi.middleware.cors import CORSMiddleware


# Create a new FastAPI app.
fastapi_app = FastAPI()

# Add CORS policy.
fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@fastapi_app.get("/", response_model=GetIndexResponse)
async def get_index():
    response = GetIndexResponse()
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=response.model_dump(),
    )


@fastapi_app.get("/health", response_model=GetIndexResponse)
async def get_health():
    response = GetIndexResponse()
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=response.model_dump(),
    )


@fastapi_app.post("/tasks", response_model=CreateTaskResponse)
async def create_task(request: CreateTaskRequest):
    # Start the celery task asynchronously
    result = start_task.delay(duration=request.duration)
    response = CreateTaskResponse(task_id=result.id, duration=request.duration)
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content=response.model_dump(),
        headers={"Location": f"/tasks/{result.id}"},
    )


@fastapi_app.get("/tasks/{task_id}", response_model=GetTaskResponse)
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


@fastapi_app.websocket("/tasks/{task_id}/ws")
async def get_task_websocket(ws: WebSocket, task_id: str):
    await ws.accept()
    last_known_state = None

    try:
        while True:
            result = AsyncResult(id=task_id)
            if last_known_state is None or result.state != last_known_state:
                print(
                    f"Task {task_id} state changed from {last_known_state} to {result.state}"
                )
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


@fastapi_app.delete("/tasks/{task_id}")
async def delete_task(task_id: str):
    revoke_task(task_id=task_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
