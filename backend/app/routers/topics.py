from fastapi import APIRouter, Body, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models import Topic, User
from app.schemas.subject import TopicOut, TopicUpdate
from app.services import subject_service

router = APIRouter(prefix="/topics", tags=["topics"])


@router.patch("/{topic_id}", response_model=TopicOut)
def update_topic(
    topic_id: int,
    data: TopicUpdate = Body(default_factory=TopicUpdate),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Topic:
    """Toggle a topic's status (empty body), set it explicitly, or rename it."""
    return subject_service.update_topic(db, user, topic_id, data)


@router.delete("/{topic_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_topic(
    topic_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> None:
    subject_service.delete_topic(db, user, topic_id)
