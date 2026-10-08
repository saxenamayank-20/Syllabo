from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.rate_limit import rate_limit
from app.core.security import get_current_user
from app.models import User
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
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])

# separate buckets so wrong codes don't block logging in
login_limit = Depends(rate_limit("login"))
code_limit = Depends(rate_limit("code"))
send_limit = Depends(rate_limit("send"))


@router.post(
    "/register", response_model=CodeSent, status_code=status.HTTP_201_CREATED, dependencies=[send_limit]
)
def register(data: RegisterRequest, db: Session = Depends(get_db)) -> CodeSent:
    """make an unverified account and email a code. no token until it's verified"""
    return auth_service.register(db, data)


@router.post("/verify-email", response_model=TokenResponse, dependencies=[code_limit])
def verify_email(data: VerifyEmailRequest, db: Session = Depends(get_db)) -> TokenResponse:
    return auth_service.verify_email(db, data)


@router.post("/resend-code", response_model=CodeSent, dependencies=[send_limit])
def resend_code(data: EmailRequest, db: Session = Depends(get_db)) -> CodeSent:
    return auth_service.resend_verification(db, data)


@router.post("/login", response_model=TokenResponse, dependencies=[login_limit])
def login(data: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    return auth_service.login(db, data)


@router.post("/forgot-password", response_model=CodeSent, dependencies=[send_limit])
def forgot_password(data: EmailRequest, db: Session = Depends(get_db)) -> CodeSent:
    """email a reset code (same reply whether the account exists or not)"""
    return auth_service.forgot_password(db, data)


@router.post("/reset-password", response_model=TokenResponse, dependencies=[code_limit])
def reset_password(data: ResetPasswordRequest, db: Session = Depends(get_db)) -> TokenResponse:
    """new password from the emailed code, logs out other sessions"""
    return auth_service.reset_password(db, data)


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)) -> User:
    return user


@router.patch("/me", response_model=UserOut)
def update_me(
    data: ProfileUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> User:
    return auth_service.update_profile(db, user, data)


@router.post("/change-password", response_model=TokenResponse, dependencies=[login_limit])
def change_password(
    data: ChangePasswordRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)
) -> TokenResponse:
    """change password, returns a new token and logs out other sessions"""
    return auth_service.change_password(db, user, data)
