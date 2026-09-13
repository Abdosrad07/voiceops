"""Tests middleware : headers de sécurité, CORS, gzip, request-id, rate limiting."""

from app.core.middleware import RateLimitStore


def test_security_headers_present(db_client) -> None:
    response = db_client.get("/api/incidents")
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["X-XSS-Protection"] == "1; mode=block"
    assert response.headers["Referrer-Policy"] == "no-referrer"
    assert "frame-ancestors 'none'" in response.headers["Content-Security-Policy"]


def test_request_id_header_and_root(db_client) -> None:
    response = db_client.get("/")
    assert response.status_code == 200
    assert response.headers.get("X-Request-ID")
    assert response.json()["deep_health"] == "/health/deep"


def test_cors_allows_configured_origin_but_not_unknown(db_client) -> None:
    allowed = db_client.options(
        "/api/incidents",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Content-Type",
        },
    )
    assert allowed.status_code == 200
    assert allowed.headers.get("access-control-allow-origin") == "http://localhost:5173"

    denied = db_client.options(
        "/api/incidents",
        headers={
            "Origin": "https://evil.example",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert not denied.headers.get("access-control-allow-origin")


def test_gzip_compression_on_large_response(db_client) -> None:
    db_client.post(
        "/api/incidents",
        json={"title": "Gros incident", "description": "x" * 2000},
    )
    response = db_client.get("/api/incidents")
    assert response.status_code == 200
    assert response.headers.get("content-encoding") == "gzip"


def test_rate_limit_store_window_and_reset() -> None:
    clock = [0.0]
    store = RateLimitStore(default_rpm=2, voice_rpm=1, window_seconds=60, now=lambda: clock[0])

    ok, _ = store.allow("1.2.3.4", "/api/incidents")
    assert ok
    ok, _ = store.allow("1.2.3.4", "/api/incidents")
    assert ok
    denied, retry_after = store.allow("1.2.3.4", "/api/incidents")
    assert not denied
    assert retry_after > 0

    clock[0] += 60
    ok, _ = store.allow("1.2.3.4", "/api/incidents")
    assert ok

    store.reset()
    ok, _ = store.allow("1.2.3.4", "/api/incidents")
    assert ok


def test_rate_limit_store_stricter_on_voice_routes() -> None:
    clock = [0.0]
    store = RateLimitStore(default_rpm=100, voice_rpm=1, window_seconds=60, now=lambda: clock[0])

    ok, _ = store.allow("9.9.9.9", "/api/voice-token")
    assert ok
    denied, _ = store.allow("9.9.9.9", "/api/voice-token")
    assert not denied
    # La route générique reste ouverte pour la même IP.
    ok, _ = store.allow("9.9.9.9", "/api/incidents")
    assert ok


def test_rate_limit_store_disabled() -> None:
    store = RateLimitStore(default_rpm=1, voice_rpm=1, window_seconds=60)
    store.enabled = False
    ok, _ = store.allow("1.1.1.1", "/api/incidents")
    assert ok
    ok, _ = store.allow("1.1.1.1", "/api/incidents")
    assert ok
