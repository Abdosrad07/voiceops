"""Résilience : retry à backoff exponentiel et circuit breaker.

Fonctions volontairement synchrones (adaptées au client HTTP et aux appels
d'outils) et injectables en horloge/sommeil pour des tests déterministes.
"""

import threading
import time
from collections.abc import Callable
from typing import Any

import httpx

SLEEP: Callable[[float], None] = time.sleep


class CircuitOpenError(RuntimeError):
    """Le circuit est ouvert : appel en échec rapide, cooldown en cours."""


class RetryExhausted(RuntimeError):
    """Tous les essais de retry ont échoué."""


class CircuitBreaker:
    """Circuit breaker fermé → ouvert → demi-ouvert, thread-safe.

    - `closed` : appels autorisés, `threshold` échecs consécutifs → `open`.
    - `open` : échec rapide (`CircuitOpenError`) pendant `cooldown`.
    - `half_open` : une sonde autorisée ; succès → `closed`, échec → `open`.
    """

    def __init__(
        self,
        threshold: int = 5,
        cooldown_seconds: float = 30.0,
        now: Callable[[], float] | None = None,
    ) -> None:
        self.threshold = max(1, threshold)
        self.cooldown = cooldown_seconds
        self._now = now or time.monotonic
        self._state = "closed"
        self._failures = 0
        self._opened_at: float | None = None
        self._lock = threading.RLock()

    @property
    def state(self) -> str:
        return self._state

    def reset(self) -> None:
        with self._lock:
            self._state = "closed"
            self._failures = 0
            self._opened_at = None

    def _transition(self, state: str) -> None:
        self._state = state
        if state == "open":
            self._opened_at = self._now()
            self._failures = 0

    def call(self, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """Exécute `fn` en respectant l'état du circuit."""
        with self._lock:
            now = self._now()
            if self._state == "open":
                if self._opened_at is not None and now - self._opened_at >= self.cooldown:
                    self._state = "half_open"
                else:
                    raise CircuitOpenError()
        try:
            result = fn(*args, **kwargs)
        except Exception:
            with self._lock:
                self._failures += 1
                if self._state == "half_open" or self._failures >= self.threshold:
                    self._transition("open")
            raise
        with self._lock:
            if self._state == "half_open":
                self._state = "closed"
            self._failures = 0
        return result


def is_http_retryable(exc: BaseException) -> bool:
    """Timeouts, erreurs de connexion et réponses 5xx/429 sont retrayés."""
    if isinstance(exc, (httpx.TimeoutException, httpx.ConnectError, httpx.ConnectTimeout)):
        return True
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code in {429, 500, 502, 503, 504}
    return False


def retry(
    fn: Callable[[], Any],
    *,
    attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 8.0,
    retryable: Callable[[BaseException], bool] = is_http_retryable,
    sleep: Callable[[float], None] = SLEEP,
) -> Any:
    """Réessaie `fn` avec backoff exponentiel (1s, 2s, 4s, max 8s)."""
    last_exc: BaseException | None = None
    delay = base_delay
    for attempt in range(1, attempts + 1):
        try:
            return fn()
        except CircuitOpenError:
            raise
        except Exception as exc:
            last_exc = exc
            if not retryable(exc):
                raise
            if attempt < attempts:
                sleep(delay)
                delay = min(delay * 2, max_delay)
    raise RetryExhausted(
        f"Échec après {attempts} tentatives"
    ) from last_exc
