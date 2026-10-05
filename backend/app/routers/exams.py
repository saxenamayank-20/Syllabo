from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models import Exam, User
from app.schemas.exam import ExamCreate, ExamOut, ExamUpdate
from app.services import exam_service

router = APIRouter(prefix="/exams", tags=["exams"])


@router.get("", response_model=list[ExamOut])
def list_exams(
    upcoming: bool = False,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[Exam]:
    return exam_service.list_exams(db, user, upcoming)


@router.post("", response_model=ExamOut, status_code=status.HTTP_201_CREATED)
def create_exam(
    data: ExamCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> Exam:
    return exam_service.create_exam(db, user, data)


@router.patch("/{exam_id}", response_model=ExamOut)
def update_exam(
    exam_id: int,
    data: ExamUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Exam:
    return exam_service.update_exam(db, user, exam_id, data)


@router.delete("/{exam_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_exam(
    exam_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> None:
    exam_service.delete_exam(db, user, exam_id)
