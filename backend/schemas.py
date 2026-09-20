from datetime import time, datetime

from pydantic import BaseModel


class ActivityCreate(BaseModel):
    title: str
    day: str
    start_time: time
    end_time: time


class GoalCreate(BaseModel):
    name: str
    description: str | None = None
    weekly_target_minutes: int
    priority: int = 5
    status: str = "ACTIVE"


class TaskCreate(BaseModel):
    title: str
    description: str | None = None

    estimated_minutes: int

    deadline: datetime

    priority: int

    status: str = "PENDING"

    goal_id: int | None = None

    subject_id: int | None = None

    task_type: str = "GENERAL"

    is_fixed: bool = False

    fixed_start_time: time | None = None

    fixed_end_time: time | None = None