from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from app.api.routes import diagnostics, health, incidents, networks, reports, voice
from app.core import logging as core_logging
from app.core.config import settings
from app.core.middleware import (
    RateLimitMiddleware,
    RateLimitStore,
    RequestLogMiddleware,
    SecurityHeadersMiddleware,
)
from app.database import engine, init_db

core_logging.setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield
    engine.dispose()


app = FastAPI(title=settings.app_name, version=settings.version, lifespan=lifespan)

_gzip_min_size = 1024
app.add_middleware(GZipMiddleware, minimum_size=_gzip_min_size)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Request-ID"],
)

_rate_store = RateLimitStore(
    default_rpm=settings.rate_limit_rpm,
    voice_rpm=settings.rate_limit_voice_rpm,
    window_seconds=settings.rate_limit_window_seconds,
)
_rate_store.enabled = settings.rate_limit_enabled

_request_logger = core_logging.get_logger("http")
app.add_middleware(RequestLogMiddleware, logger=_request_logger)
app.add_middleware(RateLimitMiddleware, store=_rate_store)
app.add_middleware(SecurityHeadersMiddleware)

app.include_router(health.router)
app.include_router(diagnostics.router)
app.include_router(networks.router)
app.include_router(incidents.router)
app.include_router(reports.router)
app.include_router(voice.router)


@app.get("/")
def root() -> dict:
    return {
        "app": settings.app_name,
        "docs": "/docs",
        "health": "/health",
        "deep_health": "/health/deep",
    }
