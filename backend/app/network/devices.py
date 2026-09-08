from app.network.simulator import (
    DeviceNotFoundError,
    NetworkSimulator,
    ScenarioNotFoundError,
    simulator,
)


def get_device(name: str, sim: NetworkSimulator = simulator) -> dict:
    """Retourne l'équipement simulé ou lève DeviceNotFoundError."""
    return sim.get_device(name)


def list_devices(sim: NetworkSimulator = simulator) -> list[dict]:
    return sim.list_devices()


def get_scenario(scenario_id: str, sim: NetworkSimulator = simulator) -> dict:
    return sim.get_scenario(scenario_id)


def list_scenarios(sim: NetworkSimulator = simulator) -> list[dict]:
    return sim.list_scenarios()


__all__ = [
    "DeviceNotFoundError",
    "ScenarioNotFoundError",
    "get_device",
    "list_devices",
    "get_scenario",
    "list_scenarios",
]
