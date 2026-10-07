import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.routers import ai, auth, dashboard, exams, marks, preferences, subjects, tasks, topics

logger = logging.getLogger("studyai")



@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    if settings.environment == "production" and (problems := settings.production_problems()):
        raise RuntimeError("Refusing to start in production:\n- " + "\n- ".join(problems))
    if settings.email_provider == "console":
        logger.warning("EMAIL_PROVIDER=console: verification/reset codes are printed here, not emailed.")
    yield


app = FastAPI(title="Syllabo API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )


for router in (auth, subjects, topics, exams, preferences, tasks, marks, dashboard, ai):
    app.include_router(router.router)


@app.get("/health", tags=["meta"])
def health() -> dict[str, str]:
    return {"status": "ok"}
