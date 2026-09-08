"""Wrapper du Voice Agent AssemblyAI : token temporaire + configuration de session.

Le navigateur se connecte directement au WebSocket AssemblyAI (`voice_agent_ws_url`)
avec le token temporaire obtenu via `GET /api/voice-token`. La clé API permanente ne
quitte jamais le serveur.
"""

import httpx
from pydantic import BaseModel

from app.agents.prompts import SYSTEM_PROMPT
from app.agents.tools import TOOLS
from app.core.config import settings
from app.core.security import require_assemblyai_key

DEFAULT_EXPIRES_IN = 300
DEFAULT_MAX_SESSION = 1800


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


def create_voice_token(
    expires_in_seconds: int = DEFAULT_EXPIRES_IN,
    max_session_duration_seconds: int = DEFAULT_MAX_SESSION,
    base_url: str | None = None,
    api_key: str | None = None,
    client: httpx.Client | None = None,
) -> VoiceTokenResponse:
    """Génère un token temporaire mono-usage auprès d'AssemblyAI (`GET /v1/token`)."""
    key = api_key or require_assemblyai_key()
    url = f"{(base_url or settings.assemblyai_base_url).rstrip('/')}/token"
    params = {"expires_in_seconds": expires_in_seconds}
    if max_session_duration_seconds:
        params["max_session_duration_seconds"] = max_session_duration_seconds

    http = client or httpx.Client(timeout=30)
    try:
        response = http.get(
            url,
            headers={"Authorization": f"Bearer {key}"},
            params=params,
        )
        response.raise_for_status()
        return VoiceTokenResponse(**response.json())
    finally:
        if client is None:
            http.close()
