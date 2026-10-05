from datetime import date, time
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel

TaskStatus = Literal["pending", "completed"]


class TaskCreate(BaseModel):
    subject_id: int
    topic_id: int | None = None
    title: str = Field(min_length=1, max_length=200)
    scheduled_date: date
    start_time: time | None = None
    duration_mins: int = Field(default=60, ge=5, le=960)


class TaskStatusUpdate(BaseModel):
    status: TaskStatus


class TaskOut(ORMModel):
    id: int
    subject_id: int
    subject_name: str
    topic_id: int | None
    title: str
    scheduled_date: date
    start_time: time | None
    duration_mins: int
    status: TaskStatus
    source: Literal["manual", "ai"]
    plan_id: int | None
