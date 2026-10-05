from fastapi.testclient import TestClient

from tests.conftest import register


def test_register_login_and_me(client: TestClient) -> None:
    headers = register(client)

    me = client.get("/auth/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["email"] == "student@gmail.com"

    login = client.post(
        "/auth/login", json={"email": "Student@Gmail.com", "password": "secret123"}
    )
    assert login.status_code == 200
    assert login.json()["access_token"]


def test_duplicate_email_rejected(client: TestClient) -> None:
    register(client)
    res = client.post(
        "/auth/register",
        json={"name": "Other", "email": "student@gmail.com", "password": "secret123"},
    )
    assert res.status_code == 409


def test_wrong_password(client: TestClient) -> None:
    register(client)
    res = client.post("/auth/login", json={"email": "student@gmail.com", "password": "nope00"})
    assert res.status_code == 401


def test_protected_routes_require_token(client: TestClient) -> None:
    assert client.get("/auth/me").status_code == 401
    assert client.get("/subjects").status_code == 401
    bad = {"Authorization": "Bearer not-a-real-token"}
    assert client.get("/dashboard/summary", headers=bad).status_code == 401


def test_validation_error(client: TestClient) -> None:
    res = client.post("/auth/register", json={"name": "", "email": "bad", "password": "1"})
    assert res.status_code == 422
