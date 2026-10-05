from datetime import date

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import StudyTask, Subject, User
from app.schemas.task import TaskCreate, TaskStatusUpdate
from app.services.ownership import get_owned, get_owned_topic


def list_tasks(db: Session, user: User, on_date: date | None = None) -> list[StudyTask]:
    stmt = select(StudyTask).where(StudyTask.user_id == user.id)
    if on_date is not None:
        stmt = stmt.where(StudyTask.scheduled_date == on_date)
    stmt = stmt.order_by(StudyTask.scheduled_date, StudyTask.start_time, StudyTask.id)
    return list(db.scalars(stmt))


def create_task(db: Session, user: User, data: TaskCreate) -> StudyTask:
    get_owned(db, Subject, data.subject_id, user)
    if data.topic_id is not None:
        topic = get_owned_topic(db, data.topic_id, user)
        if topic.subject_id != data.subject_id:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_CONTENT, "Topic does not belong to this subject"
            )
    task = StudyTask(user_id=user.id, source="manual", **data.model_dump())
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def set_status(db: Session, user: User, task_id: int, data: TaskStatusUpdate) -> StudyTask:
    task = get_owned(db, StudyTask, task_id, user)
    task.status = data.status
    db.commit()
    db.refresh(task)
    return task


def delete_task(db: Session, user: User, task_id: int) -> None:
    db.delete(get_owned(db, StudyTask, task_id, user))
    db.commit()
