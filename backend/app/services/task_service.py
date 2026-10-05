from datetime import date

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import StudyTask, Subject, User
from app.schemas.task import TaskCreate, TaskStatusUpdate, TaskUpdate
from app.services.ownership import get_owned, get_owned_topic


def list_tasks(db: Session, user: User, on_date: date | None = None) -> list[StudyTask]:
    stmt = select(StudyTask).where(StudyTask.user_id == user.id)
    if on_date is not None:
        stmt = stmt.where(StudyTask.scheduled_date == on_date)
    stmt = stmt.order_by(StudyTask.scheduled_date, StudyTask.start_time, StudyTask.id)
    return list(db.scalars(stmt))


def _check_subject_topic(db: Session, user: User, subject_id: int, topic_id: int | None) -> None:
    get_owned(db, Subject, subject_id, user)
    if topic_id is not None:
        topic = get_owned_topic(db, topic_id, user)
        if topic.subject_id != subject_id:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_CONTENT, "Topic does not belong to this subject"
            )


def create_task(db: Session, user: User, data: TaskCreate) -> StudyTask:
    _check_subject_topic(db, user, data.subject_id, data.topic_id)
    task = StudyTask(user_id=user.id, source="manual", **data.model_dump())
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def update_task(db: Session, user: User, task_id: int, data: TaskUpdate) -> StudyTask:
    task = get_owned(db, StudyTask, task_id, user)
    changes = data.model_dump(exclude_unset=True)
    # title/date/duration/subject can't be cleared; topic and start time can.
    for field in ("subject_id", "title", "scheduled_date", "duration_mins"):
        if changes.get(field, ...) is None:
            changes.pop(field)
    subject_id = changes.get("subject_id", task.subject_id)
    topic_id = changes.get("topic_id", None if "subject_id" in changes else task.topic_id)
    _check_subject_topic(db, user, subject_id, topic_id)
    for field, value in changes.items():
        setattr(task, field, value)
    task.topic_id = topic_id
    task.source = "manual"  # an edited AI task is the student's now; regenerating won't replace it
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
