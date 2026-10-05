from datetime import date, timedelta

from fastapi.testclient import TestClient

from tests.conftest import register


def test_subject_topic_crud_and_dashboard(client: TestClient) -> None:
    headers = register(client)

    res = client.post(
        "/subjects", json={"name": "Physics", "color": "#ef4444", "target_score": 80},
        headers=headers,
    )
    assert res.status_code == 201
    subject_id = res.json()["id"]

    for name in ("Kinematics", "Optics"):
        r = client.post(f"/subjects/{subject_id}/topics", json={"name": name}, headers=headers)
        assert r.status_code == 201
    topic_id = r.json()["id"]

    # Empty PATCH toggles status
    toggled = client.patch(f"/topics/{topic_id}", headers=headers)
    assert toggled.json()["status"] == "completed"
    assert toggled.json()["completed_at"] is not None

    subjects = client.get("/subjects", headers=headers).json()
    assert len(subjects) == 1 and len(subjects[0]["topics"]) == 2

    updated = client.patch(f"/subjects/{subject_id}", json={"name": "Physics II"}, headers=headers)
    assert updated.json()["name"] == "Physics II"

    today = date.today()
    client.post(
        "/exams",
        json={"title": "Mid term", "subject_id": subject_id,
              "exam_date": (today + timedelta(days=10)).isoformat()},
        headers=headers,
    )
    client.post(
        "/tasks",
        json={"subject_id": subject_id, "title": "Read notes",
              "scheduled_date": today.isoformat(), "start_time": "09:00"},
        headers=headers,
    )
    client.post(
        "/marks",
        json={"subject_id": subject_id, "assessment_name": "Quiz 1", "score": 14,
              "max_score": 20, "assessment_date": today.isoformat()},
        headers=headers,
    )

    summary = client.get("/dashboard/summary", headers=headers).json()
    assert summary["today_tasks_total"] == 1
    assert summary["today_tasks_completed"] == 0
    assert summary["days_to_next_exam"] == 10
    assert summary["overall_progress"] == 50.0
    assert summary["progress_change_this_week"] == 50.0
    assert summary["current_grade"] == "B"  # 70%
    assert summary["weak_subjects"][0]["subject"] == "Physics II"

    tasks = client.get(f"/tasks?date={today.isoformat()}", headers=headers).json()
    done = client.patch(f"/tasks/{tasks[0]['id']}/status", json={"status": "completed"},
                        headers=headers)
    assert done.json()["status"] == "completed"
    assert client.get("/dashboard/summary", headers=headers).json()["today_tasks_completed"] == 1

    assert client.delete(f"/subjects/{subject_id}", headers=headers).status_code == 204
    assert client.get(f"/subjects/{subject_id}", headers=headers).status_code == 404
    assert client.get("/tasks", headers=headers).json() == []
    assert client.get("/marks", headers=headers).json() == []


def test_users_cannot_see_each_others_data(client: TestClient) -> None:
    alice = register(client, "alice@gmail.com")
    bob = register(client, "bob@gmail.com")

    subject_id = client.post("/subjects", json={"name": "Math"}, headers=alice).json()["id"]
    topic_id = client.post(
        f"/subjects/{subject_id}/topics", json={"name": "Algebra"}, headers=alice
    ).json()["id"]

    assert client.get("/subjects", headers=bob).json() == []
    assert client.get(f"/subjects/{subject_id}", headers=bob).status_code == 404
    assert client.patch(f"/topics/{topic_id}", headers=bob).status_code == 404
    assert client.delete(f"/subjects/{subject_id}", headers=bob).status_code == 404
    res = client.post(
        "/marks",
        json={"subject_id": subject_id, "assessment_name": "X", "score": 1, "max_score": 2,
              "assessment_date": date.today().isoformat()},
        headers=bob,
    )
    assert res.status_code == 404
