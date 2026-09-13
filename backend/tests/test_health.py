"""Tests des sondes de santé (basique + profonde)."""


from app.core.config import settings


def test_health_basic(db_client) -> None:
    response = db_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_deep_reports_database_and_assemblyai(db_client, monkeypatch) -> None:
    monkeypatch.setattr(settings, "assemblyai_api_key", "")
    response = db_client.get("/health/deep")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] in {"ok", "degraded"}
    assert body["checks"]["database"] == "ok"
    assert "rag" in body["checks"]
    # En environnement de test, la clé AssemblyAI est absente -> dégradé.
    assert body["checks"]["assemblyai"] == "down"
    assert body["status"] == "degraded"
