from datetime import UTC, datetime

from sqlalchemy import JSON, DateTime, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def utcnow() -> datetime:
    return datetime.now(UTC)


class Incident(Base):
    __tablename__ = "incidents"
    __table_args__ = (
        Index("ix_incidents_device", "device"),
        Index("ix_incidents_category", "category"),
        Index("ix_incidents_severity", "severity"),
        Index("ix_incidents_status", "status"),
        Index("ix_incidents_created_at", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    device: Mapped[str] = mapped_column(String(128), default="")
    category: Mapped[str] = mapped_column(String(128), default="")
    severity: Mapped[str] = mapped_column(String(32), default="medium")
    diagnosis: Mapped[str] = mapped_column(Text, default="")
    root_cause: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(32), default="OPEN")
    status_history: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "device": self.device,
            "category": self.category,
            "severity": self.severity,
            "diagnosis": self.diagnosis,
            "root_cause": self.root_cause,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
