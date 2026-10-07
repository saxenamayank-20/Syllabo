from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]
DEFAULT_JWT_SECRET = "dev-only-insecure-jwt-secret-set-JWT_SECRET-in-env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BACKEND_DIR / ".env", extra="ignore")

    environment: Literal["development", "production"] = "development"
    database_url: str = ""
    jwt_secret: str = DEFAULT_JWT_SECRET
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24
    cors_origins: str = "http://localhost:5173"
    gemini_api_key: str = ""
    gemini_model: str = ""
    gemini_fallback_model: str = ""  # optional: tried once when the main model is busy

    # Outgoing email (verification and password-reset codes).
    #   console = print codes in the server log (local development only)
    #   brevo   = Brevo HTTP API (works on hosts that block SMTP, e.g. Render's free tier)
    #   smtp    = any SMTP server (Gmail, Brevo SMTP, SendGrid, ...)
    email_provider: Literal["console", "brevo", "smtp"] = "console"
    email_from: str = ""
    email_from_name: str = "Syllabo"
    brevo_api_key: str = ""
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    email_check_deliverability: bool = True

    # Login/sign-up attempts allowed per client IP per window (in-memory, per server process).
    auth_rate_limit: int = 10
    auth_rate_window_seconds: int = 300

    @field_validator("jwt_secret")
    @classmethod
    def blank_secret_uses_dev_default(cls, value: str) -> str:
        # An empty JWT_SECRET= line in .env shouldn't produce an empty signing key.
        return value.strip() or DEFAULT_JWT_SECRET

    @property
    def sqlalchemy_url(self) -> str:
        """Resolved DB URL: falls back to local SQLite, and forces the psycopg v3 driver for Postgres."""
        url = self.database_url.strip()
        if not url:
            return f"sqlite:///{BACKEND_DIR / 'studyai.db'}"
        if url.startswith("postgres://"):
            url = "postgresql://" + url[len("postgres://"):]
        if url.startswith("postgresql://"):
            url = "postgresql+psycopg://" + url[len("postgresql://"):]
        return url

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip().rstrip("/") for o in self.cors_origins.split(",") if o.strip()]

    @property
    def sender_address(self) -> str:
        return self.email_from or self.smtp_user

    def production_problems(self) -> list[str]:
        """Settings that are fine for local dev but unsafe or broken in production."""
        problems = []
        if self.jwt_secret == DEFAULT_JWT_SECRET or len(self.jwt_secret) < 32:
            problems.append("JWT_SECRET must be set to a random value of at least 32 characters")
        if not self.database_url:
            problems.append("DATABASE_URL must point to PostgreSQL (SQLite data is lost on redeploy)")
        if self.email_provider == "console":
            problems.append("EMAIL_PROVIDER must be 'brevo' or 'smtp' (console only prints codes to the log)")
        elif not self.sender_address:
            problems.append("EMAIL_FROM must be set to the verified sender address")
        if self.email_provider == "brevo" and not self.brevo_api_key:
            problems.append("BREVO_API_KEY is required when EMAIL_PROVIDER=brevo")
        if self.email_provider == "smtp" and not (self.smtp_user and self.smtp_password):
            problems.append("SMTP_USER and SMTP_PASSWORD are required when EMAIL_PROVIDER=smtp")
        return problems


@lru_cache
def get_settings() -> Settings:
    return Settings()
