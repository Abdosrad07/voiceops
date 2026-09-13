from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.incident import utcnow


class Session(Base):
    __tablename__ = "sessions"
    __table_args__ = (
        Index("ix_sessions_incident_id", "incident_id"),
        Index("ix_sessions_started_at", "started_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    incident_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("incidents.id"), nullable=True
    )
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    incident = relationship("Incident", backref="sessions")
    tool_calls = relationship("ToolCall", backref="session")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "incident_id": self.incident_id,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
        }
