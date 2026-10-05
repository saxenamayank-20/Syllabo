"""Outgoing email over SMTP (Gmail by default). Without SMTP credentials, messages are logged instead."""

import html as html_lib
import logging
import smtplib
import ssl
from email.message import EmailMessage

from app.core.config import get_settings

logger = logging.getLogger("studyai.email")


class EmailSendError(Exception):
    pass


def _send(to: str, subject: str, text: str, html: str) -> None:
    settings = get_settings()
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = f"{settings.smtp_from_name} <{settings.smtp_user}>"
    msg["To"] = to
    msg.set_content(text)
    msg.add_alternative(html, subtype="html")
    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as smtp:
            smtp.starttls(context=ssl.create_default_context())
            smtp.login(settings.smtp_user, settings.smtp_password)
            smtp.send_message(msg)
    except (smtplib.SMTPException, OSError) as exc:
        logger.error("Failed to send email to %s: %s", to, exc)
        raise EmailSendError(str(exc)) from exc


def send_verification_code(to: str, name: str, code: str, expires_minutes: int) -> None:
    if not get_settings().smtp_user:
        # Dev mode: no SMTP configured, so show the code in the server terminal.
        logger.warning("DEV MODE (no SMTP_USER set): verification code for %s is %s", to, code)
        print(f"\n*** DEV MODE: verification code for {to} is {code} ***\n", flush=True)
        return
    text = (
        f"Hi {name},\n\nYour StudyAI verification code is: {code}\n\n"
        f"It expires in {expires_minutes} minutes. If you didn't create a StudyAI account, ignore this email."
    )
    html = f"""\
<div style="font-family:Arial,sans-serif;max-width:480px;margin:auto;color:#1e293b">
  <h2 style="color:#2563eb;margin-bottom:4px">StudyAI</h2>
  <p>Hi {html_lib.escape(name)},</p>
  <p>Use this code to verify your email address:</p>
  <p style="font-size:32px;font-weight:bold;letter-spacing:8px;background:#eff6ff;padding:16px;text-align:center;border-radius:12px">{code}</p>
  <p style="color:#64748b;font-size:13px">It expires in {expires_minutes} minutes.
  If you didn't create a StudyAI account, you can ignore this email.</p>
</div>"""
    _send(to, f"{code} is your StudyAI verification code", text, html)
