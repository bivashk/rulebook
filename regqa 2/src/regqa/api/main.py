import logging
import time
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import psycopg
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from regqa.config import get_settings
from regqa.db import close_pool, connection
from regqa.logging import configure_logging

log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging(settings.log_level)
    log.info("startup", extra={"env": settings.app_env})
    yield
    close_pool()
    log.info("shutdown")


app = FastAPI(title="regqa", lifespan=lifespan)


@app.middleware("http")
async def access_log(request: Request, call_next):
    request_id = str(uuid.uuid4())
    started = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
    log.info(
        "http_request",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "duration_ms": elapsed_ms,
        },
    )
    response.headers["x-request-id"] = request_id
    return response


@app.get("/healthz")
def healthz() -> dict[str, str]:
    """Liveness. Answers only "is this process running", with no dependencies.

    Checking the database here would make a brief database blip restart the api,
    which does not fix the database and adds a cold start to the outage.
    """
    return {"status": "ok"}


@app.get("/readyz")
def readyz() -> JSONResponse:
    """Readiness. Answers "can this process do useful work right now"."""
    timeout = get_settings().readiness_timeout_s
    try:
        with connection(timeout=timeout) as conn, conn.cursor() as cur:
            cur.execute("SELECT 1")
            cur.fetchone()
    except psycopg.Error as exc:
        # Reported, not swallowed: the caller gets 503 and the reason is logged.
        log.warning("readiness_failed", extra={"reason": exc.__class__.__name__}, exc_info=exc)
        return JSONResponse({"status": "unready", "database": "unreachable"}, status_code=503)
    return JSONResponse({"status": "ready", "database": "ok"})
