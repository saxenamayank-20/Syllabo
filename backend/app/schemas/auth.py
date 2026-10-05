from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.core.timezones import is_valid_timezone
from app.schemas.common import ORMModel

Password = Field(min_length=6, max_length=72)
Code = Field(pattern=r"^\d{6}$")


def _check_timezone(value: str | None) -> str | None:
    if value is not None and not is_valid_timezone(value):
        raise ValueError("Unknown timezone")
    return value


class RegisterRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    password: str = Password
    timezone: str = "UTC"  # the browser's zone; unknown values fall back to UTC rather than block sign-up

    @field_validator("timezone")
    @classmethod
    def default_unknown_timezone(cls, value: str) -> str:
        return value if is_valid_timezone(value) else "UTC"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class VerifyEmailRequest(BaseModel):
    email: EmailStr
    code: str = Code


class EmailRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    email: EmailStr
    code: str = Code
    new_password: str = Password


class ProfileUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    timezone: str | None = None

    _tz = field_validator("timezone")(_check_timezone)


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Password


class UserOut(ORMModel):
    id: int
    name: str
    email: EmailStr
    email_verified: bool
    timezone: str
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class CodeSent(BaseModel):
    """Returned when a one-time code was (or may have been) emailed."""

    email: EmailStr
    email_sent: bool
    message: str
