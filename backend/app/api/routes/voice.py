from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.security import MissingApiKeyError, clean_text
from app.database import get_db
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
    except Exception as exc:  # HTTPError, réseaux, API down...
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


@router.post("/api/tools/execute")
def execute_agent_tool(payload: ToolExecuteRequest) -> dict:
    """Exécute un appel d'outil demandé par l'agent (relais navigateur → backend)."""
    payload.name = clean_text(payload.name, 128)
    result = process_tool_call(payload.name, payload.arguments)
    if result["error"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result["result"]


class SessionCreateRequest(BaseModel):
    incident_id: int | None = None


@router.post("/api/sessions", status_code=201)
def open_session(payload: SessionCreateRequest, db: Session = Depends(get_db)) -> dict:
    return sessions.create(db, incident_id=payload.incident_id).to_dict()


@router.post("/api/sessions/{session_id}/end")
def close_session(session_id: int, db: Session = Depends(get_db)) -> dict:
    try:
        return sessions.end(db, session_id).to_dict()
    except KeyError:
        raise HTTPException(status_code=404, detail="Session introuvable") from None
