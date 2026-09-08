from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Incident

router = APIRouter(prefix="/api/incidents", tags=["incidents"])

STATUSES = {"OPEN", "INVESTIGATING", "RESOLVED", "CLOSED"}


def _now() -> str:
    return datetime.now(UTC).isoformat()


class IncidentCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str = ""
    device: str = ""
    category: str = ""
    severity: str = "medium"
    diagnosis: str = ""
    root_cause: str = ""


class IncidentUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    device: str | None = None
    category: str | None = None
    severity: str | None = None
    diagnosis: str | None = None
    root_cause: str | None = None
    status: str | None = None


@router.post("", status_code=201)
def create_incident(payload: IncidentCreate, db: Session = Depends(get_db)) -> dict:
    incident = Incident(
        title=payload.title,
        description=payload.description,
        device=payload.device,
        category=payload.category,
        severity=payload.severity,
        diagnosis=payload.diagnosis,
        root_cause=payload.root_cause,
        status="OPEN",
    )
    db.add(incident)
    db.commit()
    db.refresh(incident)
    return incident.to_dict()


@router.get("")
def list_incidents(
    status: str | None = None,
    device: str | None = None,
    db: Session = Depends(get_db),
) -> list[dict]:
    query = select(Incident)
    if status:
        query = query.where(Incident.status == status)
    if device:
        query = query.where(Incident.device == device)
    incidents = db.scalars(query.order_by(Incident.created_at.desc())).all()
    return [i.to_dict() for i in incidents]


@router.get("/{incident_id}")
def get_incident(incident_id: int, db: Session = Depends(get_db)) -> dict:
    incident = db.get(Incident, incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident introuvable")
    return incident.to_dict()


@router.get("/{incident_id}/history")
def incident_history(incident_id: int, db: Session = Depends(get_db)) -> dict:
    incident = db.get(Incident, incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident introuvable")
    return {"incident_id": incident_id, "history": incident.status_history}


@router.patch("/{incident_id}")
def update_incident(
    incident_id: int, payload: IncidentUpdate, db: Session = Depends(get_db)
) -> dict:
    incident = db.get(Incident, incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident introuvable")

    data = payload.model_dump(exclude_unset=True)
    if "status" in data:
        new_status = data["status"].upper()
        if new_status not in STATUSES:
            raise HTTPException(
                status_code=422, detail=f"Statut invalide : {new_status}"
            )
        data["status"] = new_status
        if new_status != incident.status:
            incident.status_history = incident.status_history + [
                {
                    "from": incident.status,
                    "to": new_status,
                    "at": _now(),
                }
            ]

    for field, value in data.items():
        setattr(incident, field, value)

    db.commit()
    db.refresh(incident)
    return incident.to_dict()
