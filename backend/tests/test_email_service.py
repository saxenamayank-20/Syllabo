import httpx
import pytest

from app.core.config import get_settings
from app.services import email_service

# conftest replaces send_code for API tests; grab the real one for these unit tests.
REAL_SEND = email_service.__dict__["send_code"]


@pytest.fixture()
def brevo(monkeypatch: pytest.MonkeyPatch) -> list[dict]:
    settings = get_settings()
    monkeypatch.setattr(settings, "email_provider", "brevo")
    monkeypatch.setattr(settings, "brevo_api_key", "test-key")
    monkeypatch.setattr(settings, "email_from", "team@client.com")
    calls: list[dict] = []

    def fake_post(url: str, **kwargs) -> httpx.Response:
        calls.append({"url": url, **kwargs})
        return httpx.Response(201, json={"messageId": "x"})

    monkeypatch.setattr(email_service.httpx, "post", fake_post)
    return calls


def test_brevo_request_shape(brevo: list[dict]) -> None:
    REAL_SEND("riya@gmail.com", "Riya <b>", "123456", 10, "reset")
    call = brevo[0]
    assert call["url"] == email_service.BREVO_URL
    assert call["headers"]["api-key"] == "test-key"
    body = call["json"]
    assert body["sender"]["email"] == "team@client.com"
    assert body["to"] == [{"email": "riya@gmail.com"}]
    assert body["subject"].startswith("123456") and "reset" in body["subject"]
    assert "Riya &lt;b&gt;" in body["htmlContent"]  # user input is escaped


def test_brevo_error_raises(brevo: list[dict], monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(email_service.httpx, "post", lambda url, **kw: httpx.Response(401, text="bad key"))
    with pytest.raises(email_service.EmailSendError):
        REAL_SEND("riya@gmail.com", "Riya", "123456", 10, "verify")


def test_console_mode_prints_code(capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(get_settings(), "email_provider", "console")
    REAL_SEND("riya@gmail.com", "Riya", "654321", 10, "verify")
    assert "654321" in capsys.readouterr().out
