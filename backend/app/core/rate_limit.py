"""Simple in-memory sliding-window rate limiting for auth endpoints.

Limits are per server process. That's enough for a single Render instance; a multi-instance
deployment would need a shared store such as Redis.
"""

import time
from collections import defaultdict, deque
from collections.abc import Callable
from threading import Lock

from fastapi import HTTPException, Request, status

from app.core.config import get_settings

_hits: dict[tuple[str, str], deque[float]] = defaultdict(deque)
_lock = Lock()


def reset() -> None:
    with _lock:
        _hits.clear()


def rate_limit(bucket: str) -> Callable[[Request], None]:
    """FastAPI dependency: at most AUTH_RATE_LIMIT calls per client IP per window, per bucket."""

    def dependency(request: Request) -> None:
        settings = get_settings()
        client = request.client.host if request.client else "unknown"
        now = time.monotonic()
        window = settings.auth_rate_window_seconds
        with _lock:
            hits = _hits[(bucket, client)]
            while hits and now - hits[0] > window:
                hits.popleft()
            if len(hits) >= settings.auth_rate_limit:
                retry = int(window - (now - hits[0])) + 1
                raise HTTPException(
                    status.HTTP_429_TOO_MANY_REQUESTS,
                    f"Too many attempts. Please wait {retry // 60 + 1} minute(s) and try again.",
                    headers={"Retry-After": str(retry)},
                )
            hits.append(now)

    return dependency
