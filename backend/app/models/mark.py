from datetime import date

from sqlalchemy import Date, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.subject import Subject


class Mark(Base):
    __tablename__ = "marks"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    subject_id: Mapped[int] = mapped_column(
        ForeignKey("subjects.id", ondelete="CASCADE"), index=True
    )
    assessment_name: Mapped[str] = mapped_column(String(200))
    score: Mapped[float]
    max_score: Mapped[float]
    assessment_date: Mapped[date] = mapped_column(Date)

    subject: Mapped[Subject] = relationship(lazy="joined")

    @property
    def subject_name(self) -> str:
        return self.subject.name

    @property
    def percentage(self) -> float:
        return round(self.score / self.max_score * 100, 1)
