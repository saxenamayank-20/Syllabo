from datetime import date, time

from pydantic import BaseModel, Field, field_validator, model_validator

MAX_PLAN_DAYS = 31


class PlanRange(BaseModel):
    start_date: date
    end_date: date

    @model_validator(mode="after")
    def check_range(self) -> "PlanRange":
        if self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date")
        if (self.end_date - self.start_date).days + 1 > MAX_PLAN_DAYS:
            raise ValueError(f"A plan can cover at most {MAX_PLAN_DAYS} days")
        return self


class GeneratePlanRequest(PlanRange):
    pass


# --- Shape Gemini must return -------------------------------------------------

class AITask(BaseModel):
    subject: str = Field(min_length=1)
    topic: str | None = ""
    title: str = Field(min_length=1, max_length=200)
    start_time: time
    duration_mins: int = Field(ge=5, le=960)

    @field_validator("start_time", mode="before")
    @classmethod
    def parse_hhmm(cls, value: object) -> object:
        # Accept "HH:MM" (what we ask for) as well as "HH:MM:SS"
        if isinstance(value, str) and len(value.strip()) <= 5:
            return value.strip().zfill(5)
        return value


class AIDay(BaseModel):
    date: date
    tasks: list[AITask] = []


class AIPlan(BaseModel):
    days: list[AIDay]


# --- Preview returned to the client, and what it sends back to save -------------

class PlanTaskIn(BaseModel):
    subject_id: int
    topic_id: int | None = None
    title: str = Field(min_length=1, max_length=200)
    start_time: time
    duration_mins: int = Field(ge=5, le=960)


class PlanTaskPreview(PlanTaskIn):
    subject_name: str
    subject_color: str
    topic_name: str | None = None


class PlanDayPreview(BaseModel):
    date: date
    tasks: list[PlanTaskPreview]
    total_mins: int
    available_mins: int


class SkippedItem(BaseModel):
    date: str
    title: str
    reason: str


class PlanPreview(PlanRange):
    daily_study_minutes: int
    study_days: str
    days: list[PlanDayPreview]
    skipped: list[SkippedItem]
    replaces_pending_ai_tasks: int


class PlanDayIn(BaseModel):
    date: date
    tasks: list[PlanTaskIn]


class SavePlanRequest(PlanRange):
    days: list[PlanDayIn]


class SavePlanResponse(BaseModel):
    plan_id: int
    tasks_created: int
    tasks_replaced: int
