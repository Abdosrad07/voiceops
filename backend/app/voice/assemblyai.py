"""Wrapper du Voice Agent AssemblyAI : token temporaire + configuration de session.

Le navigateur se connecte directement au WebSocket AssemblyAI (`voice_agent_ws_url`)
avec le token temporaire obtenu via `GET /api/voice-token`. La clé API permanente ne
quitte jamais le serveur.

La génération de token est protégée par retry à backoff exponentiel et un circuit
breaker (échec rapide si AssemblyAI est down, cooldown avant nouvelle tentative).
"""

import httpx
from pydantic import BaseModel

from app.agents.prompts import SYSTEM_PROMPT
from app.agents.tools import TOOLS
from app.core.config import settings
from app.core.resilience import CircuitBreaker, CircuitOpenError, is_http_retryable, retry
from app.core.security import require_assemblyai_key

DEFAULT_EXPIRES_IN = 300
DEFAULT_MAX_SESSION = 1800

_TOKEN_CIRCUITS: dict[str, CircuitBreaker] = {}


class VoiceTokenResponse(BaseModel):
    token: str
    expires_in_seconds: int
    max_session_duration_seconds: int | None = None


def build_voice_config() -> dict:
    """Configuration de session envoyée côté navigateur (session.update)."""
    return {
        "system_prompt": SYSTEM_PROMPT,
        "greeting": (
            "Bonjour, ici VoiceOps. Je suis votre assistant de diagnostic réseau. "
            "Décrivez-moi le problème rencontré, par exemple : « le PC 204 n'a plus "
            "de réseau »."
        ),
        "input": {"format": {"encoding": "audio/pcm"}},
        "output": {"voice": settings.voice_name, "format": {"encoding": "audio/pcm"}},
        "tools": [{"type": "function", **tool} for tool in TOOLS],
    }


def _circuit_for(url: str) -> CircuitBreaker:
    """Un circuit breaker par base URL (global au processus)."""
    circuit = _TOKEN_CIRCUITS.get(url)
    if circuit is None:
        circuit = CircuitBreaker(
            threshold=settings.circuit_breaker_threshold,
            cooldown_seconds=settings.circuit_breaker_cooldown_seconds,
        )
        _TOKEN_CIRCUITS[url] = circuit
    return circuit


def create_voice_token(
    expires_in_seconds: int = DEFAULT_EXPIRES_IN,
    max_session_duration_seconds: int = DEFAULT_MAX_SESSION,
    base_url: str | None = None,
    api_key: str | None = None,
    client: httpx.Client | None = None,
    timeout: float | None = None,
    max_retries: int | None = None,
    retry_backoff: float | None = None,
    sleep=None,
) -> VoiceTokenResponse:
    """Génère un token temporaire mono-usage auprès d'AssemblyAI (`GET /v1/token`).

    Lève `RuntimeError` si le circuit est ouvert, `RetryExhausted` si tous les
    essais échouent, ou l'exception httpx sous-jacente.
    """
    key = api_key or require_assemblyai_key()
    url = f"{(base_url or settings.assemblyai_base_url).rstrip('/')}/token"
    params = {"expires_in_seconds": expires_in_seconds}
    if max_session_duration_seconds:
        params["max_session_duration_seconds"] = max_session_duration_seconds

    timeout = timeout if timeout is not None else settings.assemblyai_timeout_seconds
    attempts = max_retries if max_retries is not None else settings.assemblyai_max_retries
    backoff = retry_backoff or settings.assemblyai_retry_backoff_seconds

    headers = {"Authorization": f"Bearer {key}"}

    def attempt() -> httpx.Response:
        http = client or httpx.Client(timeout=timeout)
        try:
            response = http.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response
        finally:
            if client is None:
                http.close()

    def guarded() -> VoiceTokenResponse:
        response = retry(
            attempt,
            attempts=attempts,
            base_delay=backoff,
            retryable=is_http_retryable,
            sleep=sleep,
        )
        return VoiceTokenResponse(**response.json())

    circuit = _circuit_for(url)
    try:
        return circuit.call(guarded)
    except CircuitOpenError as exc:
        raise RuntimeError(
            "AssemblyAI est temporairement indisponible (circuit ouvert). Reessayez plus tard."
        ) from exc
