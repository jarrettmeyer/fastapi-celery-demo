
from fastapi import FastAPI
from .models import CreateTaskRequest, CreateTaskResponse
from .worker import start_task

app = FastAPI()


@app.post("/tasks", response_model=CreateTaskResponse)
async def create_task(request: CreateTaskRequest):
	# Start the celery task asynchronously
	result = start_task.delay(duration=request.duration)
	return CreateTaskResponse(task_id=result.id, duration=request.duration)
