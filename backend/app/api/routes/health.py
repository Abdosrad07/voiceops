"""Endpoints de supervision : sonde basique et health check détaillé."""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database import get_db

router = APIRouter(tags=["health"])

STATUS_OK = "ok"
STATUS_DEGRADED = "degraded"
STATUS_DOWN = "down"


@router.get("/health")
def health() -> dict:
    """Sonde basique : toujours OK quand le processus répond."""
    return {"status": STATUS_OK}


@router.get("/health/deep")
def deep_health(db: Session = Depends(get_db)) -> dict:
    """Health check détaillé : base de données, RAG, configuration AssemblyAI."""
    checks: dict = {"database": STATUS_DOWN, "rag": STATUS_DOWN}
    degraded = False

    try:
        db.execute(text("SELECT 1"))
        checks["database"] = STATUS_OK
    except Exception as exc:  # pragma: no cover - dépend de l'infra
        checks["database_detail"] = str(exc)
        degraded = True

    try:
        from app.rag.retriever import initialize

        index = initialize()
        checks["rag"] = STATUS_OK
        checks["rag_chunks"] = index.n_docs
    except Exception as exc:
        checks["rag_detail"] = str(exc)
        degraded = True

    checks["assemblyai"] = (
        STATUS_OK if settings.assemblyai_api_key.strip() else STATUS_DOWN
    )
    checks["environment"] = settings.environment
    if checks["assemblyai"] == STATUS_DOWN:
        degraded = True

    status = STATUS_DEGRADED if degraded else STATUS_OK
    return {"status": status, "checks": checks}
