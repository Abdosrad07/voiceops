import httpx
from fastapi.testclient import TestClient

from app.core.security import MissingApiKeyError
from app.main import app
from app.voice import assemblyai
from app.voice.events import tool_result_payload

client = TestClient(app)


def test_voice_config_contract() -> None:
    config = assemblyai.build_voice_config()
    assert config["system_prompt"].startswith("Tu es VoiceOps")
    assert config["greeting"]
    assert config["output"]["voice"] == "ivy"
    tools = {tool["name"] for tool in config["tools"]}
    assert "check_vlan" in tools
    assert "create_incident" in tools
    # la clé API ne doit jamais apparaître dans la config navigateur
    assert "api_key" not in config
    assert not any("key" in tool for tool in config["tools"])


def test_create_voice_token_uses_spec_endpoint_and_returns_token() -> None:
    captures = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captures["url"] = str(request.url)
        captures["auth"] = request.headers.get("Authorization")
        return httpx.Response(
            200,
            json={"token": "tok_abc", "expires_in_seconds": 300},
        )

    with httpx.Client(transport=httpx.MockTransport(handler)) as transport:
        token = assemblyai.create_voice_token(
            api_key="sk_test_123",
            base_url="https://api.assemblyai.com/v1",
            client=transport,
        )

    assert token.token == "tok_abc"
    assert token.expires_in_seconds == 300
    assert captures["auth"] == "Bearer sk_test_123"
    assert captures["url"] == "https://api.assemblyai.com/v1/token?expires_in_seconds=300&max_session_duration_seconds=1800"


def test_voice_token_endpoint_contract(monkeypatch) -> None:
    monkeypatch.setattr(
        assemblyai,
        "create_voice_token",
        lambda: assemblyai.VoiceTokenResponse(token="t", expires_in_seconds=300),
    )
    response = client.get("/api/voice-token")
    assert response.status_code == 200
    body = response.json()
    assert body["token"] == "t"
    assert body["expires_in_seconds"] == 300
    assert body["config"]["system_prompt"]
    assert "tools" in body["config"]


def test_voice_token_endpoint_without_key_returns_503(monkeypatch) -> None:
    monkeypatch.setattr(
        assemblyai,
        "create_voice_token",
        lambda: (_ for _ in ()).throw(MissingApiKeyError("ASSEMBLYAI_API_KEY absente")),
    )
    response = client.get("/api/voice-token")
    assert response.status_code == 503
    assert "ASSEMBLYAI_API_KEY" in response.json()["detail"]


def test_execute_agent_tool_endpoint() -> None:
    response = client.post(
        "/api/tools/execute",
        json={"name": "check_vlan", "call_id": "call_1", "arguments": {"device": "PC-B204"}},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "mismatch"

    bad = client.post(
        "/api/tools/execute",
        json={"name": "not_a_tool", "arguments": {}},
    )
    assert bad.status_code == 400


def test_tool_result_payload_for_assemblyai() -> None:
    out = tool_result_payload("call_2", {"status": "mismatch"})
    assert out["type"] == "tool.result"
    assert out["call_id"] == "call_2"
    assert '"mismatch"' in out["result"]


def test_session_lifecycle(db_client) -> None:
    created = db_client.post("/api/sessions", json={})
    assert created.status_code == 201
    session_id = created.json()["id"]
    assert created.json()["ended_at"] is None

    ended = db_client.post(f"/api/sessions/{session_id}/end")
    assert ended.status_code == 200
    assert ended.json()["ended_at"] is not None

    missing = db_client.post("/api/sessions/9999/end")
    assert missing.status_code == 404


def test_build_voice_config_is_http_error_safe() -> None:
    """La config ne doit jamais exposer un chemin d'outil exécutable par le client."""
    config = assemblyai.build_voice_config()
    for tool in config["tools"]:
        assert tool["type"] == "function"
        assert "name" in tool and "description" in tool and "parameters" in tool
