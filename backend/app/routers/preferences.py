from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models import StudyPreference, User
from app.schemas.preference import PreferenceOut, PreferenceUpdate
from app.services import preference_service

router = APIRouter(prefix="/preferences", tags=["preferences"])


@router.get("", response_model=PreferenceOut)
def get_preferences(
    db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> StudyPreference:
    return preference_service.get_or_create(db, user)


@router.put("", response_model=PreferenceOut)
def update_preferences(
    data: PreferenceUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> StudyPreference:
    return preference_service.update(db, user, data)
