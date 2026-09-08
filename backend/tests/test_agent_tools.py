import pytest

from app.agents.prompts import SYSTEM_PROMPT
from app.agents.tools import TOOLS, execute_tool_call
from app.voice.events import process_tool_call, tool_result_payload

TOOL_NAMES = [t["name"] for t in TOOLS]


@pytest.mark.parametrize("tool", TOOLS)
def test_tool_schema_shape(tool) -> None:
    assert tool["name"]
    assert tool["description"]
    assert "type" in tool["parameters"]
    assert "properties" in tool["parameters"]


def test_tools_covers_diagnostic_contract() -> None:
    for name in (
        "check_ip_configuration",
        "check_vlan",
        "check_dhcp",
        "check_dns",
        "check_gateway",
        "ping_host",
        "traceroute",
        "get_device_status",
        "run_diagnosis",
        "create_incident",
        "generate_report",
        "search_knowledge",
    ):
        assert name in TOOL_NAMES


def test_execute_check_vlan_via_middleware() -> None:
    result = execute_tool_call("check_vlan", {"device": "PC-B204"})
    assert result["status"] == "mismatch"
    assert result["expected_vlan"] == 20


def test_execute_run_diagnosis() -> None:
    result = execute_tool_call("run_diagnosis", '{"device": "PC-B204"}')
    assert result["device"] == "PC-B204"
    assert result["nb_issues"] >= 2


def test_execute_unknown_tool_rejected() -> None:
    with pytest.raises(ValueError):
        execute_tool_call("rm_rf", {})


def test_process_tool_call_success_and_error() -> None:
    ok = process_tool_call("ping_host", {"host": "RTR-CORE"})
    assert ok["name"] == "ping_host"
    assert ok["error"] is None
    assert "result" in ok

    err = process_tool_call("nope", {})
    assert err["name"] == "nope"
    assert err["error"] is not None


def test_tool_result_payload_shape() -> None:
    payload = process_tool_call("check_dhcp", {"device": "PC-B204"})
    out = tool_result_payload("call_1", payload["result"])
    assert out["type"] == "tool.result"
    assert out["call_id"] == "call_1"
    assert "PC-B204" in out["result"]


def test_system_prompt_french_and_complete() -> None:
    assert SYSTEM_PROMPT.lstrip().startswith("Tu es VoiceOps")
    assert "check_vlan" not in SYSTEM_PROMPT  # aucun inventaire d'outil en dur
    assert "192.168.20.1" in SYSTEM_PROMPT
