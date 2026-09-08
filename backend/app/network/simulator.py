import json
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
SIMULATOR_DIR = BACKEND_DIR.parent / "simulator"


class DeviceNotFoundError(KeyError):
    pass


class ScenarioNotFoundError(KeyError):
    pass


class NetworkSimulator:
    """Environnement réseau 100 % simulé (aucun accès au matériel réel)."""

    def __init__(self, data_dir: Path = SIMULATOR_DIR) -> None:
        self.data_dir = data_dir
        self.devices: dict = self._load("devices.json")
        self.topology: dict = self._load("topology.json")
        self.scenarios: list = self._load("scenarios.json")

    def _load(self, filename: str):
        with (self.data_dir / filename).open(encoding="utf-8") as fh:
            return json.load(fh)

    def get_device(self, name: str) -> dict:
        try:
            return self.devices[name]
        except KeyError as exc:
            raise DeviceNotFoundError(name) from exc

    def list_devices(self) -> list[dict]:
        return [{"name": name, **device} for name, device in self.devices.items()]

    def get_scenario(self, scenario_id: str) -> dict:
        for scenario in self.scenarios:
            if scenario["id"] == scenario_id:
                return scenario
        raise ScenarioNotFoundError(scenario_id)

    def list_scenarios(self) -> list[dict]:
        return self.scenarios


simulator = NetworkSimulator()
