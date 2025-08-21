from pydantic import BaseModel


class CreateTaskRequest(BaseModel):
    duration: int


class CreateTaskResponse(BaseModel):
    task_id: str
    duration: int
