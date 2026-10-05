from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models import Subject, Topic, User
from app.schemas.subject import SubjectCreate, SubjectOut, SubjectUpdate, TopicCreate, TopicOut
from app.services import subject_service

router = APIRouter(prefix="/subjects", tags=["subjects"])


@router.get("", response_model=list[SubjectOut])
def list_subjects(
    db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> list[Subject]:
    return subject_service.list_subjects(db, user)


@router.post("", response_model=SubjectOut, status_code=status.HTTP_201_CREATED)
def create_subject(
    data: SubjectCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> Subject:
    return subject_service.create_subject(db, user, data)


@router.get("/{subject_id}", response_model=SubjectOut)
def get_subject(
    subject_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> Subject:
    return subject_service.get_subject(db, user, subject_id)


@router.patch("/{subject_id}", response_model=SubjectOut)
def update_subject(
    subject_id: int,
    data: SubjectUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Subject:
    return subject_service.update_subject(db, user, subject_id, data)


@router.delete("/{subject_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_subject(
    subject_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> None:
    subject_service.delete_subject(db, user, subject_id)


@router.get("/{subject_id}/topics", response_model=list[TopicOut])
def list_topics(
    subject_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> list[Topic]:
    return subject_service.list_topics(db, user, subject_id)


@router.post(
    "/{subject_id}/topics", response_model=TopicOut, status_code=status.HTTP_201_CREATED
)
def create_topic(
    subject_id: int,
    data: TopicCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Topic:
    return subject_service.create_topic(db, user, subject_id, data)
