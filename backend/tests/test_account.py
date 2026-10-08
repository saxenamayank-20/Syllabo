from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings, get_settings
from tests.conftest import register

EMAIL = "student@gmail.com"


def test_forgot_and_reset_password(client: TestClient, fake_email: dict) -> None:
    old_headers = register(client)
    res = client.post("/auth/forgot-password", json={"email": EMAIL})
    assert res.status_code == 200
    code = fake_email[EMAIL]

    wrong = client.post("/auth/reset-password", json={"email": EMAIL, "code": "000000" if code != "000000" else "111111", "new_password": "newpass99"})
    assert wrong.status_code == 400

    res = client.post("/auth/reset-password", json={"email": EMAIL, "code": code, "new_password": "newpass99"})
    assert res.status_code == 200 and res.json()["access_token"]

    assert client.get("/auth/me", headers=old_headers).status_code == 401  # old sessions ended
    assert client.post("/auth/login", json={"email": EMAIL, "password": "secret123"}).status_code == 401
    assert client.post("/auth/login", json={"email": EMAIL, "password": "newpass99"}).status_code == 200
    # Code is single use
    again = client.post("/auth/reset-password", json={"email": EMAIL, "code": code, "new_password": "another1"})
    assert again.status_code == 400


def test_forgot_password_does_not_reveal_accounts(client: TestClient, fake_email: dict) -> None:
    res = client.post("/auth/forgot-password", json={"email": "nobody@gmail.com"})
    assert res.status_code == 200
    assert "nobody@gmail.com" not in fake_email  # nothing sent


def test_forgot_password_cooldown(client: TestClient) -> None:
    register(client)
    assert client.post("/auth/forgot-password", json={"email": EMAIL}).status_code == 200
    assert client.post("/auth/forgot-password", json={"email": EMAIL}).status_code == 429


def test_reset_verifies_unverified_account(client: TestClient, fake_email: dict) -> None:
    client.post("/auth/register", json={"name": "U", "email": EMAIL, "password": "secret123"})
    client.post("/auth/forgot-password", json={"email": EMAIL})
    res = client.post("/auth/reset-password", json={"email": EMAIL, "code": fake_email[EMAIL], "new_password": "newpass99"})
    assert res.status_code == 200 and res.json()["user"]["email_verified"] is True


def test_profile_update_and_change_password(client: TestClient) -> None:
    headers = register(client)
    res = client.patch("/auth/me", json={"name": "New Name", "timezone": "Asia/Kolkata"}, headers=headers)
    assert res.json()["name"] == "New Name" and res.json()["timezone"] == "Asia/Kolkata"
    assert client.patch("/auth/me", json={"timezone": "Mars/Olympus"}, headers=headers).status_code == 422

    bad = client.post("/auth/change-password", json={"current_password": "wrong", "new_password": "newpass99"}, headers=headers)
    assert bad.status_code == 400
    res = client.post("/auth/change-password", json={"current_password": "secret123", "new_password": "newpass99"}, headers=headers)
    assert res.status_code == 200
    new_headers = {"Authorization": f"Bearer {res.json()['access_token']}"}
    assert client.get("/auth/me", headers=headers).status_code == 401  # other sessions logged out
    assert client.get("/auth/me", headers=new_headers).status_code == 200


def test_login_rate_limited(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    register(client)
    monkeypatch.setattr(get_settings(), "auth_rate_limit", 3)
    for _ in range(3):
        assert client.post("/auth/login", json={"email": EMAIL, "password": "bad"}).status_code == 401
    res = client.post("/auth/login", json={"email": EMAIL, "password": "secret123"})
    assert res.status_code == 429 and "Retry-After" in res.headers


def test_today_follows_user_timezone(client: TestClient) -> None:
    headers = register(client)
    tz = "Pacific/Kiritimati"  # UTC+14: often a different date than the server
    client.patch("/auth/me", json={"timezone": tz}, headers=headers)
    local_today = datetime.now(ZoneInfo(tz)).date()
    sid = client.post("/subjects", json={"name": "Math"}, headers=headers).json()["id"]
    client.post("/tasks", json={"subject_id": sid, "title": "T", "scheduled_date": local_today.isoformat()}, headers=headers)
    client.post("/exams", json={"title": "E", "exam_date": (local_today + timedelta(days=3)).isoformat()}, headers=headers)
    summary = client.get("/dashboard/summary", headers=headers).json()
    assert summary["today_tasks_total"] == 1
    assert summary["days_to_next_exam"] == 3


def test_edit_task_and_mark(client: TestClient) -> None:
    headers = register(client)
    sid = client.post("/subjects", json={"name": "Math"}, headers=headers).json()["id"]
    other = client.post("/subjects", json={"name": "Physics"}, headers=headers).json()["id"]
    tid = client.post(f"/subjects/{sid}/topics", json={"name": "Algebra"}, headers=headers).json()["id"]
    task = client.post("/tasks", json={"subject_id": sid, "topic_id": tid, "title": "Old", "scheduled_date": date.today().isoformat(), "start_time": "09:00"}, headers=headers).json()

    res = client.patch(f"/tasks/{task['id']}", json={"title": "New", "duration_mins": 90, "start_time": None}, headers=headers)
    assert res.status_code == 200
    body = res.json()
    assert body["title"] == "New" and body["duration_mins"] == 90 and body["start_time"] is None
    assert body["topic_id"] == tid
    # changing subject clears the topic, a topic from another subject is rejected
    assert client.patch(f"/tasks/{task['id']}", json={"subject_id": other}, headers=headers).json()["topic_id"] is None
    assert client.patch(f"/tasks/{task['id']}", json={"topic_id": tid}, headers=headers).status_code == 422

    mark = client.post("/marks", json={"subject_id": sid, "assessment_name": "Q1", "score": 10, "max_score": 20, "assessment_date": date.today().isoformat()}, headers=headers).json()
    res = client.patch(f"/marks/{mark['id']}", json={"score": 18}, headers=headers)
    assert res.json()["percentage"] == 90.0
    assert client.patch(f"/marks/{mark['id']}", json={"score": 25}, headers=headers).status_code == 422

    exam = client.post("/exams", json={"title": "E", "exam_date": date.today().isoformat()}, headers=headers).json()
    assert client.patch(f"/exams/{exam['id']}", json={"title": "Final"}, headers=headers).json()["title"] == "Final"


def test_production_settings_are_checked() -> None:
    problems = Settings(_env_file=None, environment="production").production_problems()
    assert any("JWT_SECRET" in p for p in problems)
    assert any("DATABASE_URL" in p for p in problems)
    assert any("EMAIL_PROVIDER" in p for p in problems)
    ok = Settings(
        _env_file=None, environment="production", jwt_secret="x" * 40,
        database_url="postgresql://u:p@host/db", email_provider="brevo",
        brevo_api_key="key", email_from="team@client.com",
    )
    assert ok.production_problems() == []


@pytest.mark.parametrize("raw", [
    "https://a.vercel.app,https://b.vercel.app",
    '"https://a.vercel.app, https://b.vercel.app/"',
    "https://a.vercel.app\nhttps://b.vercel.app",
    "https://a.vercel.app; https://b.vercel.app",
])
def test_cors_origins_tolerate_pasting_mistakes(raw: str) -> None:
    assert Settings(_env_file=None, cors_origins=raw).cors_origin_list == [
        "https://a.vercel.app", "https://b.vercel.app",
    ]
