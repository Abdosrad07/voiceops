from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.network import active, diagnostics
from app.network.devices import (
    DeviceNotFoundError,
    get_device,
    list_devices,
    list_scenarios,
)

router = APIRouter(prefix="/api/diagnostics", tags=["diagnostics"])

TOOLS: dict[str, callable] = {
    "ip": diagnostics.check_ip_configuration,
    "vlan": diagnostics.check_vlan,
    "dhcp": diagnostics.check_dhcp,
    "dns": diagnostics.check_dns,
    "gateway": diagnostics.check_gateway,
    "ping": diagnostics.ping_host,
    "traceroute": diagnostics.traceroute,
    "status": diagnostics.get_device_status,
}


@router.get("/devices")
def api_list_devices(db: Session = Depends(get_db)) -> list[dict]:
    return list_devices(active.active_simulator(db))


@router.get("/scenarios")
def api_list_scenarios(db: Session = Depends(get_db)) -> list[dict]:
    return list_scenarios(active.active_simulator(db))


@router.get("/device/{name}/diagnosis")
def api_diagnosis(name: str, db: Session = Depends(get_db)) -> dict:
    try:
        return diagnostics.diagnosis(name, active.active_simulator(db))
    except DeviceNotFoundError:
        raise HTTPException(status_code=404, detail=f"Équipement inconnu : {name}") from None


@router.get("/device/{name}/{tool}")
def api_run_tool(name: str, tool: str, db: Session = Depends(get_db)) -> dict:
    if tool not in TOOLS:
        raise HTTPException(status_code=400, detail=f"Outil inconnu : {tool}")
    try:
        return TOOLS[tool](name, active.active_simulator(db))
    except DeviceNotFoundError:
        raise HTTPException(status_code=404, detail=f"Équipement inconnu : {name}") from None


@router.get("/device/{name}")
def api_get_device(name: str, db: Session = Depends(get_db)) -> dict:
    try:
        device = get_device(name, active.active_simulator(db))
    except DeviceNotFoundError:
        raise HTTPException(status_code=404, detail=f"Équipement inconnu : {name}") from None
    return {"name": name, **device}
