from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.logging import audit_log
from app.core.security import clean_text, safe_incident_fields
from app.database import get_db
from app.models import Incident

router = APIRouter(prefix="/api/incidents", tags=["incidents"])

STATUSES = {"OPEN", "INVESTIGATING", "RESOLVED", "CLOSED"}

# Transitions autorisées (état suivant strictement adjacent, pas de saut).
TRANSITIONS: dict[str, set[str]] = {
    "OPEN": {"INVESTIGATING"},
    "INVESTIGATING": {"RESOLVED"},
    "RESOLVED": {"CLOSED"},
    "CLOSED": set(),
}

SORTABLE = {"id", "created_at", "updated_at", "severity"}


def _now() -> str:
    return datetime.now(UTC).isoformat()


class IncidentCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str = Field(default="", max_length=2000)
    device: str = Field(default="", max_length=128)
    category: str = Field(default="", max_length=128)
    severity: str = Field(default="medium", pattern="^(low|medium|high|critical)$")
    diagnosis: str = Field(default="", max_length=2000)
    root_cause: str = Field(default="", max_length=2000)


class IncidentUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    device: str | None = Field(default=None, max_length=128)
    category: str | None = Field(default=None, max_length=128)
    severity: str | None = Field(
        default=None, pattern="^(low|medium|high|critical)$"
    )
    diagnosis: str | None = Field(default=None, max_length=2000)
    root_cause: str | None = Field(default=None, max_length=2000)
    status: str | None = None


@router.post("", status_code=201)
def create_incident(payload: IncidentCreate, db: Session = Depends(get_db)) -> dict:
    cleaned = safe_incident_fields(payload.model_dump(), max_len=2000)
    incident = Incident(
        title=clean_text(cleaned["title"], 255),
        description=cleaned.get("description", ""),
        device=cleaned.get("device", ""),
        category=cleaned.get("category", ""),
        severity=cleaned.get("severity", "medium"),
        diagnosis=cleaned.get("diagnosis", ""),
        root_cause=cleaned.get("root_cause", ""),
        status="OPEN",
        status_history=[
            {"from": None, "to": "OPEN", "at": _now()},
        ],
    )
    db.add(incident)
    db.commit()
    db.refresh(incident)
    audit_log("incident.create", incident_id=incident.id, title=incident.title)
    return incident.to_dict()


@router.get("")
def list_incidents(
    status: str | None = None,
    device: str | None = None,
    category: str | None = None,
    severity: str | None = None,
    q: str | None = Query(default=None, max_length=255),
    created_after: datetime | None = None,
    created_before: datetime | None = None,
    sort_by: str = Query(default="created_at", pattern="^(id|created_at|updated_at|severity)$"),
    sort_dir: str = Query(default="desc", pattern="^(asc|desc)$"),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> dict:
    filters = []
    if status:
        filters.append(Incident.status == status.upper())
    if device:
        filters.append(Incident.device == device)
    if category:
        filters.append(Incident.category == category)
    if severity:
        filters.append(Incident.severity == severity)
    if q:
        pattern = f"%{clean_text(q, 255)}%"
        filters.append(
            or_(Incident.title.ilike(pattern), Incident.description.ilike(pattern))
        )
    if created_after:
        filters.append(Incident.created_at >= created_after)
    if created_before:
        filters.append(Incident.created_at <= created_before)

    base = select(Incident).where(*filters)
    column = getattr(Incident, sort_by)
    order = column.asc() if sort_dir == "asc" else column.desc()
    total = db.scalar(select(func.count()).select_from(base.subquery())) or 0
    incidents = db.scalars(base.order_by(order).offset(offset).limit(limit)).all()
    return {
        "items": [i.to_dict() for i in incidents],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


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
                status_code=422, detail=f"Statut inconnu : {new_status}"
            )
        old_status = incident.status
        if new_status != old_status:
            allowed = TRANSITIONS.get(old_status, set()) or set()
            if new_status not in allowed:
                raise HTTPException(
                    status_code=409,
                    detail=f"Transition de statut invalide : {old_status} → {new_status}",
                )
            data["status"] = new_status
            incident.status_history = incident.status_history + [
                {"from": old_status, "to": new_status, "at": _now()}
            ]
            audit_log(
                "incident.status_change",
                incident_id=incident_id,
                from_status=old_status,
                to_status=new_status,
            )

    for field, value in data.items():
        setattr(incident, field, value)

    db.commit()
    db.refresh(incident)
    audit_log("incident.update", incident_id=incident_id)
    return incident.to_dict()
