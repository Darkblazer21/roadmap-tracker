"""Session model - a unit of focus time logged against a roadmap week.

Types:
  - ``focus``   : manual entry ("I studied 3h today on week 5")
  - ``pomodoro``: created automatically by the pomodoro engine (M4)

Completed pomodoro sessions automatically bump the linked week's
``actual_hours`` and trigger the ``hours_max`` cap alert (decision M5).
"""

from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class SessionType(str, enum.Enum):
    focus = "focus"
    pomodoro = "pomodoro"


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # Week this session counts toward (must exist in the weeks table).
    week_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("weeks.number", ondelete="CASCADE"), nullable=False, index=True
    )
    type: Mapped[SessionType] = mapped_column(
        Enum(SessionType, name="session_type", native_enum=False, length=20),
        nullable=False,
        default=SessionType.focus,
    )
    # When the study happened. Defaults to now() server-side.
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # Duration in seconds. Required (the importer derives hours from this).
    duration_sec: Mapped[float] = mapped_column(Float, nullable=False)
    # Optional free-form note ("studied async/await, did the bot telegram").
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    week: Mapped["Week"] = relationship()  # type: ignore[name-defined]  # noqa: F821

    def __repr__(self) -> str:
        return f"<Session id={self.id} type={self.type} dur={self.duration_sec}s week={self.week_id}>"