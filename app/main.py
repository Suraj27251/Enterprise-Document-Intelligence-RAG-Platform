"""FastAPI application entrypoint."""

from __future__ import annotations

import logging
import os

import sentry_sdk
from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.endpoints import router
from app.core.config import get_settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

settings = get_settings()
commit_sha = os.getenv("RENDER_GIT_COMMIT", "local")
if settings.sentry_dsn:
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.environment,
        traces_sample_rate=0.2,
    )

app = FastAPI(title=settings.app_name)
logging.getLogger(__name__).info("Application booted with commit=%s", commit_sha)
app.include_router(router, prefix="/api/v1", tags=["document-intelligence"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/")
def root() -> dict[str, str]:
    """Human-friendly root route for hosted environments (Render, etc.)."""

    return {
        "message": "Enterprise Document Intelligence API is running.",
        "docs": "/docs",
        "health": "/health",
        "api_base": "/api/v1",
    }


@app.get("/version")
def version() -> dict[str, str]:
    """Expose deployment/version metadata to verify Render is on latest commit."""

    return {"service": settings.app_name, "commit": commit_sha, "environment": settings.environment}


@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Consistent 404 payload with discoverability links."""

    return JSONResponse(
        status_code=404,
        content={
            "detail": "Not Found",
            "path": str(request.url.path),
            "docs": "/docs",
            "health": "/health",
            "version": "/version",
            "api_base": "/api/v1",
        },
    )
