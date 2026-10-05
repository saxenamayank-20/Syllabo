from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Subject, Topic, User
from app.schemas.subject import SubjectCreate, SubjectUpdate, TopicCreate, TopicUpdate
from app.services.ownership import get_owned, get_owned_topic


def list_subjects(db: Session, user: User) -> list[Subject]:
    stmt = (
        select(Subject)
        .where(Subject.user_id == user.id)
        .options(selectinload(Subject.topics))
        .order_by(Subject.name)
    )
    return list(db.scalars(stmt))


def get_subject(db: Session, user: User, subject_id: int) -> Subject:
    return get_owned(db, Subject, subject_id, user)


def create_subject(db: Session, user: User, data: SubjectCreate) -> Subject:
    subject = Subject(user_id=user.id, **data.model_dump())
    db.add(subject)
    db.commit()
    db.refresh(subject)
    return subject


def update_subject(db: Session, user: User, subject_id: int, data: SubjectUpdate) -> Subject:
    subject = get_owned(db, Subject, subject_id, user)
    for field, value in data.model_dump(exclude_unset=True, exclude_none=True).items():
        setattr(subject, field, value)
    db.commit()
    db.refresh(subject)
    return subject


def delete_subject(db: Session, user: User, subject_id: int) -> None:
    db.delete(get_owned(db, Subject, subject_id, user))
    db.commit()


def list_topics(db: Session, user: User, subject_id: int) -> list[Topic]:
    return get_owned(db, Subject, subject_id, user).topics


def create_topic(db: Session, user: User, subject_id: int, data: TopicCreate) -> Topic:
    subject = get_owned(db, Subject, subject_id, user)
    topic = Topic(subject_id=subject.id, name=data.name.strip())
    db.add(topic)
    db.commit()
    db.refresh(topic)
    return topic


def update_topic(db: Session, user: User, topic_id: int, data: TopicUpdate) -> Topic:
    topic = get_owned_topic(db, topic_id, user)
    if data.name is not None:
        topic.name = data.name.strip()
    if "name" not in data.model_fields_set or "status" in data.model_fields_set:
        new_status = data.status or ("pending" if topic.status == "completed" else "completed")
        if new_status != topic.status:
            topic.status = new_status
            topic.completed_at = datetime.now(timezone.utc) if new_status == "completed" else None
    db.commit()
    db.refresh(topic)
    return topic


def delete_topic(db: Session, user: User, topic_id: int) -> None:
    db.delete(get_owned_topic(db, topic_id, user))
    db.commit()
