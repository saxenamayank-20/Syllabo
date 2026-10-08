"""small wrapper around the gemini sdk. only runs when the user clicks generate"""

import logging

from google import genai
from google.genai import errors, types

from app.core.config import get_settings

logger = logging.getLogger("studyai.gemini")


class AIError(Exception):
    """ai errors, message is ok to show the user"""

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

BUSY_CODES = (429, 503)  # rate limited or google's model is overloaded


def _get_client() -> tuple[genai.Client, list[str]]:
    """client + models to try (main, then fallback)"""
    global _client
    settings = get_settings()
    if not settings.gemini_api_key or not settings.gemini_model:
        raise AINotConfiguredError(
            "AI plan generation is not configured. Set GEMINI_API_KEY and GEMINI_MODEL on the server."
        )
    if _client is None:
        _client = genai.Client(api_key=settings.gemini_api_key)
    models = [settings.gemini_model]
    if settings.gemini_fallback_model and settings.gemini_fallback_model != settings.gemini_model:
        models.append(settings.gemini_fallback_model)
    return _client, models


def _generate(client: genai.Client, model: str, prompt: str) -> str:
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.4,
            # no tools, so turn this off (stops a log warning)
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        ),
    )
    return response.text or ""


def generate_json(prompt: str) -> str:
    """ask gemini for json and return the raw text. tries the fallback model once if busy"""
    client, models = _get_client()
    for i, model in enumerate(models):
        try:
            return _generate(client, model, prompt)
        except errors.APIError as exc:
            logger.warning("Gemini API error %s from %s: %s", exc.code, model, exc)
            if exc.code in BUSY_CODES:
                if i + 1 < len(models):
                    continue  # try the fallback model
                raise AIRateLimitError(
                    "The AI service is busy right now. Please wait a minute and try again."
                ) from exc
            if exc.code in (401, 403):
                raise AINotConfiguredError("The AI service rejected the server's API key.") from exc
            if exc.code == 404:
                raise AINotConfiguredError(f"The configured Gemini model '{model}' was not found.") from exc
            raise AIUnavailableError("The AI service is unavailable right now. Please try again later.") from exc
        except Exception as exc:  # network errors, timeouts
            logger.exception("Gemini request failed")
            raise AIUnavailableError("Could not reach the AI service. Please try again later.") from exc
    raise AssertionError("unreachable")  # the loop always returns or raises
