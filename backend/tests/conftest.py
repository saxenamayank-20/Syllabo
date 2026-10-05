from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.core.config import get_settings
from app.core.database import Base, get_db
from app.main import app
from app.services import email_service

SENT_CODES: dict[str, str] = {}


@pytest.fixture(autouse=True)
def fake_email(monkeypatch: pytest.MonkeyPatch) -> dict[str, str]:
    """Capture verification codes instead of sending mail; skip DNS lookups."""
    SENT_CODES.clear()
    monkeypatch.setattr(get_settings(), "email_check_deliverability", False)
    monkeypatch.setattr(
        email_service, "send_verification_code",
        lambda to, name, code, minutes: SENT_CODES.__setitem__(to, code),
    )
    return SENT_CODES


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    event.listen(engine, "connect", lambda conn, _: conn.execute("PRAGMA foreign_keys=ON"))
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def override_get_db() -> Generator[Session, None, None]:
        db = TestSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    engine.dispose()


def register(client: TestClient, email: str = "student@gmail.com") -> dict[str, str]:
    """Register and verify a user; return auth headers."""
    res = client.post(
        "/auth/register", json={"name": "Test Student", "email": email, "password": "secret123"}
    )
    assert res.status_code == 201, res.text
    res = client.post("/auth/verify-email", json={"email": email, "code": SENT_CODES[email]})
    assert res.status_code == 200, res.text
    return {"Authorization": f"Bearer {res.json()['access_token']}"}
