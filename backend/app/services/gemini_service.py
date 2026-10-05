"""Thin wrapper around the Google Gemini SDK. Only called on explicit user action."""

import logging

from google import genai
from google.genai import errors, types

from app.core.config import get_settings

logger = logging.getLogger("studyai.gemini")


class AIError(Exception):
    """Base class for AI failures; `message` is safe to show to users."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class AINotConfiguredError(AIError):
    pass


class AIRateLimitError(AIError):
    pass


class AIUnavailableError(AIError):
    pass


_client: genai.Client | None = None


def _get_client() -> tuple[genai.Client, str]:
    global _client
    settings = get_settings()
    if not settings.gemini_api_key or not settings.gemini_model:
        raise AINotConfiguredError(
            "AI plan generation is not configured. Set GEMINI_API_KEY and GEMINI_MODEL on the server."
        )
    if _client is None:
        _client = genai.Client(api_key=settings.gemini_api_key)
    return _client, settings.gemini_model


def generate_json(prompt: str) -> str:
    """Send `prompt` to Gemini asking for a JSON-only response and return the raw text."""
    client, model = _get_client()
    try:
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.4,
            ),
        )
    except errors.APIError as exc:
        logger.warning("Gemini API error %s: %s", exc.code, exc)
        if exc.code == 429:
            raise AIRateLimitError(
                "The AI service is busy right now (rate limit reached). Please wait a minute and try again."
            ) from exc
        if exc.code in (401, 403):
            raise AINotConfiguredError("The AI service rejected the server's API key.") from exc
        if exc.code == 404:
            raise AINotConfiguredError(f"The configured Gemini model '{model}' was not found.") from exc
        raise AIUnavailableError("The AI service is unavailable right now. Please try again later.") from exc
    except Exception as exc:  # network errors, timeouts
        logger.exception("Gemini request failed")
        raise AIUnavailableError("Could not reach the AI service. Please try again later.") from exc
    return response.text or ""
