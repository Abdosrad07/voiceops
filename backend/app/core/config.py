import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")


def env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def env_float(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default


def env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def env_list(name: str, default: list[str] | None = None) -> list[str]:
    value = os.getenv(name)
    if value is None:
        return list(default or [])
    return [part.strip() for part in value.split(",") if part.strip()]


class Settings:
    app_name: str = os.getenv("APP_NAME", "voiceops")
    version: str = os.getenv("APP_VERSION", "0.1.0")
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))
    log_level: str = os.getenv("LOG_LEVEL", "info")
    debug: bool = env_bool("DEBUG", False)
    environment: str = os.getenv("ENVIRONMENT", "development")
    assemblyai_api_key: str = os.getenv("ASSEMBLYAI_API_KEY", "")
    assemblyai_base_url: str = os.getenv(
        "ASSEMBLYAI_BASE_URL", "https://api.assemblyai.com/v1"
    )
    voice_agent_ws_url: str = os.getenv(
        "VOICE_AGENT_WS_URL", "wss://agents.assemblyai.com/v1/ws"
    )
    voice_name: str = os.getenv("VOICE_NAME", "ivy")
    rag_index_path: str = os.getenv("RAG_INDEX_PATH", str(BASE_DIR / "rag_index.json"))
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./voiceops.db")

    # --- Optimisation SQLite / pooling ---
    database_pool_size: int = env_int("DATABASE_POOL_SIZE", 5)
    database_max_overflow: int = env_int("DATABASE_MAX_OVERFLOW", 10)
    database_busy_timeout_ms: int = env_int("DATABASE_BUSY_TIMEOUT_MS", 5000)

    # --- CORS ---
    cors_origins: list[str] = env_list(
        "CORS_ORIGINS", ["http://localhost:5173", "http://127.0.0.1:5173"]
    )
    cors_allow_credentials: bool = env_bool("CORS_ALLOW_CREDENTIALS", False)

    # --- Rate limiting (par IP, en mémoire) ---
    rate_limit_enabled: bool = env_bool("RATE_LIMIT_ENABLED", True)
    rate_limit_rpm: int = env_int("RATE_LIMIT_RPM", 100)
    rate_limit_voice_rpm: int = env_int("RATE_LIMIT_VOICE_RPM", 30)
    rate_limit_window_seconds: int = env_int("RATE_LIMIT_WINDOW_SECONDS", 60)

    # --- Résilience AssemblyAI ---
    assemblyai_timeout_seconds: float = env_float("ASSEMBLYAI_TIMEOUT_SECONDS", 30.0)
    assemblyai_max_retries: int = env_int("ASSEMBLYAI_MAX_RETRIES", 3)
    assemblyai_retry_backoff_seconds: float = env_float("ASSEMBLYAI_RETRY_BACKOFF", 1.0)
    circuit_breaker_threshold: int = env_int("CIRCUIT_BREAKER_THRESHOLD", 5)
    circuit_breaker_cooldown_seconds: float = env_float("CIRCUIT_BREAKER_COOLDOWN", 30.0)

    # --- Outils / simulateur ---
    tool_timeout_seconds: float = env_float("TOOL_TIMEOUT_SECONDS", 10.0)
    simulate_latency: bool = env_bool("SIMULATE_LATENCY", False)


settings = Settings()
