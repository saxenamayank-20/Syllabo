from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Exam, Subject, User
from app.schemas.exam import ExamCreate, ExamUpdate
from app.services.ownership import get_owned


def _check_subject(db: Session, user: User, subject_id: int | None) -> None:
    if subject_id is not None:
        get_owned(db, Subject, subject_id, user)


def list_exams(db: Session, user: User, upcoming: bool = False) -> list[Exam]:
    stmt = select(Exam).where(Exam.user_id == user.id)
    if upcoming:
        stmt = stmt.where(Exam.exam_date >= date.today())
    return list(db.scalars(stmt.order_by(Exam.exam_date, Exam.id)))


def create_exam(db: Session, user: User, data: ExamCreate) -> Exam:
    _check_subject(db, user, data.subject_id)
    exam = Exam(user_id=user.id, **data.model_dump())
    db.add(exam)
    db.commit()
    db.refresh(exam)
    return exam


def update_exam(db: Session, user: User, exam_id: int, data: ExamUpdate) -> Exam:
    exam = get_owned(db, Exam, exam_id, user)
    changes = data.model_dump(exclude_unset=True)
    if "subject_id" in changes:
        _check_subject(db, user, changes["subject_id"])
    for field, value in changes.items():
        if value is not None or field == "subject_id":
            setattr(exam, field, value)
    db.commit()
    db.refresh(exam)
    return exam


def delete_exam(db: Session, user: User, exam_id: int) -> None:
    db.delete(get_owned(db, Exam, exam_id, user))
    db.commit()
