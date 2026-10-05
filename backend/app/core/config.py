from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BACKEND_DIR / ".env", extra="ignore")

    database_url: str = ""
    jwt_secret: str = "dev-only-insecure-jwt-secret-set-JWT_SECRET-in-env"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24
    cors_origins: str = "http://localhost:5173"
    gemini_api_key: str = ""
    gemini_model: str = ""

    # Email verification (Gmail SMTP by default). With no SMTP_USER, codes are printed to the server log.
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from_name: str = "StudyAI"
    email_check_deliverability: bool = True

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
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
