"""Gestion des sessions voix : création et clôture (persistance SQLite)."""

from datetime import UTC, datetime

from sqlalchemy.orm import Session as DbSession

from app.models import Session as VoiceSession


def create(db: DbSession, incident_id: int | None = None) -> VoiceSession:
    """Ouvre une session voix et la persiste."""
    session = VoiceSession(incident_id=incident_id)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def end(db: DbSession, session_id: int) -> VoiceSession:
    """Clôture une session (ended_at)."""
    session = db.get(VoiceSession, session_id)
    if session is None:
        raise KeyError(f"Session introuvable : {session_id}")
    session.ended_at = datetime.now(UTC)
    db.commit()
    db.refresh(session)
    return session
