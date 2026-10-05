"""Lookup helpers that enforce per-user data scoping. Anything not owned by the user is a 404."""

from typing import TypeVar

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Exam, Mark, StudyTask, Subject, Topic, User

T = TypeVar("T", Exam, Mark, StudyTask, Subject)


def not_found(entity: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{entity} not found")


def get_owned(db: Session, model: type[T], obj_id: int, user: User) -> T:
    obj = db.get(model, obj_id)
    if obj is None or obj.user_id != user.id:
        raise not_found(model.__name__.replace("Study", ""))
    return obj


def get_owned_topic(db: Session, topic_id: int, user: User) -> Topic:
    topic = db.scalar(
        select(Topic).join(Subject).where(Topic.id == topic_id, Subject.user_id == user.id)
    )
    if topic is None:
        raise not_found("Topic")
    return topic
