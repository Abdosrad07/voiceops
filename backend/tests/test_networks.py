"""Import / activation de réseaux arbitraires + impact sur les diagnostics."""

CUSTOM_NETWORK = {
    "name": "Réseau entrepôt Lyon",
    "description": "Topologie importée pour la démo",
    "payload": {
        "devices": {
            "PC-B11": {
                "type": "PC", "ip": "169.254.5.11", "gateway": "10.0.5.1",
                "vlan": 30, "expected_vlan": 40, "dhcp": "failed", "dns": "ok",
                "status": "online", "reachable": True,
            },
            "SRV-DHCP": {
                "type": "Server", "ip": "10.0.5.50", "status": "online", "reachable": True,
            },
            "PC-B12": {
                "type": "PC", "ip": "10.0.5.12", "gateway": "10.0.5.1",
                "vlan": 40, "expected_vlan": 40, "dhcp": "ok", "dns": "failed",
                "status": "online", "reachable": True,
            },
        }
    },
}


def _import_network(client, name="Réseau entrepôt Lyon", payload=None):
    body = {"name": name, "description": "démo", "payload": payload or CUSTOM_NETWORK["payload"]}
    return client.post("/api/networks", json=body)


def test_import_network_first_becomes_active(db_client):
    response = _import_network(db_client)
    assert response.status_code == 201
    data = response.json()
    assert data["active"] is True
    assert data["device_count"] == 3
    ids = {s["id"] for s in data["scenarios"]}
    assert "vlan-PC-B11" in ids  # VLAN mismatch déduit
    assert "dhcp-PC-B11" in ids  # échec DHCP déduit
    assert "dns-PC-B12" in ids   # échec DNS déduit
    assert "gateway-PC-B11" not in ids  # reachable=True → pas de scenario passerelle


def test_import_invalid_payload_rejected(db_client):
    response = db_client.post("/api/networks", json={
        "name": "Bidon",
        "payload": {"devices": 1234},
    })
    assert response.status_code == 422
    response = db_client.post("/api/networks", json={"name": "Bidon", "payload": {}})
    assert response.status_code == 422


def test_diagnostics_use_imported_network(db_client):
    _import_network(db_client)  # active le réseau importé

    devices = db_client.get("/api/diagnostics/devices").json()
    names = {d["name"] for d in devices}
    assert "PC-B11" in names

    vlan = db_client.get("/api/diagnostics/device/PC-B11/vlan").json()
    assert vlan["status"] == "mismatch"
    assert vlan["vlan"] == 30 and vlan["expected_vlan"] == 40

    ip = db_client.get("/api/diagnostics/device/PC-B11/ip").json()
    assert ip["status"] == "apipa"

    scenarios = db_client.get("/api/diagnostics/scenarios").json()
    assert any(s["id"] == "vlan-PC-B11" for s in scenarios)


def test_activate_switches_network(db_client):
    first = _import_network(db_client, name="Réseau A").json()
    second = _import_network(db_client, name="Réseau B", payload={
        "devices": {
            "SW-X": {"type": "Switch", "vlan": 1, "expected_vlan": 2, "status": "online"},
            "PC-Y": {"type": "PC", "ip": "10.1.1.2", "vlan": 2, "expected_vlan": 2,
                     "dhcp": "ok", "dns": "ok", "status": "online", "reachable": True},
        }
    }).json()
    assert first["active"] is True and second["active"] is False

    response = db_client.post(f"/api/networks/{second['id']}/activate")
    assert response.status_code == 200 and response.json()["active"] is True

    devices = db_client.get("/api/diagnostics/devices").json()
    names = {d["name"] for d in devices}
    assert "SW-X" in names and "PC-B11" not in names

    vlan = db_client.get("/api/diagnostics/device/SW-X/vlan").json()
    assert vlan["status"] == "mismatch"


def test_delete_active_network_falls_back_to_static(db_client):
    imported = _import_network(db_client).json()
    assert imported["active"] is True

    response = db_client.delete(f"/api/networks/{imported['id']}")
    assert response.status_code == 204

    devices = db_client.get("/api/diagnostics/devices").json()
    names = {d["name"] for d in devices}
    assert "PC-B204" in names and "PC-B11" not in names


def test_list_and_get(db_client):
    imported = _import_network(db_client).json()
    listing = db_client.get("/api/networks").json()
    assert listing["total"] == 1 and listing["items"][0]["id"] == imported["id"]

    detail = db_client.get(f"/api/networks/{imported['id']}").json()
    assert detail["device_count"] == 3

    assert db_client.get("/api/networks/99999").status_code == 404
