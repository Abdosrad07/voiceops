"""Middleware FastAPI : sécurité des headers, CORS, rate limiting par IP,
logging des requêtes avec request-id et compression gzip.

- Gzip : activé via `GZipMiddleware` (réponses > 1 Ko).
- Rate limiting : en mémoire (token bucket par IP), sans dépendance Redis.
"""

import threading
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core import logging as core_logging
from app.core.config import settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Positionne les en-têtes de sécurité sur chaque réponse."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Permissions-Policy"] = "camera=(), geolocation=(), autoplay=()"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; object-src 'none'; base-uri 'self'; "
            "frame-ancestors 'none'; img-src 'self' data:; "
            f"connect-src 'self' {settings.voice_agent_ws_url} https:; "
            "script-src 'self'; style-src 'self' 'unsafe-inline'"
        )
        if settings.environment == "production":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )
        return response


class RequestLogMiddleware(BaseHTTPMiddleware):
    """Attribue un request-id et journalise méthode / chemin / statut / durée."""

    def __init__(self, app, logger):
        super().__init__(app)
        self.logger = logger

    async def dispatch(self, request: Request, call_next):
        request_id = uuid.uuid4().hex[:12]
        core_logging.set_request_id(request_id)
        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception as exc:
            self.logger.warning(
                "request.error",
                extra={
                    "extra": {
                        "method": request.method,
                        "path": request.url.path,
                        "error": str(exc),
                    }
                },
            )
            raise
        duration_ms = (time.perf_counter() - start) * 1000
        response.headers["X-Request-ID"] = request_id
        self.logger.info(
            "request",
            extra={
                "extra": {
                    "method": request.method,
                    "path": request.url.path,
                    "status": response.status_code,
                    "duration_ms": round(duration_ms, 1),
                }
            },
        )
        return response


class RateLimitStore:
    """Compteurs token bucket par IP et par route (mémoire, thread-safe).

    `default_rpm` s'applique à l'API ; `voice_rpm`, plus strict, aux endpoints
    vocaux (/api/voice-token et /api/tools/execute).
    """

    def __init__(
        self,
        default_rpm: int = 100,
        voice_rpm: int = 30,
        window_seconds: int = 60,
        now: float | None = None,
    ) -> None:
        self.default_rpm = default_rpm
        self.voice_rpm = voice_rpm
        self.window_seconds = window_seconds
        self.enabled = True
        self._buckets: dict[tuple[str, bool], dict] = {}
        self._lock = threading.RLock()
        self._now = now or time.monotonic

    def _rate_for_path(self, path: str) -> int:
        if path.startswith("/api/voice-token") or path.startswith("/api/tools"):
            return self.voice_rpm
        return self.default_rpm

    def reset(self) -> None:
        with self._lock:
            self._buckets.clear()

    def allow(self, client_host: str, path: str) -> tuple[bool, float]:
        """Retourne (autorisé?, retry_after_seconds)."""
        if not self.enabled:
            return True, 0.0
        rate = self._rate_for_path(path)
        key = (client_host, rate)
        now = self._now()
        with self._lock:
            bucket = self._buckets.get(key)
            if bucket is None:
                self._buckets[key] = {"tokens": float(rate), "updated": now}
                bucket = self._buckets[key]
            elapsed = now - bucket["updated"]
            bucket["tokens"] = min(
                float(rate), bucket["tokens"] + elapsed * (rate / self.window_seconds)
            )
            bucket["updated"] = now
            if bucket["tokens"] < 1.0:
                retry_after = (1.0 - bucket["tokens"]) * self.window_seconds / rate
                return False, max(1.0, round(retry_after))
            bucket["tokens"] -= 1.0
            if len(self._buckets) > 10_000:
                self._prune(now)
            return True, 0.0

    def _prune(self, now: float) -> None:
        stale = [
            key
            for key, bucket in self._buckets.items()
            if now - bucket["updated"] > self.window_seconds * 2
        ]
        for key in stale:
            self._buckets.pop(key, None)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting par IP sur les routes /api/* (désactivable pour les tests)."""

    def __init__(self, app, store: RateLimitStore):
        super().__init__(app)
        self.store = store

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if not path.startswith("/api/"):
            return await call_next(request)
        if not settings.rate_limit_enabled or not self.store.enabled:
            return await call_next(request)
        client_host = request.client.host if request.client else "unknown"
        allowed, retry_after = self.store.allow(client_host, path)
        if not allowed:
            return Response(
                status_code=429,
                headers={"Retry-After": str(int(retry_after))},
                content="Too many requests",
            )
        return await call_next(request)
