from app.api.routes.reports import build_report_content
from app.models import Incident


def test_create_incident(db_client) -> None:
    response = db_client.post(
        "/api/incidents",
        json={
            "title": "PC sans réseau",
            "description": "Le PC du bureau 204 n'accède plus au réseau.",
            "device": "PC-B204",
            "category": "Network / VLAN",
            "severity": "medium",
            "diagnosis": "VLAN incorrect",
            "root_cause": "Port associé au VLAN 10 au lieu du VLAN 20",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["id"] == 1
    assert body["status"] == "OPEN"
    assert body["device"] == "PC-B204"


def test_list_and_get_incident(db_client) -> None:
    db_client.post("/api/incidents", json={"title": "Incident A"})
    db_client.post("/api/incidents", json={"title": "Incident B"})

    response = db_client.get("/api/incidents")
    assert response.status_code == 200
    assert len(response.json()) == 2

    detail = db_client.get("/api/incidents/1")
    assert detail.status_code == 200
    assert detail.json()["title"] == "Incident A"


def test_update_incident_status_tracks_history(db_client) -> None:
    db_client.post("/api/incidents", json={"title": "Incident A"})

    response = db_client.patch("/api/incidents/1", json={"status": "INVESTIGATING"})
    assert response.status_code == 200
    assert response.json()["status"] == "INVESTIGATING"

    history = db_client.get("/api/incidents/1/history").json()["history"]
    assert len(history) == 1
    assert history[0]["from"] == "OPEN"
    assert history[0]["to"] == "INVESTIGATING"

    invalid = db_client.patch("/api/incidents/1", json={"status": "BOGUS"})
    assert invalid.status_code == 422


def test_report_generation(db_client) -> None:
    created = db_client.post(
        "/api/incidents",
        json={
            "title": "PC sans réseau",
            "device": "PC-B204",
            "category": "Network / VLAN",
            "diagnosis": "Échec DHCP + mauvais VLAN",
            "root_cause": "Configuration incorrecte du port du switch",
            "severity": "high",
        },
    ).json()

    response = db_client.post(f"/api/incidents/{created['id']}/report")
    assert response.status_code == 201
    report = response.json()
    assert report["incident_id"] == created["id"]
    assert "Incident #VO-001" in report["content"]
    assert "PC-B204" in report["content"]
    assert "Configuration incorrecte" in report["content"]

    reports = db_client.get(f"/api/incidents/{created['id']}/reports").json()
    assert len(reports) == 1


def test_build_report_content() -> None:
    incident = Incident(title="Test", device="PC-X", diagnosis="D", root_cause="R")
    incident.id = 5
    content = build_report_content(incident)
    assert "Incident #VO-005" in content
    assert "PC-X" in content
