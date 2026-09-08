from fastapi.testclient import TestClient

from app.main import app
from app.network import diagnostics

client = TestClient(app)


def test_check_ip() -> None:
    result = diagnostics.check_ip_configuration("PC-B204")
    assert result["status"] == "apipa"
    assert result["ip"] == "169.254.14.23"
    assert result["ok"] is False

    result_ok = diagnostics.check_ip_configuration("PC-B203")
    assert result_ok["status"] == "ok"
    assert result_ok["ok"] is True


def test_check_vlan() -> None:
    result = diagnostics.check_vlan("PC-B204")
    assert result["status"] == "mismatch"
    assert result["vlan"] == 10
    assert result["expected_vlan"] == 20

    conform = diagnostics.check_vlan("PC-B203")
    assert conform["ok"] is True


def test_check_dhcp() -> None:
    result = diagnostics.check_dhcp("PC-B204")
    assert result["status"] == "failed"
    assert result["ok"] is False

    ok = diagnostics.check_dhcp("PC-B203")
    assert ok["status"] == "ok"


def test_check_gateway() -> None:
    assert diagnostics.check_gateway("PC-B201")["ok"] is False
    assert diagnostics.check_gateway("PC-B203")["ok"] is True


def test_check_dns() -> None:
    assert diagnostics.check_dns("PC-B203")["ok"] is False
    assert diagnostics.check_dns("PC-B204")["ok"] is True


def test_diagnosis() -> None:
    result = diagnostics.diagnosis("PC-B204")
    assert result["device"] == "PC-B204"
    assert result["nb_issues"] >= 2
    assert "VLAN" in result["root_cause"] or "DHCP" in result["root_cause"]
    assert result["severity"] != "low"
    assert result["recommended_actions"]


def test_unknown_device_raises_404() -> None:
    response = client.get("/api/diagnostics/device/INEXISTANT/vlan")
    assert response.status_code == 404

    response = client.get("/api/diagnostics/device/PC-B204/inexistant")
    assert response.status_code == 400


def test_api_diagnostics() -> None:
    response = client.get("/api/diagnostics/devices")
    assert response.status_code == 200
    names = {d["name"] for d in response.json()}
    assert "PC-B204" in names

    diagnosis = client.get("/api/diagnostics/device/PC-B204/diagnosis")
    assert diagnosis.status_code == 200
    body = diagnosis.json()
    assert body["nb_issues"] >= 2
