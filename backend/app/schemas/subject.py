from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel

TopicStatus = Literal["pending", "completed"]


class TopicCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)


class TopicUpdate(BaseModel):
    """Omit `status` to toggle pending <-> completed; pass it to set explicitly."""

    name: str | None = Field(default=None, min_length=1, max_length=200)
    status: TopicStatus | None = None


class TopicOut(ORMModel):
    id: int
    subject_id: int
    name: str
    status: TopicStatus
    completed_at: datetime | None


class SubjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    color: str = Field(default="#2563eb", pattern=r"^#[0-9a-fA-F]{6}$")
    target_score: int = Field(default=75, ge=0, le=100)


class SubjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    color: str | None = Field(default=None, pattern=r"^#[0-9a-fA-F]{6}$")
    target_score: int | None = Field(default=None, ge=0, le=100)


class SubjectOut(ORMModel):
    id: int
    name: str
    color: str
    target_score: int
    topics: list[TopicOut] = []
