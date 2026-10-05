from datetime import date

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class ExamCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    subject_id: int | None = None
    syllabus: str = ""
    exam_date: date


class ExamUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    subject_id: int | None = None
    syllabus: str | None = None
    exam_date: date | None = None


class ExamOut(ORMModel):
    id: int
    title: str
    subject_id: int | None
    syllabus: str
    exam_date: date
