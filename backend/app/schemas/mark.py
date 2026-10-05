from datetime import date

from pydantic import BaseModel, Field, model_validator

from app.schemas.common import ORMModel


class MarkCreate(BaseModel):
    subject_id: int
    assessment_name: str = Field(min_length=1, max_length=200)
    score: float = Field(ge=0)
    max_score: float = Field(gt=0)
    assessment_date: date

    @model_validator(mode="after")
    def score_within_max(self) -> "MarkCreate":
        if self.score > self.max_score:
            raise ValueError("score cannot exceed max_score")
        return self


class MarkUpdate(BaseModel):
    subject_id: int | None = None
    assessment_name: str | None = Field(default=None, min_length=1, max_length=200)
    score: float | None = Field(default=None, ge=0)
    max_score: float | None = Field(default=None, gt=0)
    assessment_date: date | None = None


class MarkOut(ORMModel):
    id: int
    subject_id: int
    subject_name: str
    assessment_name: str
    score: float
    max_score: float
    percentage: float
    assessment_date: date
