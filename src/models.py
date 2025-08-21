from typing import Optional
from pydantic import BaseModel


class CreateTaskRequest(BaseModel):
    duration: int


class CreateTaskResponse(BaseModel):
    task_id: str
    duration: int


class GetTaskResponse(BaseModel):
    task_id: str
    state: str
    date_done: Optional[str]


class GetTaskWebsocketResponse(BaseModel):
    task_id: str
    state: str
    date_done: Optional[str]
