from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

DEFAULT_STUDY_DAYS = "Mon,Tue,Wed,Thu,Fri,Sat"


class StudyPreference(Base):
    __tablename__ = "study_preferences"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True
    )
    daily_study_minutes: Mapped[int] = mapped_column(default=120)
    study_days: Mapped[str] = mapped_column(String(50), default=DEFAULT_STUDY_DAYS)
    goal_note: Mapped[str] = mapped_column(Text, default="")
