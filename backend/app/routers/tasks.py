from datetime import date

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models import StudyTask, User
from app.schemas.task import TaskCreate, TaskOut, TaskStatusUpdate
from app.services import task_service

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("", response_model=list[TaskOut])
def list_tasks(
    on_date: date | None = Query(default=None, alias="date"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[StudyTask]:
    return task_service.list_tasks(db, user, on_date)


@router.post("", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
def create_task(
    data: TaskCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> StudyTask:
    return task_service.create_task(db, user, data)


@router.patch("/{task_id}/status", response_model=TaskOut)
def set_task_status(
    task_id: int,
    data: TaskStatusUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> StudyTask:
    return task_service.set_status(db, user, task_id, data)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> None:
    task_service.delete_task(db, user, task_id)
