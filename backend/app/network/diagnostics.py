from app.network.simulator import DeviceNotFoundError, NetworkSimulator, simulator

APIPA_PREFIX = "169.254."


def _requires_device(name: str, sim: NetworkSimulator) -> dict:
    try:
        return sim.get_device(name)
    except DeviceNotFoundError:
        raise


def check_ip_configuration(
    device: str, sim: NetworkSimulator = simulator
) -> dict:
    """Analyse l'adresse IPv4 simulée du poste (détection APIPA)."""
    info = _requires_device(device, sim)
    ip = info.get("ip", "")
    apipa = ip.startswith(APIPA_PREFIX)
    return {
        "tool": "check_ip_configuration",
        "device": device,
        "ok": not apipa,
        "status": "apipa" if apipa else "ok",
        "ip": ip,
        "detail": "Adresse APIPA détectée" if apipa else "Adresse valide configurée",
    }


def check_vlan(device: str, sim: NetworkSimulator = simulator) -> dict:
    """Compare le VLAN actuel au VLAN attendu."""
    info = _requires_device(device, sim)
    vlan = info.get("vlan")
    expected = info.get("expected_vlan")
    match = vlan == expected
    return {
        "tool": "check_vlan",
        "device": device,
        "ok": match,
        "status": "mismatch" if not match else "ok",
        "vlan": vlan,
        "expected_vlan": expected,
        "detail": (
            f"VLAN actuel {vlan} différent du VLAN attendu {expected}"
            if not match
            else f"VLAN {vlan} conforme"
        ),
    }


def check_dhcp(device: str, sim: NetworkSimulator = simulator) -> dict:
    """Vérifie l'état DHCP simulé."""
    info = _requires_device(device, sim)
    dhcp = info.get("dhcp", "unknown")
    ok = dhcp == "ok"
    return {
        "tool": "check_dhcp",
        "device": device,
        "ok": ok,
        "status": dhcp,
        "detail": (
            "Échec DHCP : le poste n'a pas reçu d'adresse"
            if not ok
            else "DHCP fonctionnel"
        ),
    }


def check_dns(host: str, sim: NetworkSimulator = simulator) -> dict:
    """Vérifie la résolution DNS simulée pour un hôte connu."""
    info = _requires_device(host, sim)
    dns = info.get("dns", "ok")
    ok = dns == "ok"
    return {
        "tool": "check_dns",
        "host": host,
        "ok": ok,
        "status": dns,
        "detail": "Résolution DNS en échec" if not ok else "Résolution DNS OK",
    }


def check_gateway(device: str, sim: NetworkSimulator = simulator) -> dict:
    """Vérifie l'accessibilité de la passerelle simulée."""
    info = _requires_device(device, sim)
    gateway = info.get("gateway")
    reachable = bool(info.get("reachable", True))
    return {
        "tool": "check_gateway",
        "device": device,
        "gateway": gateway,
        "ok": reachable,
        "status": "reachable" if reachable else "unreachable",
        "detail": (
            f"Passerelle {gateway} jointe"
            if reachable
            else f"Passerelle {gateway} inaccessible"
        ),
    }


def ping_host(host: str, sim: NetworkSimulator = simulator) -> dict:
    """Ping simulé vers un hôte connu."""
    info = _requires_device(host, sim)
    reachable = bool(info.get("reachable", True)) and info.get("status") == "online"
    return {
        "tool": "ping_host",
        "host": host,
        "ok": reachable,
        "status": "ok" if reachable else "timeout",
        "rtt_ms": 1 if reachable else None,
        "detail": "Réponse reçue" if reachable else "Délai d'attente dépassé",
    }


def traceroute(host: str, sim: NetworkSimulator = simulator) -> dict:
    """Traceroute simulé à partir de la topologie."""
    _requires_device(host, sim)
    try:
        uplink = sim.get_device(host).get("type")
        hops = ["SW-A101"] if uplink != "Router" else ["RTR-CORE"]
        hops = list(dict.fromkeys(hops + ["RTR-CORE", "DNS-01"]))
    except DeviceNotFoundError:
        hops = ["RTR-CORE", "DNS-01"]
    return {"tool": "traceroute", "host": host, "ok": True, "hops": hops, "ttl": 64}


def get_device_status(device: str, sim: NetworkSimulator = simulator) -> dict:
    info = _requires_device(device, sim)
    return {
        "tool": "get_device_status",
        "device": device,
        "status": info.get("status", "unknown"),
        "type": info.get("type", "unknown"),
        "detail": "Équipement en ligne" if info.get("status") == "online" else "Hors ligne",
    }


def _severity(findings: list[dict]) -> str:
    nb_failures = sum(1 for f in findings if not f["ok"])
    if nb_failures == 0:
        return "low"
    if nb_failures >= 2:
        return "high"
    return "medium"


ACTIONS_BY_FINDING = {
    "check_vlan": [
        "Vérifier le port du switch (topologie.json)",
        "Vérifier l'affectation VLAN du port",
        "Corriger l'affectation du port",
    ],
    "check_dhcp": [
        "Renouveler la configuration DHCP du poste",
        "Vérifier la disponibilité du serveur DHCP",
    ],
    "check_dns": ["Vérifier la configuration DNS", "Tester un autre serveur DNS"],
    "check_gateway": [
        "Vérifier la connectivité locale",
        "Contrôler la passerelle par défaut",
    ],
}


def diagnosis(device: str, sim: NetworkSimulator = simulator) -> dict:
    """Batterie de contrôles : IP, DHCP, VLAN, passerelle, DNS."""
    checks = [
        check_ip_configuration(device, sim),
        check_dhcp(device, sim),
        check_vlan(device, sim),
        check_gateway(device, sim),
        check_dns(device, sim),
    ]
    failed = [c for c in checks if not c["ok"]]

    causes = [
        c["detail"]
        for c in failed
        if c["tool"] in {"check_dhcp", "check_vlan", "check_dns", "check_gateway"}
    ]
    root_cause = " ; ".join(causes) if causes else "Aucun problème détecté"

    actions: list[str] = []
    for c in failed:
        actions.extend(ACTIONS_BY_FINDING.get(c["tool"], []))

    return {
        "device": device,
        "checks": checks,
        "nb_issues": len(failed),
        "diagnosis": root_cause if failed else "Environnement nominal",
        "root_cause": root_cause,
        "severity": _severity(checks),
        "recommended_actions": actions,
    }
