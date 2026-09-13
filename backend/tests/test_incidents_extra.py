"""Tests des nouveaux endpoints et du workflow de statut (pagination, filtres)."""


def _seed(db_client, titles: list[str]) -> None:
    for i, title in enumerate(titles):
        db_client.post(
            "/api/incidents",
            json={
                "title": title,
                "device": f"PC-B{i + 1}",
                "category": "Network / VLAN",
                "severity": ["low", "medium", "high", "critical"][i % 4],
                "description": f"Description du {title} (DHCP en échec)",
            },
        )


def test_pagination_and_total(db_client) -> None:
    _seed(db_client, ["A", "B", "C"])
    body = db_client.get("/api/incidents?limit=2&offset=1").json()
    assert body["total"] == 3
    assert len(body["items"]) == 2
    assert body["limit"] == 2
    assert body["offset"] == 1


def test_filter_by_status_and_severity(db_client) -> None:
    _seed(db_client, ["A", "B", "C", "D"])
    assert db_client.patch("/api/incidents/1", json={"status": "INVESTIGATING"}).status_code == 200
    assert db_client.patch("/api/incidents/1", json={"status": "RESOLVED"}).status_code == 200

    open_items = db_client.get("/api/incidents?status=OPEN").json()["items"]
    assert len(open_items) == 3
    critical_items = db_client.get("/api/incidents?severity=critical").json()["items"]
    assert len(critical_items) == 1
    resolved = db_client.get("/api/incidents?status=resolved").json()["items"]
    assert len(resolved) == 1


def test_filter_by_device_category_and_search(db_client) -> None:
    _seed(db_client, ["A", "B"])

    by_device = db_client.get("/api/incidents?device=PC-B2").json()["items"]
    assert len(by_device) == 1
    by_category = db_client.get("/api/incidents?category=Network / VLAN").json()["items"]
    assert len(by_category) == 2
    search = db_client.get("/api/incidents?q=DHCP").json()["items"]
    assert len(search) == 2
    no_match = db_client.get("/api/incidents?q=inexistant").json()["items"]
    assert no_match == []


def test_sort_and_invalid_sort_param(db_client) -> None:
    _seed(db_client, ["A", "B"])
    asc = db_client.get("/api/incidents?sort_by=created_at&sort_dir=asc").json()["items"]
    assert asc[0]["id"] == 1
    desc = db_client.get("/api/incidents?sort_dir=desc").json()["items"]
    assert desc[0]["id"] == 2
    assert db_client.get("/api/incidents?sort_by=hack").status_code == 422
    assert db_client.get("/api/incidents?sort_dir=sideways").status_code == 422


def test_status_workflow_strict_transitions(db_client) -> None:
    db_client.post("/api/incidents", json={"title": "Incident A"})

    assert db_client.patch("/api/incidents/1", json={"status": "INVESTIGATING"}).status_code == 200
    # Saut interdit : INVESTIGATING -> CLOSED
    assert db_client.patch("/api/incidents/1", json={"status": "CLOSED"}).status_code == 409
    # Re-open interdit : RESOLVED -> OPEN impossible, mais INVESTIGATING -> RESOLVED OK
    assert db_client.patch("/api/incidents/1", json={"status": "RESOLVED"}).status_code == 200
    assert db_client.patch("/api/incidents/1", json={"status": "CLOSED"}).status_code == 200
    assert db_client.patch("/api/incidents/1", json={"status": "OPEN"}).status_code == 409


def test_create_incident_validation(db_client) -> None:
    invalid_severity = db_client.post(
        "/api/incidents", json={"title": "X", "severity": "bogus"}
    )
    assert invalid_severity.status_code == 422
    missing_title = db_client.post("/api/incidents", json={"title": ""})
    assert missing_title.status_code == 422


def test_list_sessions_paginated(db_client) -> None:
    db_client.post("/api/sessions", json={})
    db_client.post("/api/sessions", json={})
    body = db_client.get("/api/sessions").json()
    assert body["total"] == 2
    assert len(body["items"]) == 2
    assert db_client.get("/api/sessions?limit=1&offset=1").json()["total"] == 2
