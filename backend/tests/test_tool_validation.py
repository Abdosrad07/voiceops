"""Tests de validation stricte des appels d'outils et de leur budget temps."""

import time

import pytest

from app.agents.tools import (
    ToolTimeoutError,
    _run_with_timeout,
    execute_tool_call,
    validate_arguments,
)


def test_validate_unknown_parameter() -> None:
    with pytest.raises(ValueError, match="inconnu"):
        validate_arguments("ping_host", {"host": "x", "bogus": 1})


def test_validate_too_many_parameters() -> None:
    with pytest.raises(ValueError, match="Trop de paramètres"):
        validate_arguments(
            "create_incident",
            {
                "title": "A",
                "device": "B",
                "description": "C",
                "diagnosis": "D",
                "root_cause": "E",
                "severity": "high",
            },
        )


def test_validate_type_mismatch_and_enum() -> None:
    with pytest.raises(ValueError, match="type invalide"):
        validate_arguments("check_vlan", {"device": 123})
    with pytest.raises(ValueError, match="hors valeurs autorisées"):
        validate_arguments("create_incident", {"title": "A", "severity": "bogus"})


def test_validate_missing_required() -> None:
    with pytest.raises(ValueError, match="requis manquants"):
        validate_arguments("ping_host", {})


def test_execute_tool_call_rejects_malformed_arguments() -> None:
    with pytest.raises(ValueError, match="objet JSON"):
        execute_tool_call("list_devices", [1, 2])


def test_tool_call_times_out() -> None:
    def slow(**kwargs) -> dict:
        time.sleep(0.2)
        return {"ok": True}

    with pytest.raises(ToolTimeoutError, match="dépassé"):
        _run_with_timeout(slow, {}, 0.01)


def test_execute_tool_call_with_ok_arg_uses_handler_timeout() -> None:
    result = execute_tool_call("check_vlan", {"device": "PC-B204"}, timeout=1.0)
    assert result["status"] == "mismatch"
