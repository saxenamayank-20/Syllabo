from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models import Mark, User
from app.schemas.mark import MarkCreate, MarkOut, MarkUpdate
from app.services import mark_service

router = APIRouter(prefix="/marks", tags=["marks"])


@router.get("", response_model=list[MarkOut])
def list_marks(
    subject_id: int | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[Mark]:
    return mark_service.list_marks(db, user, subject_id)


@router.post("", response_model=MarkOut, status_code=status.HTTP_201_CREATED)
def create_mark(
    data: MarkCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> Mark:
    return mark_service.create_mark(db, user, data)


@router.patch("/{mark_id}", response_model=MarkOut)
def update_mark(
    mark_id: int,
    data: MarkUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Mark:
    return mark_service.update_mark(db, user, mark_id, data)


@router.delete("/{mark_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_mark(
    mark_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> None:
    mark_service.delete_mark(db, user, mark_id)
