from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.incident import utcnow


class ToolCall(Base):
    __tablename__ = "tool_calls"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("sessions.id"), nullable=True
    )
    tool_name: Mapped[str] = mapped_column(Text)
    arguments: Mapped[str] = mapped_column(Text, default="")
    result: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "tool_name": self.tool_name,
            "arguments": self.arguments,
            "result": self.result,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
