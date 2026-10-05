import hashlib
import hmac
import logging
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import create_access_token, hash_password, verify_password
from app.models import EmailVerification, User
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    ResendCodeRequest,
    TokenResponse,
    UserOut,
    VerificationPending,
    VerifyEmailRequest,
)
from app.services import email_service
from app.services.email_validation import validate_real_email

logger = logging.getLogger("studyai.auth")

CODE_TTL = timedelta(minutes=10)
RESEND_COOLDOWN = timedelta(seconds=60)
MAX_ATTEMPTS = 5
NOT_VERIFIED = "email_not_verified"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)  # SQLite drops tzinfo


def _hash_code(user_id: int, code: str) -> str:
    key = get_settings().jwt_secret.encode()
    return hmac.new(key, f"{user_id}:{code}".encode(), hashlib.sha256).hexdigest()


def _token_response(user: User) -> TokenResponse:
    return TokenResponse(access_token=create_access_token(user.id), user=UserOut.model_validate(user))


def _get_verification(db: Session, user: User) -> EmailVerification | None:
    return db.scalar(select(EmailVerification).where(EmailVerification.user_id == user.id))


def _issue_code(db: Session, user: User) -> bool:
    """Create (or replace) the user's code and email it. Returns False if sending failed."""
    code = f"{secrets.randbelow(1_000_000):06d}"
    record = _get_verification(db, user) or EmailVerification(user_id=user.id)
    record.code_hash = _hash_code(user.id, code)
    record.expires_at = _now() + CODE_TTL
    record.sent_at = _now()
    record.attempts = 0
    db.add(record)
    db.commit()
    try:
        email_service.send_verification_code(user.email, user.name, code, int(CODE_TTL.total_seconds() // 60))
    except email_service.EmailSendError:
        return False
    return True


def _pending(user: User, sent: bool) -> VerificationPending:
    message = (
        f"We sent a 6-digit code to {user.email}."
        if sent
        else "Your account is ready, but we couldn't send the verification email. Please use 'Resend code'."
    )
    return VerificationPending(email=user.email, email_sent=sent, message=message)


def register(db: Session, data: RegisterRequest) -> VerificationPending:
    email = validate_real_email(data.email)
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status.HTTP_409_CONFLICT, "An account with this email already exists")
    user = User(name=data.name.strip(), email=email, password_hash=hash_password(data.password))
    db.add(user)
    db.commit()
    return _pending(user, _issue_code(db, user))


def login(db: Session, data: LoginRequest) -> TokenResponse:
    user = db.scalar(select(User).where(User.email == data.email.lower()))
    if user is None or not verify_password(data.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Incorrect email or password")
    if not user.email_verified:
        # Send a fresh code if the old one has expired, so the user isn't stuck.
        record = _get_verification(db, user)
        if record is None or _aware(record.expires_at) <= _now():
            _issue_code(db, user)
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            {"code": NOT_VERIFIED, "message": "Please verify your email address to log in.", "email": user.email},
        )
    return _token_response(user)


def verify_email(db: Session, data: VerifyEmailRequest) -> TokenResponse:
    invalid = HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid or expired code")
    user = db.scalar(select(User).where(User.email == data.email.lower()))
    if user is None:
        raise invalid
    if user.email_verified:
        raise HTTPException(status.HTTP_409_CONFLICT, "This email is already verified. Please log in.")
    record = _get_verification(db, user)
    if record is None or _aware(record.expires_at) <= _now():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "This code has expired. Please request a new one.")
    if record.attempts >= MAX_ATTEMPTS:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Too many wrong attempts. Please request a new code.")
    if not hmac.compare_digest(record.code_hash, _hash_code(user.id, data.code)):
        record.attempts += 1
        db.commit()
        left = MAX_ATTEMPTS - record.attempts
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Incorrect code. {left} attempt{'s' if left != 1 else ''} left." if left else
            "Incorrect code. Please request a new one.",
        )
    user.email_verified = True
    db.delete(record)
    db.commit()
    return _token_response(user)


def resend_code(db: Session, data: ResendCodeRequest) -> VerificationPending:
    user = db.scalar(select(User).where(User.email == data.email.lower()))
    if user is None or user.email_verified:
        # Don't reveal whether an account exists / its state.
        return VerificationPending(
            email=data.email, email_sent=True,
            message="If this email has an unverified account, a new code has been sent.",
        )
    record = _get_verification(db, user)
    if record is not None:
        wait = RESEND_COOLDOWN - (_now() - _aware(record.sent_at))
        if wait > timedelta(0):
            raise HTTPException(
                status.HTTP_429_TOO_MANY_REQUESTS,
                f"Please wait {int(wait.total_seconds()) + 1} seconds before requesting another code.",
            )
    return _pending(user, _issue_code(db, user))
