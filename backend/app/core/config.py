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


class Settings:
    app_name: str = os.getenv("APP_NAME", "voiceops")
    version: str = os.getenv("APP_VERSION", "0.1.0")
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))
    log_level: str = os.getenv("LOG_LEVEL", "info")
    debug: bool = env_bool("DEBUG", False)
    environment: str = os.getenv("ENVIRONMENT", "development")
    assemblyai_api_key: str = os.getenv("ASSEMBLYAI_API_KEY", "")
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./voiceops.db")


settings = Settings()
