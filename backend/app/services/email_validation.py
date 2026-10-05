"""Reject email addresses that can't belong to a real, reachable inbox."""

import email_validator
from fastapi import HTTPException, status

from app.core.config import get_settings

# Common throwaway-inbox providers. Not exhaustive, but it covers the usual suspects.
DISPOSABLE_DOMAINS = frozenset({
    "10minutemail.com", "10minutemail.net", "20minutemail.com", "33mail.com", "anonaddy.me",
    "burnermail.io", "discard.email", "dispostable.com", "emailondeck.com", "fakeinbox.com",
    "fakemail.net", "getairmail.com", "getnada.com", "guerrillamail.biz", "guerrillamail.com",
    "guerrillamail.de", "guerrillamail.info", "guerrillamail.net", "guerrillamail.org",
    "guerrillamailblock.com", "harakirimail.com", "inboxkitten.com", "mail.tm", "mailcatch.com",
    "maildrop.cc", "mailinator.com", "mailinator.net", "mailnesia.com", "mailpoof.com",
    "mintemail.com", "moakt.com", "mohmal.com", "mytemp.email", "nada.email", "sharklasers.com",
    "spam4.me", "spamgourmet.com", "temp-mail.io", "temp-mail.org", "tempail.com", "tempmail.com",
    "tempmail.dev", "tempmail.net", "tempmailo.com", "tempr.email", "throwawaymail.com",
    "trashmail.com", "trashmail.de", "trashmail.net", "yopmail.com", "yopmail.fr", "yopmail.net",
})


def _bad_email(message: str) -> HTTPException:
    return HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, message)


def validate_real_email(email: str) -> str:
    """Return the normalised address, or raise 422 if it's disposable or its domain can't receive mail."""
    try:
        result = email_validator.validate_email(
            email, check_deliverability=get_settings().email_check_deliverability, timeout=8
        )
    except email_validator.EmailUndeliverableError:
        raise _bad_email("This email domain can't receive mail. Please use your real email address.")
    except email_validator.EmailNotValidError as exc:
        raise _bad_email(str(exc))
    domain = result.domain.lower()
    if domain in DISPOSABLE_DOMAINS or any(domain.endswith("." + d) for d in DISPOSABLE_DOMAINS):
        raise _bad_email("Temporary/disposable email addresses aren't allowed. Please use your real email.")
    return result.normalized.lower()
