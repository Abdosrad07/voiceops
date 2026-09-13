from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.logging import audit_log
from app.core.security import MissingApiKeyError, clean_text
from app.database import get_db
from app.models import Session as SessionModel
from app.models import ToolCall
from app.voice import assemblyai, sessions
from app.voice.events import process_tool_call

router = APIRouter(tags=["voice"])


@router.get("/api/voice-token")
def voice_token() -> dict:
    """Mint un token temporaire AssemblyAI + la configuration de session serveur."""
    try:
        token = assemblyai.create_voice_token()
    except MissingApiKeyError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from None
    except Exception as exc:  # HTTPError, réseaux, circuit ouvert...
        raise HTTPException(status_code=502, detail=f"Erreur AssemblyAI : {exc}") from None
    return {
        "token": token.token,
        "expires_in_seconds": token.expires_in_seconds,
        "max_session_duration_seconds": token.max_session_duration_seconds,
        "config": assemblyai.build_voice_config(),
    }


class ToolExecuteRequest(BaseModel):
    name: str
    call_id: str = ""
    arguments: dict | str = {}
    session_id: int | None = None


@router.post("/api/tools/execute")
def execute_agent_tool(
    payload: ToolExecuteRequest, db: Session = Depends(get_db)
) -> dict:
    """Exécute un appel d'outil demandé par l'agent (relais navigateur → backend)."""
    payload.name = clean_text(payload.name, 128)
    result = process_tool_call(payload.name, payload.arguments)
    stored_result = clean_text(str(result.get("result") or result.get("error") or ""), 2000)
    stored_args = clean_text(str(payload.arguments), 2000)
    if payload.session_id:
        tool_call = ToolCall(
            session_id=payload.session_id,
            tool_name=payload.name,
            arguments=stored_args,
            result=stored_result,
        )
        db.add(tool_call)
        db.commit()
        audit_log(
            "tool.execute",
            tool=payload.name,
            ok=not result["error"],
        )
    if result["error"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result["result"]


class SessionCreateRequest(BaseModel):
    incident_id: int | None = None


@router.post("/api/sessions", status_code=201)
def open_session(payload: SessionCreateRequest, db: Session = Depends(get_db)) -> dict:
    session = sessions.create(db, incident_id=payload.incident_id)
    audit_log("session.open", session_id=session.id)
    return session.to_dict()


@router.get("/api/sessions")
def list_sessions(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    sort_dir: str = Query(default="desc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db),
) -> dict:
    query = select(SessionModel)
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    order = (
        SessionModel.started_at.asc()
        if sort_dir == "asc"
        else SessionModel.started_at.desc()
    )
    items = db.scalars(query.order_by(order).offset(offset).limit(limit)).all()
    return {
        "items": [s.to_dict() for s in items],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.post("/api/sessions/{session_id}/end")
def close_session(session_id: int, db: Session = Depends(get_db)) -> dict:
    try:
        session = sessions.end(db, session_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Session introuvable") from None
    audit_log("session.end", session_id=session.id)
    return session.to_dict()
