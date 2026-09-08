from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Incident, Report

router = APIRouter(prefix="/api", tags=["reports"])

DEFAULT_ACTIONS = [
    "Vérifier la configuration de l'équipement",
    "Contrôler la connectivité (câble, port, VLAN)",
    "Redémarrer le service/équipement concerné",
    "Revalider le scénario de bout en bout",
]


def build_report_content(incident: Incident) -> str:
    lines = [
        f"Incident #VO-{incident.id:03d}",
        "",
        "Date :",
        f"  {incident.created_at.isoformat() if incident.created_at else 'N/D'}",
        "",
        "Équipement :",
        f"  {incident.device or 'N/D'}",
        "",
        "Catégorie :",
        f"  {incident.category or 'N/D'}",
        "",
        "Symptôme :",
        f"  {incident.description or 'N/D'}",
        "",
        "Diagnostic :",
        f"  {incident.diagnosis or 'N/D'}",
        "",
        "Cause probable :",
        f"  {incident.root_cause or 'N/D'}",
        "",
        "Sévérité :",
        f"  {incident.severity}",
        "",
        "Actions recommandées :",
    ]
    if incident.root_cause:
        lines.append("  " + "\n  ".join(DEFAULT_ACTIONS))
    else:
        lines += [f"  {i}. {action}" for i, action in enumerate(DEFAULT_ACTIONS, 1)]
    lines += [
        "",
        "Statut :",
        f"  {incident.status}",
    ]
    return "\n".join(lines)


@router.post("/incidents/{incident_id}/report", status_code=201)
def generate_report(incident_id: int, db: Session = Depends(get_db)) -> dict:
    incident = db.get(Incident, incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident introuvable")
    report = Report(incident_id=incident_id, content=build_report_content(incident))
    db.add(report)
    db.commit()
    db.refresh(report)
    return report.to_dict()


@router.get("/reports/{report_id}")
def get_report(report_id: int, db: Session = Depends(get_db)) -> dict:
    report = db.get(Report, report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Rapport introuvable")
    return report.to_dict()


@router.get("/incidents/{incident_id}/reports")
def list_incident_reports(incident_id: int, db: Session = Depends(get_db)) -> list[dict]:
    reports = db.scalars(
        select(Report).where(Report.incident_id == incident_id)
    ).all()
    return [r.to_dict() for r in reports]
