import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import create_access_token, hash_password, verify_password
from app.models import AuthCode, User
from app.schemas.auth import (
    ChangePasswordRequest,
    CodeSent,
    EmailRequest,
    LoginRequest,
    ProfileUpdate,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserOut,
    VerifyEmailRequest,
)
from app.services import email_service
from app.services.email_service import CodePurpose
from app.services.email_validation import validate_real_email

CODE_TTL = timedelta(minutes=10)
RESEND_COOLDOWN = timedelta(seconds=60)
MAX_ATTEMPTS = 5
NOT_VERIFIED = "email_not_verified"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)  # sqlite drops tzinfo


def _hash_code(user_id: int, purpose: str, code: str) -> str:
    key = get_settings().jwt_secret.encode()
    return hmac.new(key, f"{user_id}:{purpose}:{code}".encode(), hashlib.sha256).hexdigest()


def _token_response(user: User) -> TokenResponse:
    return TokenResponse(access_token=create_access_token(user), user=UserOut.model_validate(user))


def _find_user(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email.lower()))


def _get_code(db: Session, user: User, purpose: CodePurpose) -> AuthCode | None:
    return db.scalar(select(AuthCode).where(AuthCode.user_id == user.id, AuthCode.purpose == purpose))


def _cooldown_left(record: AuthCode | None) -> timedelta:
    if record is None:
        return timedelta(0)
    return max(RESEND_COOLDOWN - (_now() - _aware(record.sent_at)), timedelta(0))


def _issue_code(db: Session, user: User, purpose: CodePurpose) -> bool:
    """make a new code and email it. False if the email didn't go out"""
    code = f"{secrets.randbelow(1_000_000):06d}"
    record = _get_code(db, user, purpose) or AuthCode(user_id=user.id, purpose=purpose)
    record.code_hash = _hash_code(user.id, purpose, code)
    record.expires_at = _now() + CODE_TTL
    record.sent_at = _now()
    record.attempts = 0
    db.add(record)
    db.commit()
    try:
        email_service.send_code(user.email, user.name, code, int(CODE_TTL.total_seconds() // 60), purpose)
    except email_service.EmailSendError:
        return False
    return True


def _consume_code(db: Session, user: User, purpose: CodePurpose, code: str) -> None:
    """check the code. right = delete it, wrong = count the attempt"""
    record = _get_code(db, user, purpose)
    if record is None or _aware(record.expires_at) <= _now():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "This code has expired. Please request a new one.")
    if record.attempts >= MAX_ATTEMPTS:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Too many wrong attempts. Please request a new code.")
    if not hmac.compare_digest(record.code_hash, _hash_code(user.id, purpose, code)):
        record.attempts += 1
        db.commit()
        left = MAX_ATTEMPTS - record.attempts
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Incorrect code. {left} attempt{'s' if left != 1 else ''} left."
            if left else "Incorrect code. Please request a new one.",
        )
    db.delete(record)


def _code_sent(user: User, sent: bool) -> CodeSent:
    message = (
        f"We sent a 6-digit code to {user.email}."
        if sent
        else "We couldn't send the email right now. Please try 'Resend code' in a minute."
    )
    return CodeSent(email=user.email, email_sent=sent, message=message)


# signup + verification

def register(db: Session, data: RegisterRequest) -> CodeSent:
    email = validate_real_email(data.email)
    if _find_user(db, email):
        raise HTTPException(status.HTTP_409_CONFLICT, "An account with this email already exists")
    user = User(
        name=data.name.strip(), email=email, password_hash=hash_password(data.password), timezone=data.timezone
    )
    db.add(user)
    db.commit()
    return _code_sent(user, _issue_code(db, user, "verify"))


def verify_email(db: Session, data: VerifyEmailRequest) -> TokenResponse:
    user = _find_user(db, data.email)
    if user is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid or expired code")
    if user.email_verified:
        raise HTTPException(status.HTTP_409_CONFLICT, "This email is already verified. Please log in.")
    _consume_code(db, user, "verify", data.code)
    user.email_verified = True
    db.commit()
    return _token_response(user)


def resend_verification(db: Session, data: EmailRequest) -> CodeSent:
    user = _find_user(db, data.email)
    if user is None or user.email_verified:
        # don't leak whether the account exists
        return CodeSent(
            email=data.email, email_sent=True,
            message="If this email has an unverified account, a new code has been sent.",
        )
    wait = _cooldown_left(_get_code(db, user, "verify"))
    if wait:
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            f"Please wait {int(wait.total_seconds()) + 1} seconds before requesting another code.",
        )
    return _code_sent(user, _issue_code(db, user, "verify"))


def login(db: Session, data: LoginRequest) -> TokenResponse:
    user = _find_user(db, data.email)
    if user is None or not verify_password(data.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Incorrect email or password")
    if not user.email_verified:
        # old code expired, send a new one so they aren't stuck
        record = _get_code(db, user, "verify")
        if record is None or _aware(record.expires_at) <= _now():
            _issue_code(db, user, "verify")
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            {"code": NOT_VERIFIED, "message": "Please verify your email address to log in.", "email": user.email},
        )
    return _token_response(user)


# password reset

def forgot_password(db: Session, data: EmailRequest) -> CodeSent:
    generic = CodeSent(
        email=data.email, email_sent=True,
        message=f"If an account exists for {data.email}, we've sent a password reset code.",
    )
    user = _find_user(db, data.email)
    if user is None:
        return generic  # don't reveal which emails have accounts
    wait = _cooldown_left(_get_code(db, user, "reset"))
    if wait:
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            f"Please wait {int(wait.total_seconds()) + 1} seconds before requesting another code.",
        )
    if not _issue_code(db, user, "reset"):
        return _code_sent(user, False)
    return generic


def reset_password(db: Session, data: ResetPasswordRequest) -> TokenResponse:
    user = _find_user(db, data.email)
    if user is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "This code has expired. Please request a new one.")
    _consume_code(db, user, "reset", data.code)
    user.password_hash = hash_password(data.new_password)
    user.token_version += 1  # logs out every session
    user.email_verified = True  # they got the code, so the inbox is theirs
    db.commit()
    return _token_response(user)


# account settings

def update_profile(db: Session, user: User, data: ProfileUpdate) -> User:
    if data.name is not None:
        user.name = data.name.strip()
    if data.timezone is not None:
        user.timezone = data.timezone
    db.commit()
    db.refresh(user)
    return user


def change_password(db: Session, user: User, data: ChangePasswordRequest) -> TokenResponse:
    if not verify_password(data.current_password, user.password_hash):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Your current password is incorrect")
    if data.current_password == data.new_password:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "The new password must be different")
    user.password_hash = hash_password(data.new_password)
    user.token_version += 1  # other devices get logged out, this one gets a new token
    db.commit()
    return _token_response(user)
