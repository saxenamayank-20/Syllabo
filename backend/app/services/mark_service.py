from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Mark, Subject, User
from app.schemas.mark import MarkCreate, MarkUpdate
from app.services.ownership import get_owned


def list_marks(db: Session, user: User, subject_id: int | None = None) -> list[Mark]:
    stmt = select(Mark).where(Mark.user_id == user.id)
    if subject_id is not None:
        stmt = stmt.where(Mark.subject_id == subject_id)
    return list(db.scalars(stmt.order_by(Mark.assessment_date.desc(), Mark.id.desc())))


def create_mark(db: Session, user: User, data: MarkCreate) -> Mark:
    get_owned(db, Subject, data.subject_id, user)
    mark = Mark(user_id=user.id, **data.model_dump())
    db.add(mark)
    db.commit()
    db.refresh(mark)
    return mark


def update_mark(db: Session, user: User, mark_id: int, data: MarkUpdate) -> Mark:
    mark = get_owned(db, Mark, mark_id, user)
    changes = data.model_dump(exclude_unset=True, exclude_none=True)
    if "subject_id" in changes:
        get_owned(db, Subject, changes["subject_id"], user)
    score = changes.get("score", mark.score)
    max_score = changes.get("max_score", mark.max_score)
    if score > max_score:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "score cannot exceed max_score")
    for field, value in changes.items():
        setattr(mark, field, value)
    db.commit()
    db.refresh(mark)
    return mark


def delete_mark(db: Session, user: User, mark_id: int) -> None:
    db.delete(get_owned(db, Mark, mark_id, user))
    db.commit()
