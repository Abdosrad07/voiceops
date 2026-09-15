"""Gestion des réseaux simulés importés : CRUD + activation.

Permet d'injecter n'importe quelle topologie (descripteur JSON) et de la
rendre active pour les diagnostics et les outils de l'agent vocal, sans
aucune modification de code.
"""

import json

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.logging import audit_log
from app.core.security import clean_text
from app.database import get_db
from app.models import Network
from app.network import active
from app.network.imports import validate_descriptor

router = APIRouter(prefix="/api/networks", tags=["networks"])


class NetworkCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    description: str = Field(default="", max_length=512)
    payload: dict = Field(..., description="Descripteur réseau (devices, topology, scenarios)")


def _get_network(db: Session, network_id: int) -> Network:
    network = db.get(Network, network_id)
    if network is None:
        raise HTTPException(status_code=404, detail="Réseau introuvable")
    return network


@router.get("")
def list_networks(db: Session = Depends(get_db)) -> dict:
    rows = db.scalars(select(Network).order_by(Network.created_at.desc())).all()
    return {"items": [row.to_dict() for row in rows], "total": len(rows)}


@router.post("", status_code=201)
def import_network(payload: NetworkCreate, db: Session = Depends(get_db)) -> dict:
    """Importe une topologie arbitraire ; devient active si aucune ne l'est."""
    name = clean_text(payload.name, 128)
    description = clean_text(payload.description, 512)
    try:
        descriptor = validate_descriptor(payload.payload)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from None

    has_active = db.scalar(select(Network).where(Network.active.is_(True))) is not None
    network = Network(
        name=name,
        description=description,
        payload=json.dumps(descriptor, ensure_ascii=False),
        active=not has_active,
    )
    db.add(network)
    db.commit()
    db.refresh(network)
    audit_log("network.import", network_id=network.id, active=network.active)
    if network.active:
        active.invalidate()
    return network.to_dict(include_payload=True)


@router.get("/{network_id}")
def get_network(network_id: int, db: Session = Depends(get_db)) -> dict:
    network = _get_network(db, network_id)
    return network.to_dict(include_payload=True)


@router.post("/{network_id}/activate")
def activate_network(network_id: int, db: Session = Depends(get_db)) -> dict:
    """Active un réseau importé : il sert désormais diagnostics et outils."""
    network = _get_network(db, network_id)
    for row in db.scalars(select(Network).where(Network.active.is_(True))).all():
        row.active = False
    network.active = True
    db.commit()
    db.refresh(network)
    audit_log("network.activate", network_id=network.id)
    active.invalidate()
    return network.to_dict(include_payload=True)


@router.delete("/{network_id}", status_code=204)
def delete_network(network_id: int, db: Session = Depends(get_db)) -> None:
    network = _get_network(db, network_id)
    was_active = network.active
    db.delete(network)
    db.commit()
    audit_log("network.delete", network_id=network_id)
    if was_active:
        active.invalidate()
