from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class CreateTaskRequest(BaseModel):
    duration: int


class CreateTaskResponse(BaseModel):
    task_id: str
    duration: int


class GetTaskResponse(BaseModel):
    task_id: str
    status: str
    date_done: Optional[datetime]

class GetTaskWebsocketResponse(BaseModel):
    task_id: str
    status: str
    date_done: Optional[str]
