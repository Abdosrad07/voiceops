"""Logging structuré JSON + audit trail pour VoiceOps.

Chaque enregistrement porte un `request_id` (contextvar via middleware web)
et une horodatation ISO. Les données sensibles (clés API, tokens, adresses IP
réelles du réseau simulé) ne sont jamais journalisées.
"""

import json
import logging
from contextvars import ContextVar
from datetime import UTC, datetime
from typing import Any

_request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)


def get_request_id() -> str | None:
    return _request_id_var.get()


def set_request_id(value: str) -> None:
    _request_id_var.set(value)


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
            "request_id": get_request_id(),
        }
        extra = getattr(record, "extra", None)
        if isinstance(extra, dict):
            payload.update(extra)
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False, default=str)


def setup_logging() -> None:
    level = logging.INFO  # niveau INFO par défaut
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger("app")
    root.handlers = [handler]
    root.setLevel(level)
    root.propagate = False


def get_logger(name: str) -> logging.Logger:
    package_logger = logging.getLogger(f"app.{name}")
    return package_logger


def audit_log(action: str, **details: Any) -> None:
    """Journalise une action métier (création/modification incident, outil, session).

    `details` ne doit contenir que des champs non sensibles (ids, statuts).
    """
    get_logger("audit").info(
        action,
        extra={
            "extra": {
                "event": "audit",
                "action": action,
                **{k: str(v) for k, v in details.items()},
            }
        },
    )
