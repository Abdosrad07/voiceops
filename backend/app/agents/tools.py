"""Enregistrement des outils exposés à l'agent vocal.

Chaque outil est une fonction Python (liste blanche) exposée avec un nom,
une description et un schéma JSON décrivant ses arguments. L'agent les appelle
uniquement lorsque cela est nécessaire.
"""

import json
from collections.abc import Callable
from typing import Any

from app.network import diagnostics


def _device_schema(extra: dict | None = None) -> dict:
    return {
        "type": "object",
        "properties": {
            "device": {
                "type": "string",
                "description": "Nom de l'équipement réseau (ex. PC-B204)",
            }
        },
        "required": ["device"],
        **({"extra": extra} if extra else {}),
    }


def schema_create_incident() -> dict:
    return {
        "type": "object",
        "properties": {
            "title": {"type": "string", "description": "Titre court de l'incident"},
            "device": {"type": "string", "description": "Équipement concerné"},
            "description": {"type": "string", "description": "Symptôme observé"},
            "diagnosis": {"type": "string", "description": "Conclusion du diagnostic"},
            "root_cause": {"type": "string", "description": "Cause probable"},
            "severity": {
                "type": "string",
                "enum": ["low", "medium", "high", "critical"],
                "description": "Sévérité de l'incident",
            },
        },
        "required": ["title"],
    }


def _list_devices() -> dict:
    from app.network.devices import list_devices

    return {"devices": list_devices()}


def _get_device(name: str) -> dict:
    from app.network.devices import get_device

    return {"name": name, **get_device(name)}


def _create_incident(
    title: str,
    device: str = "",
    description: str = "",
    diagnosis: str = "",
    root_cause: str = "",
    severity: str = "medium",
) -> dict:
    from sqlalchemy.orm import Session

    from app.database import engine
    from app.models import Incident

    with Session(engine) as db:
        incident = Incident(
            title=title,
            device=device,
            description=description,
            diagnosis=diagnosis,
            root_cause=root_cause,
            severity=severity,
        )
        db.add(incident)
        db.commit()
        db.refresh(incident)
        return {"incident": incident.to_dict()}


def _generate_report(incident_id: int) -> dict:
    from sqlalchemy.orm import Session

    from app.api.routes.reports import build_report_content
    from app.database import engine
    from app.models import Incident, Report

    with Session(engine) as db:
        incident = db.get(Incident, incident_id)
        if incident is None:
            raise KeyError(f"Incident introuvable : {incident_id}")
        report = Report(incident_id=incident.id, content=build_report_content(incident))
        db.add(report)
        db.commit()
        db.refresh(report)
        return {"report": report.to_dict()}


def _search_knowledge(query: str) -> dict:
    from app.rag.retriever import search_knowledge

    try:
        return search_knowledge(query)
    except Exception as exc:  # pragma: no cover - dépend de la Phase 5
        return {"query": query, "results": [], "error": str(exc)}


_HANDLERS: dict[str, Callable[..., dict]] = {
    "list_devices": _list_devices,
    "get_device": _get_device,
    "get_device_status": diagnostics.get_device_status,
    "check_ip_configuration": diagnostics.check_ip_configuration,
    "check_gateway": diagnostics.check_gateway,
    "check_dhcp": diagnostics.check_dhcp,
    "check_dns": diagnostics.check_dns,
    "check_vlan": diagnostics.check_vlan,
    "ping_host": diagnostics.ping_host,
    "traceroute": diagnostics.traceroute,
    "run_diagnosis": diagnostics.diagnosis,
    "create_incident": _create_incident,
    "generate_report": _generate_report,
    "search_knowledge": _search_knowledge,
}


def execute_tool_call(name: str, arguments: str | dict[str, Any]) -> dict:
    """Exécute un appel d'outil (nom + arguments JSON) et renvoie le résultat.

    Coeur du middleware de tool calling : validation de la liste blanche puis
    exécution de la fonction Python correspondante.
    """
    if name not in _HANDLERS:
        raise ValueError(f"Outil non autorisé : {name}")
    params: dict[str, Any] = (
        json.loads(arguments) if isinstance(arguments, str) else (arguments or {})
    )
    handler = _HANDLERS[name]
    result = handler(**params)
    return result if isinstance(result, dict) else {"result": result}


TOOLS: list[dict] = [
    {
        "name": "list_devices",
        "description": "Liste tous les équipements du réseau simulé.",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_device",
        "description": "Retourne les caractéristiques d'un équipement précis.",
        "parameters": _device_schema(),
    },
    {
        "name": "get_device_status",
        "description": "États up/down du périphérique réseau.",
        "parameters": _device_schema(),
    },
    {
        "name": "check_ip_configuration",
        "description": "Vérifie la configuration IP du poste.",
        "parameters": _device_schema(),
    },
    {
        "name": "check_gateway",
        "description": "Teste la joignabilité de la passerelle par défaut.",
        "parameters": _device_schema(),
    },
    {
        "name": "check_dhcp",
        "description": "Vérifie que le poste a obtenu une adresse par DHCP.",
        "parameters": _device_schema(),
    },
    {
        "name": "check_dns",
        "description": "Vérifie la résolution DNS du poste.",
        "parameters": _device_schema(),
    },
    {
        "name": "check_vlan",
        "description": "Vérifie que le poste est sur le bon VLAN.",
        "parameters": _device_schema(),
    },
    {
        "name": "ping_host",
        "description": "Teste la connectivité ICMP vers un hôte.",
        "parameters": {
            "type": "object",
            "properties": {
                "host": {"type": "string", "description": "Hôte cible (nom ou IP)"}
            },
            "required": ["host"],
        },
    },
    {
        "name": "traceroute",
        "description": "Trace la route vers un hôte.",
        "parameters": {
            "type": "object",
            "properties": {
                "host": {"type": "string", "description": "Hôte cible (nom ou IP)"}
            },
            "required": ["host"],
        },
    },
    {
        "name": "run_diagnosis",
        "description": "Exécute le diagnostic complet d'un équipement.",
        "parameters": _device_schema(),
    },
    {
        "name": "create_incident",
        "description": "Crée un incident à partir de l'analyse.",
        "parameters": schema_create_incident(),
    },
    {
        "name": "generate_report",
        "description": "Génère le rapport structuré d'un incident.",
        "parameters": {
            "type": "object",
            "properties": {
                "incident_id": {"type": "integer", "description": "Identifiant de l'incident"}
            },
            "required": ["incident_id"],
        },
    },
    {
        "name": "search_knowledge",
        "description": "Récupère des extraits documentaires pertinents (base de connaissances).",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Question technique posée"}
            },
            "required": ["query"],
        },
    },
]
