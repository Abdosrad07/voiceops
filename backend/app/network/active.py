"""Résolution du réseau actif pour les diagnostics et les outils agent.

Priorité :
1. le réseau importé `active=True` en base (topologie arbitraire) ;
2. sinon le simulateur statique de démo (`simulator/*.json`).

La lecture via `SessionLocal` (hors requête HTTP, ex. outil agent exécuté
dans un thread) est protégée : toute erreur (base absente, table inexistante,
descripteur invalide) replie silencieusement sur le simulateur statique.
"""

from __future__ import annotations

import threading
import time

from sqlalchemy import select

from app.database import SessionLocal
from app.models import Network
from app.network.simulator import NetworkSimulator

DEFAULT_SIMULATOR = NetworkSimulator()

_CACHE_SECONDS = 2.0
_cache: dict = {}
_lock = threading.Lock()


def _static() -> NetworkSimulator:
    """Le réseau de démo par défaut (fichiers statiques)."""
    return DEFAULT_SIMULATOR


def _from_db(db) -> NetworkSimulator | None:
    """Le simulateur du réseau actif en base, ou None si aucun actif."""
    network = db.scalar(select(Network).where(Network.active.is_(True)))
    if network is None:
        return None
    try:
        return NetworkSimulator.from_dict(network.descriptor())
    except Exception:
        return None


def active_simulator(db=None) -> NetworkSimulator:
    """Renvoie le simulateur du réseau actif (cache court si pas de session)."""
    if db is not None:
        try:
            return _from_db(db) or _static()
        except Exception:
            return _static()

    now = time.monotonic()
    with _lock:
        cached = _cache.get("sim")
        if cached and now - cached["ts"] < _CACHE_SECONDS:
            return cached["sim"]

    sim = _load_from_session()
    with _lock:
        _cache["sim"] = {"sim": sim, "ts": now}
    return sim


def _load_from_session() -> NetworkSimulator:
    try:
        with SessionLocal() as db:
            return _from_db(db) or _static()
    except Exception:
        return _static()


def invalidate() -> None:
    """Invalide le cache après une activation/suppression de réseau."""
    with _lock:
        _cache.pop("sim", None)
