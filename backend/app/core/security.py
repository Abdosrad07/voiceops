"""Helpers de sécurité : clé AssemblyAI et assainissement des entrées."""

from app.core.config import settings


class MissingApiKeyError(RuntimeError):
    """Clé AssemblyAI absente ou vide."""


def require_assemblyai_key() -> str:
    """Retourne la clé AssemblyAI ou lève si elle n'est pas configurée."""
    key = settings.assemblyai_api_key.strip()
    if not key:
        raise MissingApiKeyError(
            "ASSEMBLYAI_API_KEY n'est pas configurée (cf. backend/.env)."
        )
    return key


def clean_text(text: str, max_len: int = 4000) -> str:
    """Nettoie et borne un texte libre provenant d'une entrée utilisateur."""
    cleaned = " ".join(str(text).split())
    return cleaned[:max_len]


def safe_incident_fields(payload: dict, max_len: int = 2000) -> dict:
    """Assainit les champs texte d'un futur incident (anti-crash / bruit)."""
    return {k: clean_text(v, max_len) if isinstance(v, str) else v for k, v in payload.items()}
