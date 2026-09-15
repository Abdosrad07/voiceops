"""Accès générique aux équipements du réseau actif.

Les fonctions acceptent un simulateur explicite (tests) ou résolvent le
réseau actif (importé en base, sinon démo statique) automatiquement.
"""

from app.network import active
from app.network.simulator import (
    DeviceNotFoundError,
    NetworkSimulator,
    ScenarioNotFoundError,
)


def _sim(sim: NetworkSimulator | None) -> NetworkSimulator:
    return sim if sim is not None else active.active_simulator()


def get_device(name: str, sim: NetworkSimulator | None = None) -> dict:
    """Retourne l'équipement du réseau actif ou lève DeviceNotFoundError."""
    return _sim(sim).get_device(name)


def list_devices(sim: NetworkSimulator | None = None) -> list[dict]:
    return _sim(sim).list_devices()


def get_scenario(scenario_id: str, sim: NetworkSimulator | None = None) -> dict:
    return _sim(sim).get_scenario(scenario_id)


def list_scenarios(sim: NetworkSimulator | None = None) -> list[dict]:
    return _sim(sim).list_scenarios()


__all__ = [
    "DeviceNotFoundError",
    "ScenarioNotFoundError",
    "get_device",
    "list_devices",
    "get_scenario",
    "list_scenarios",
]
