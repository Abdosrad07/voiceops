"""Validation et normalisation de descripteurs de réseaux importés.

Un descripteur réseau est un dict JSON avec les clés :
- `devices` : obligatoire, dict {nom: {attributs}}
- `topology` : optionnel, dict (liens, ports…)
- `scenarios` : optionnel, liste de dicts ; si absente, les scénarios
  sont déduits automatiquement des défauts repérés dans les attributs.
"""

from __future__ import annotations

from typing import Any

# ---- Attributs par défaut --------------------------------------------------

_DEFAULT_DEVICE_ATTRS: dict[str, Any] = {
    "type": "Device",
    "dhcp": "ok",
    "dns": "ok",
    "status": "online",
    "reachable": True,
}


# ---- Normalisation des équipements -----------------------------------------

def normalize_devices(raw: dict) -> dict[str, dict]:
    """Valide et normalise un dict d'équipements importé."""
    if not isinstance(raw, dict) or not raw:
        raise ValueError("payload.devices doit être un objet non vide {nom: {attributs}}")

    devices: dict[str, dict] = {}
    for name, attrs in raw.items():
        if not isinstance(name, str) or not isinstance(attrs, dict):
            raise ValueError(f"Équipement invalide : {name!r}")
        devices[name] = {**_DEFAULT_DEVICE_ATTRS, **attrs}
    return devices


# ---- Déduction automatique des scénarios ----------------------------------

def derive_scenarios(devices: dict[str, dict]) -> list[dict]:
    """Génère des scénarios listant les défauts repérés dans les attributs."""
    scenarios: list[dict] = []

    for name, a in devices.items():
        # DHCP
        if a.get("dhcp") not in (None, "ok"):
            scenarios.append({
                "id": f"dhcp-{name}",
                "name": "DHCP failure",
                "symptom": "Adresse 169.254.x.x",
                "cause": "Échec DHCP",
                "devices": [name],
            })

        # VLAN mismatch
        vlan, expected = a.get("vlan"), a.get("expected_vlan")
        if vlan is not None and expected is not None and vlan != expected:
            scenarios.append({
                "id": f"vlan-{name}",
                "name": "VLAN mismatch",
                "symptom": "PC inaccessible",
                "cause": "Mauvais VLAN",
                "devices": [name],
            })

        # DNS
        if a.get("dns") not in (None, "ok"):
            scenarios.append({
                "id": f"dns-{name}",
                "name": "DNS failure",
                "symptom": "Internet accessible par IP mais pas par nom",
                "cause": "Problème DNS",
                "devices": [name],
            })

        # Passerelle injoignable
        if a.get("reachable") is False:
            if a.get("status", "online") == "online":
                scenarios.append({
                    "id": f"gateway-{name}",
                    "name": "Gateway unreachable",
                    "symptom": "Passerelle injoignable",
                    "cause": "Problème de connectivité locale",
                    "devices": [name],
                })
            else:
                scenarios.append({
                    "id": f"interface-{name}",
                    "name": "Interface down",
                    "symptom": "Équipement inaccessible",
                    "cause": "Interface désactivée",
                    "devices": [name],
                })
        elif a.get("status") not in (None, "online"):
            scenarios.append({
                "id": f"interface-{name}",
                "name": "Interface down",
                "symptom": "Équipement inaccessible",
                "cause": "Interface désactivée",
                "devices": [name],
            })

    return scenarios


# ---- Validation globale du descripteur ------------------------------------

def validate_descriptor(raw: dict) -> dict:
    """Valide et renvoie un descripteur réseau normalisé.

    Lève ``ValueError`` si le descripteur est invalide.
    """
    if not isinstance(raw, dict):
        raise ValueError("payload doit être un objet JSON")

    devices = normalize_devices(raw.get("devices"))

    topology = raw.get("topology")
    if not isinstance(topology, dict):
        topology = {}

    scenarios = raw.get("scenarios")
    if scenarios is None:
        scenarios = derive_scenarios(devices)
    elif not isinstance(scenarios, list):
        raise ValueError("payload.scenarios doit être une liste")
    else:
        # Conserver uniquement les scénarios dont les équipements existent
        filtered: list[dict] = []
        for s in scenarios:
            if not isinstance(s, dict):
                continue
            referenced = s.get("devices")
            if isinstance(referenced, list) and referenced:
                referenced = [d for d in referenced if d in devices]
                if referenced:
                    filtered.append({**s, "devices": referenced})
        scenarios = filtered

    return {"devices": devices, "topology": topology, "scenarios": scenarios}
