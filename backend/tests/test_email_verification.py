from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import update

from app.core.database import get_db
from app.models import AuthCode
from app.services import email_validation

EMAIL = "riya@gmail.com"
SIGNUP = {"name": "Riya", "email": EMAIL, "password": "secret123"}


def signup(client: TestClient) -> dict:
    res = client.post("/auth/register", json=SIGNUP)
    assert res.status_code == 201, res.text
    return res.json()


def test_register_sends_code_and_returns_no_token(client: TestClient, fake_email: dict) -> None:
    body = signup(client)
    assert body["email_sent"] is True
    assert "access_token" not in body
    assert len(fake_email[EMAIL]) == 6 and fake_email[EMAIL].isdigit()


def test_login_blocked_until_verified(client: TestClient, fake_email: dict) -> None:
    signup(client)
    res = client.post("/auth/login", json={"email": EMAIL, "password": "secret123"})
    assert res.status_code == 403
    assert res.json()["detail"]["code"] == "email_not_verified"

    res = client.post("/auth/verify-email", json={"email": EMAIL, "code": fake_email[EMAIL]})
    assert res.status_code == 200
    assert res.json()["user"]["email_verified"] is True

    assert client.post("/auth/login", json={"email": EMAIL, "password": "secret123"}).status_code == 200
    # Code is single-use
    again = client.post("/auth/verify-email", json={"email": EMAIL, "code": fake_email[EMAIL]})
    assert again.status_code == 409


def test_wrong_code_attempts_are_limited(client: TestClient, fake_email: dict) -> None:
    signup(client)
    good = fake_email[EMAIL]
    wrong = "000000" if good != "000000" else "111111"
    for left in (4, 3, 2, 1):
        res = client.post("/auth/verify-email", json={"email": EMAIL, "code": wrong})
        assert res.status_code == 400 and f"{left} attempt" in res.json()["detail"]
    client.post("/auth/verify-email", json={"email": EMAIL, "code": wrong})
    # Even the right code is refused after 5 failures
    res = client.post("/auth/verify-email", json={"email": EMAIL, "code": good})
    assert res.status_code == 429


def test_resend_cooldown_and_new_code(client: TestClient, fake_email: dict) -> None:
    signup(client)
    first = fake_email[EMAIL]
    assert client.post("/auth/resend-code", json={"email": EMAIL}).status_code == 429

    # Pretend the code was sent 2 minutes ago
    db = next(client.app.dependency_overrides[get_db]())
    db.execute(update(AuthCode).values(sent_at=datetime.now(timezone.utc) - timedelta(minutes=2)))
    db.commit()

    assert client.post("/auth/resend-code", json={"email": EMAIL}).status_code == 200
    if fake_email[EMAIL] != first:  # (1-in-a-million chance the new code is identical)
        assert client.post("/auth/verify-email", json={"email": EMAIL, "code": first}).status_code == 400
    assert client.post("/auth/verify-email", json={"email": EMAIL, "code": fake_email[EMAIL]}).status_code == 200


def test_expired_code_rejected(client: TestClient, fake_email: dict) -> None:
    signup(client)
    db = next(client.app.dependency_overrides[get_db]())
    db.execute(update(AuthCode).values(expires_at=datetime.now(timezone.utc) - timedelta(seconds=1)))
    db.commit()
    res = client.post("/auth/verify-email", json={"email": EMAIL, "code": fake_email[EMAIL]})
    assert res.status_code == 400 and "expired" in res.json()["detail"]


def test_resend_for_unknown_email_reveals_nothing(client: TestClient) -> None:
    res = client.post("/auth/resend-code", json={"email": "nobody@gmail.com"})
    assert res.status_code == 200


@pytest.mark.parametrize("email", ["x@mailinator.com", "x@yopmail.com", "x@sub.guerrillamail.com"])
def test_disposable_domains_rejected(client: TestClient, email: str) -> None:
    res = client.post("/auth/register", json={**SIGNUP, "email": email})
    assert res.status_code == 422
    assert "disposable" in res.json()["detail"]


def test_undeliverable_domain_rejected(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    import email_validator

    from app.core.config import get_settings

    real_validate = email_validator.validate_email

    def no_mx(email: str, **kwargs):
        if kwargs.get("check_deliverability"):
            raise email_validator.EmailUndeliverableError("no MX")
        return real_validate(email, **kwargs)

    monkeypatch.setattr(get_settings(), "email_check_deliverability", True)
    monkeypatch.setattr(email_validation.email_validator, "validate_email", no_mx)
    res = client.post("/auth/register", json={**SIGNUP, "email": "x@not-a-real-domain-zz.com"})
    assert res.status_code == 422
    assert "can't receive mail" in res.json()["detail"]
