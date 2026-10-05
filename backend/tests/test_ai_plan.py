import json
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from app.services import gemini_service
from tests.conftest import register


def next_weekday(weekday: int) -> date:
    """Next date (after today) falling on `weekday` (Mon=0)."""
    d = date.today() + timedelta(days=1)
    while d.weekday() != weekday:
        d += timedelta(days=1)
    return d


@pytest.fixture()
def setup(client: TestClient) -> dict:
    headers = register(client)
    client.put(
        "/preferences",
        json={"daily_study_minutes": 120, "study_days": "Mon,Tue,Wed", "goal_note": "Pass"},
        headers=headers,
    )
    subject = client.post("/subjects", json={"name": "Physics"}, headers=headers).json()
    topic = client.post(
        f"/subjects/{subject['id']}/topics", json={"name": "Optics"}, headers=headers
    ).json()
    monday = next_weekday(0)
    return {"headers": headers, "subject": subject, "topic": topic, "monday": monday}


def fake_gemini(monkeypatch: pytest.MonkeyPatch, *responses: str) -> list[str]:
    prompts: list[str] = []
    queue = list(responses)

    def generate_json(prompt: str) -> str:
        prompts.append(prompt)
        return queue.pop(0)

    monkeypatch.setattr(gemini_service, "generate_json", generate_json)
    return prompts


def plan_json(monday: date) -> str:
    sunday = monday + timedelta(days=6)
    task = lambda subject, topic, mins, t="09:00": {  # noqa: E731
        "subject": subject, "topic": topic, "title": f"{subject} {topic}".strip(),
        "start_time": t, "duration_mins": mins,
    }
    return json.dumps({"days": [
        {"date": monday.isoformat(), "tasks": [
            task("physics", "Optics", 60),           # case-insensitive match
            task("Physics", "", 45, "10:30"),        # general revision, no topic
            task("Physics", "", 30, "12:00"),        # exceeds 120 min/day -> skipped
        ]},
        {"date": (monday + timedelta(days=1)).isoformat(), "tasks": [
            task("Biology", "Cells", 30),            # unknown subject -> skipped
            task("Physics", "Thermo", 30),           # unknown topic -> skipped
        ]},
        {"date": sunday.isoformat(), "tasks": [task("Physics", "", 30)]},  # not a study day
    ]})


def test_generate_preview_maps_and_enforces_rules(client: TestClient, setup: dict, monkeypatch) -> None:
    monday = setup["monday"]
    prompts = fake_gemini(monkeypatch, plan_json(monday))
    res = client.post(
        "/ai/generate-plan",
        json={"start_date": monday.isoformat(), "end_date": (monday + timedelta(days=6)).isoformat()},
        headers=setup["headers"],
    )
    assert res.status_code == 200, res.text
    preview = res.json()

    assert [d["date"] for d in preview["days"]] == [
        (monday + timedelta(days=i)).isoformat() for i in range(3)
    ]  # Mon, Tue, Wed only
    first = preview["days"][0]
    assert [t["duration_mins"] for t in first["tasks"]] == [60, 45]
    assert first["tasks"][0]["topic_id"] == setup["topic"]["id"]
    assert first["tasks"][1]["topic_id"] is None
    assert first["total_mins"] <= 120
    reasons = " | ".join(s["reason"] for s in preview["skipped"])
    assert "daily study minutes" in reasons
    assert "Unknown subject" in reasons and "Unknown topic" in reasons
    assert "not one of your study days" in reasons

    # Prompt carries the context Gemini needs
    assert "Physics" in prompts[0] and "Optics" in prompts[0] and "120 min" in prompts[0]


def test_invalid_response_retries_once_then_errors(client: TestClient, setup: dict, monkeypatch) -> None:
    monday = setup["monday"]
    body = {"start_date": monday.isoformat(), "end_date": monday.isoformat()}

    prompts = fake_gemini(monkeypatch, "not json", plan_json(monday))
    assert client.post("/ai/generate-plan", json=body, headers=setup["headers"]).status_code == 200
    assert len(prompts) == 2

    prompts = fake_gemini(monkeypatch, "not json", '{"days": [{"date": "bad"}]}')
    res = client.post("/ai/generate-plan", json=body, headers=setup["headers"])
    assert res.status_code == 502
    assert len(prompts) == 2


def test_rate_limit_is_friendly(client: TestClient, setup: dict, monkeypatch) -> None:
    def boom(prompt: str) -> str:
        raise gemini_service.AIRateLimitError("busy, try later")

    monkeypatch.setattr(gemini_service, "generate_json", boom)
    monday = setup["monday"]
    res = client.post(
        "/ai/generate-plan",
        json={"start_date": monday.isoformat(), "end_date": monday.isoformat()},
        headers=setup["headers"],
    )
    assert res.status_code == 429
    assert res.json()["detail"] == "busy, try later"


def test_save_replaces_only_pending_ai_tasks(client: TestClient, setup: dict) -> None:
    headers, monday, sid = setup["headers"], setup["monday"], setup["subject"]["id"]
    rng = {"start_date": monday.isoformat(), "end_date": (monday + timedelta(days=2)).isoformat()}

    def save(titles: list[str]) -> dict:
        res = client.post("/ai/save-plan", json={**rng, "days": [{"date": monday.isoformat(), "tasks": [
            {"subject_id": sid, "title": t, "start_time": "15:00", "duration_mins": 20} for t in titles
        ]}]}, headers=headers)
        assert res.status_code == 200, res.text
        return res.json()

    manual = client.post("/tasks", json={
        "subject_id": sid, "title": "Manual", "scheduled_date": monday.isoformat(), "duration_mins": 30,
    }, headers=headers).json()

    first = save(["AI one", "AI two"])
    assert first == {"plan_id": first["plan_id"], "tasks_created": 2, "tasks_replaced": 0}

    tasks = client.get(f"/tasks?date={monday.isoformat()}", headers=headers).json()
    ai_done = next(t for t in tasks if t["title"] == "AI one")
    client.patch(f"/tasks/{ai_done['id']}/status", json={"status": "completed"}, headers=headers)

    second = save(["AI three"])
    assert second["tasks_replaced"] == 1  # only the pending "AI two"
    titles = {t["title"] for t in client.get(f"/tasks?date={monday.isoformat()}", headers=headers).json()}
    assert titles == {"Manual", "AI one", "AI three"}
    assert manual["source"] == "manual"


def test_save_rejects_overbooked_day_and_foreign_subject(client: TestClient, setup: dict) -> None:
    headers, monday, sid = setup["headers"], setup["monday"], setup["subject"]["id"]
    rng = {"start_date": monday.isoformat(), "end_date": monday.isoformat()}
    too_long = {**rng, "days": [{"date": monday.isoformat(), "tasks": [
        {"subject_id": sid, "title": "Long", "start_time": "09:00", "duration_mins": 121},
    ]}]}
    assert client.post("/ai/save-plan", json=too_long, headers=headers).status_code == 422

    other = register(client, "other@gmail.com")
    stolen = {**rng, "days": [{"date": monday.isoformat(), "tasks": [
        {"subject_id": sid, "title": "X", "start_time": "09:00", "duration_mins": 30},
    ]}]}
    assert client.post("/ai/save-plan", json=stolen, headers=other).status_code == 404


def test_not_configured_returns_503(client: TestClient, setup: dict, monkeypatch) -> None:
    from app.core import config

    monkeypatch.setattr(config.get_settings(), "gemini_api_key", "")
    monday = setup["monday"]
    res = client.post(
        "/ai/generate-plan",
        json={"start_date": monday.isoformat(), "end_date": monday.isoformat()},
        headers=setup["headers"],
    )
    assert res.status_code == 503
