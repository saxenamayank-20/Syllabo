"""Outgoing email: Brevo HTTP API, any SMTP server, or the console (local development)."""

import html as html_lib
import logging
import smtplib
import ssl
from email.message import EmailMessage
from typing import Literal

import httpx

from app.core.config import get_settings

logger = logging.getLogger("studyai.email")

BREVO_URL = "https://api.brevo.com/v3/smtp/email"

CodePurpose = Literal["verify", "reset"]

_COPY: dict[CodePurpose, tuple[str, str, str]] = {
    # purpose: (subject suffix, intro line, "ignore" line)
    "verify": (
        "is your StudyAI verification code",
        "Use this code to verify your email address:",
        "If you didn't create a StudyAI account, you can ignore this email.",
    ),
    "reset": (
        "is your StudyAI password reset code",
        "Use this code to reset your password:",
        "If you didn't ask to reset your password, you can ignore this email — your password won't change.",
    ),
}


class EmailSendError(Exception):
    pass


def _send_smtp(to: str, subject: str, text: str, html: str) -> None:
    settings = get_settings()
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = f"{settings.email_from_name} <{settings.sender_address}>"
    msg["To"] = to
    msg.set_content(text)
    msg.add_alternative(html, subtype="html")
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as smtp:
        smtp.starttls(context=ssl.create_default_context())
        smtp.login(settings.smtp_user, settings.smtp_password)
        smtp.send_message(msg)


def _send_brevo(to: str, subject: str, text: str, html: str) -> None:
    settings = get_settings()
    response = httpx.post(
        BREVO_URL,
        headers={"api-key": settings.brevo_api_key, "accept": "application/json"},
        json={
            "sender": {"name": settings.email_from_name, "email": settings.sender_address},
            "to": [{"email": to}],
            "subject": subject,
            "textContent": text,
            "htmlContent": html,
        },
        timeout=15,
    )
    if response.status_code >= 400:
        raise EmailSendError(f"Brevo returned {response.status_code}: {response.text[:300]}")


def send_code(to: str, name: str, code: str, expires_minutes: int, purpose: CodePurpose) -> None:
    """Email a one-time code. Raises EmailSendError if the provider fails."""
    settings = get_settings()
    if settings.email_provider == "console":
        logger.warning("DEV MODE (EMAIL_PROVIDER=console): %s code for %s is %s", purpose, to, code)
        print(f"\n*** DEV MODE: {purpose} code for {to} is {code} ***\n", flush=True)
        return

    subject_suffix, intro, ignore = _COPY[purpose]
    subject = f"{code} {subject_suffix}"
    text = f"Hi {name},\n\n{intro} {code}\n\nIt expires in {expires_minutes} minutes. {ignore}"
    html = f"""\
<div style="font-family:Arial,sans-serif;max-width:480px;margin:auto;color:#1e293b">
  <h2 style="color:#2563eb;margin-bottom:4px">StudyAI</h2>
  <p>Hi {html_lib.escape(name)},</p>
  <p>{intro}</p>
  <p style="font-size:32px;font-weight:bold;letter-spacing:8px;background:#eff6ff;padding:16px;text-align:center;border-radius:12px">{code}</p>
  <p style="color:#64748b;font-size:13px">It expires in {expires_minutes} minutes. {ignore}</p>
</div>"""
    try:
        if settings.email_provider == "brevo":
            _send_brevo(to, subject, text, html)
        else:
            _send_smtp(to, subject, text, html)
    except (smtplib.SMTPException, OSError, httpx.HTTPError, EmailSendError) as exc:
        logger.error("Failed to send %s email to %s via %s: %s", purpose, to, settings.email_provider, exc)
        raise EmailSendError(str(exc)) from exc
