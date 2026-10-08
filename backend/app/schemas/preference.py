from pydantic import BaseModel, Field, field_validator

from app.schemas.common import ORMModel

VALID_DAYS = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")


class PreferenceUpdate(BaseModel):
    daily_study_minutes: int = Field(ge=15, le=960)
    study_days: str = Field(examples=["Mon,Tue,Wed,Thu,Fri,Sat"])
    goal_note: str = ""

    @field_validator("study_days")
    @classmethod
    def normalize_days(cls, value: str) -> str:
        days = [d.strip().capitalize() for d in value.split(",") if d.strip()]
        invalid = [d for d in days if d not in VALID_DAYS]
        if invalid:
            raise ValueError(f"Invalid day(s): {', '.join(invalid)}. Use {', '.join(VALID_DAYS)}")
        if not days:
            raise ValueError("Choose at least one study day")
        # week order, no duplicates
        return ",".join(d for d in VALID_DAYS if d in days)


class PreferenceOut(ORMModel):
    daily_study_minutes: int
    study_days: str
    goal_note: str
