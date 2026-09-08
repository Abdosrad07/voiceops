"""Middleware de tool calling pour le flux vocal.

Intercepte les demandes d'appel d'outil émanant de l'agent, exécute la
fonction Python associée (liste blanche dans agents/tools) et produit le
résultat exact destiné à être renvoyé à l'agent.

Ce module est volontairement indépendant du SDK AssemblyAI : le mapping
vers les événements réels (`item.function_call.completed`, etc.) est fait
dans la boucle de flux (Phase 2). Le contrat de Phase 2 pourra ainsi être
testé de façon déterministe ici.
"""

import json
from typing import Any

from app.agents.tools import execute_tool_call


class ToolCallError(Exception):
    """Outillage invalide ou échec d'exécution d'un appel d'outil."""


def process_tool_call(name: str, arguments: str | dict[str, Any]) -> dict:
    """Exécute l'appel d'outil et renvoie un dict prêt pour l'agent.

    En cas d'échec, on renvoie structurellement un message d'erreur lisible
    par l'agent afin que la conversation continue.
    """
    try:
        result = execute_tool_call(name, arguments)
        return {"name": name, "result": result, "error": None}
    except Exception as exc:
        return {"name": name, "result": None, "error": str(exc)}


def tool_result_payload(tool_call_id: str, payload: dict) -> dict[str, Any]:
    """Construit le payload JSON à injecter dans le flux de l'agent."""
    return {
        "type": "function_call_output",
        "call_id": tool_call_id,
        "output": json.dumps(payload, ensure_ascii=False),
    }
