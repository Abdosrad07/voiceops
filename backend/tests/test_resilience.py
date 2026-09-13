"""Tests résilience : retry à backoff exponentiel et circuit breaker."""

import httpx
import pytest

from app.core.resilience import (
    CircuitBreaker,
    CircuitOpenError,
    RetryExhausted,
    is_http_retryable,
    retry,
)
from app.voice import assemblyai


def _http_error(status: int) -> httpx.HTTPStatusError:
    request = httpx.Request("GET", "https://api.assemblyai.com/v1/token")
    response = httpx.Response(status, request=request)
    return httpx.HTTPStatusError("boom", request=request, response=response)


def test_retry_with_exponential_backoff_and_success() -> None:
    sleeps: list[float] = []
    attempts = {"count": 0}

    def fn():
        attempts["count"] += 1
        if attempts["count"] <= 2:
            raise _http_error(500)
        return "ok"

    result = retry(
        fn,
        attempts=3,
        base_delay=1.0,
        retryable=is_http_retryable,
        sleep=sleeps.append,
    )
    assert result == "ok"
    assert attempts["count"] == 3
    assert sleeps == [1.0, 2.0]


def test_retry_max_delay_capped() -> None:
    sleeps: list[float] = []
    attempts = {"count": 0}

    def fn():
        attempts["count"] += 1
        raise _http_error(503)

    with pytest.raises(RetryExhausted):
        retry(fn, attempts=5, base_delay=3.0, max_delay=8.0, sleep=sleeps.append)
    assert sleeps == [3.0, 6.0, 8.0, 8.0]


def test_retry_does_not_retry_non_retryable() -> None:
    sleeps: list[float] = []
    with pytest.raises(httpx.HTTPStatusError):
        retry(
            lambda: (_ for _ in ()).throw(_http_error(400)),
            attempts=3,
            sleep=sleeps.append,
        )
    assert sleeps == []


def test_circuit_breaker_transitions() -> None:
    clock = [0.0]
    breaker = CircuitBreaker(threshold=2, cooldown_seconds=30.0, now=lambda: clock[0])
    assert breaker.state == "closed"

    with pytest.raises(ValueError):
        breaker.call(lambda: (_ for _ in ()).throw(ValueError("x")))
    assert breaker.state == "closed"
    with pytest.raises(ValueError):
        breaker.call(lambda: (_ for _ in ()).throw(ValueError("x")))
    assert breaker.state == "open"

    # Échec rapide tant que le cooldown n'est pas écoulé.
    with pytest.raises(CircuitOpenError):
        breaker.call(lambda: "ok")

    # Après cooldown : demi-ouvert, un succès referme.
    clock[0] += 31.0
    assert breaker.call(lambda: "ok") == "ok"
    assert breaker.state == "closed"


def test_voice_token_retries_then_succeeds() -> None:
    attempts = {"count": 0}
    called_urls = []

    def handler(request: httpx.Request) -> httpx.Response:
        attempts["count"] += 1
        called_urls.append(str(request.url))
        if attempts["count"] < 3:
            return httpx.Response(502, request=request)
        return httpx.Response(200, json={"token": "tok_r", "expires_in_seconds": 300})

    with httpx.Client(transport=httpx.MockTransport(handler)) as transport:
        token = assemblyai.create_voice_token(
            api_key="sk_test_1",
            base_url="https://api.assemblyai.com/v1",
            client=transport,
            max_retries=3,
            retry_backoff=0.01,
            sleep=lambda _: None,
        )
    assert token.token == "tok_r"
    assert attempts["count"] == 3


def test_voice_token_circuit_breaker_opens(monkeypatch) -> None:
    monkeypatch.setattr(assemblyai.settings, "circuit_breaker_threshold", 2)
    monkeypatch.setattr(assemblyai.settings, "circuit_breaker_cooldown_seconds", 60.0)
    assemblyai._TOKEN_CIRCUITS.clear()

    failures = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        failures["count"] += 1
        return httpx.Response(503, request=request)

    with httpx.Client(transport=httpx.MockTransport(handler)) as transport:
        for _ in range(4):
            with pytest.raises((RetryExhausted, RuntimeError)):
                assemblyai.create_voice_token(
                    api_key="sk_test_2",
                    client=transport,
                    max_retries=1,
                    retry_backoff=0.0,
                    sleep=lambda _: None,
                )
    # Ouvrir le circuit puis vérifier l'échec rapide.
    with pytest.raises(RuntimeError) as excinfo:
        assemblyai.create_voice_token(
            api_key="sk_test_2",
            client=transport,
            max_retries=1,
            sleep=lambda _: None,
        )
    assert "circuit" in str(excinfo.value).lower()
    assert failures["count"] == 2  # plus de tentative HTTP une fois le circuit ouvert
    assemblyai._TOKEN_CIRCUITS.clear()  # ne pas polluer les autres tests
