from datetime import time, datetime

from pydantic import BaseModel


class ActivityCreate(BaseModel):
    title: str
    day: str
    start_time: time
    end_time: time


class TaskCreate(BaseModel):
    title: str
    description: str | None = None
    estimated_minutes: int
    deadline: datetime
    priority: int
    status: str = "PENDING"
    is_fixed: bool = False
    fixed_start_time: time | None = None
    fixed_end_time: time | None = None