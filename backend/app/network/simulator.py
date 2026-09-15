import json
import random
import time
from pathlib import Path

from app.core.config import settings

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
SIMULATOR_DIR = BACKEND_DIR.parent / "simulator"


class DeviceNotFoundError(KeyError):
    pass


class ScenarioNotFoundError(KeyError):
    pass


class NetworkSimulator:
    """Environnement réseau simulé (aucun accès au matériel réel).

    Deux sources de données :
    - les fichiers statiques de `simulator/` (réseau de démo par défaut) ;
    - un descripteur importé (topologie arbitraire) via `NetworkSimulator.from_dict`.
    """

    def __init__(self, data_dir: Path = SIMULATOR_DIR, simulate_latency: bool | None = None):
        self.data_dir = data_dir
        self.simulate_latency = (
            settings.simulate_latency if simulate_latency is None else simulate_latency
        )
        self.devices: dict = self._load("devices.json")
        self.topology: dict = self._load("topology.json")
        self.scenarios: list = self._load("scenarios.json")

    @classmethod
    def from_dict(
        cls, data: dict, simulate_latency: bool | None = None
    ) -> "NetworkSimulator":
        """Construit un simulateur depuis un descripteur réseau arbitraire.

        `data` expose `devices` (dict nom → attributs), `topology` (dict) et
        `scenarios` (liste) — le même contrat que les fichiers statiques.
        """
        instance = cls.__new__(cls)
        instance.data_dir = None
        instance.simulate_latency = (
            settings.simulate_latency if simulate_latency is None else simulate_latency
        )
        instance.devices = data.get("devices", {})
        instance.topology = data.get("topology", {})
        instance.scenarios = data.get("scenarios", [])
        return instance

    def to_dict(self) -> dict:
        """Le descripteur du réseau (réutilisable pour un ré-import)."""
        return {
            "devices": self.devices,
            "topology": self.topology,
            "scenarios": self.scenarios,
        }

    def _load(self, filename: str):
        with (self.data_dir / filename).open(encoding="utf-8") as fh:
            return json.load(fh)

    def _maybe_latency(self) -> None:
        """Reproduit une latence réseau réaliste (100-500 ms) si activée."""
        if self.simulate_latency:
            time.sleep(random.uniform(0.1, 0.5))

    def get_device(self, name: str) -> dict:
        self._maybe_latency()
        try:
            return self.devices[name]
        except KeyError as exc:
            raise DeviceNotFoundError(name) from exc

    def list_devices(self) -> list[dict]:
        self._maybe_latency()
        return [{"name": name, **device} for name, device in self.devices.items()]

    def get_scenario(self, scenario_id: str) -> dict:
        self._maybe_latency()
        for scenario in self.scenarios:
            if scenario["id"] == scenario_id:
                return scenario
        raise ScenarioNotFoundError(scenario_id)

    def list_scenarios(self) -> list[dict]:
        self._maybe_latency()
        return self.scenarios


simulator = NetworkSimulator()
