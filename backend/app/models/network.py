"""Réseau simulé importable : une topologie arbitraire persistée en base.

Permet à VoiceOps d'accueillir n'importe quel réseau (n'importe quelle
topologie / flotte d'équipements) sans modification de code : le descripteur
JSON (`devices`, `topology`, `scenarios`) est stocké tel quel puis rechargé
dans un `NetworkSimulator` au moment du diagnostic.
"""

import json
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Network(Base):
    __tablename__ = "networks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str] = mapped_column(String(512), default="")
    payload: Mapped[str] = mapped_column(Text, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    def descriptor(self) -> dict[str, Any]:
        """Le descripteur réseau (devices/topology/scenarios) reconstruit."""
        return json.loads(self.payload)

    def to_dict(self, include_payload: bool = False) -> dict:
        data = {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "active": self.active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_payload:
            desc = self.descriptor()
            data["device_count"] = len(desc.get("devices", {}))
            data["scenarios"] = desc.get("scenarios", [])
            data["topology"] = desc.get("topology", {})
        return data
