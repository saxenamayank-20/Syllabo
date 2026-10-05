from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import StudyPreference, User
from app.schemas.preference import PreferenceUpdate


def get_or_create(db: Session, user: User) -> StudyPreference:
    pref = db.scalar(select(StudyPreference).where(StudyPreference.user_id == user.id))
    if pref is None:
        pref = StudyPreference(user_id=user.id)
        db.add(pref)
        db.commit()
        db.refresh(pref)
    return pref


def update(db: Session, user: User, data: PreferenceUpdate) -> StudyPreference:
    pref = get_or_create(db, user)
    for field, value in data.model_dump().items():
        setattr(pref, field, value)
    db.commit()
    db.refresh(pref)
    return pref
