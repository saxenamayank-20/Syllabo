from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models import User
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    ResendCodeRequest,
    TokenResponse,
    UserOut,
    VerificationPending,
    VerifyEmailRequest,
)
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=VerificationPending, status_code=status.HTTP_201_CREATED)
def register(data: RegisterRequest, db: Session = Depends(get_db)) -> VerificationPending:
    """Create an unverified account and email a 6-digit code. No token until the email is verified."""
    return auth_service.register(db, data)


@router.post("/verify-email", response_model=TokenResponse)
def verify_email(data: VerifyEmailRequest, db: Session = Depends(get_db)) -> TokenResponse:
    return auth_service.verify_email(db, data)


@router.post("/resend-code", response_model=VerificationPending)
def resend_code(data: ResendCodeRequest, db: Session = Depends(get_db)) -> VerificationPending:
    return auth_service.resend_code(db, data)


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    return auth_service.login(db, data)


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)) -> User:
    return user
