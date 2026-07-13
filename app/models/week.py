"""Week model - a single row of a roadmap markdown table.

A week is identified by its plan number (1..56) and belongs to exactly one
phase. User-mutable state (``status``, ``actual_hours``, ``recap``) lives here
but is overwritten only by explicit user action, never by the importer - the
importer upserts only the plan fields (``theme``, ``resources``,
``deliverable``, ``hours_min``, ``hours_max``, ``buffer``) and leaves user
state untouched.
"""

from __future__ import annotations

import enum

from sqlalchemy import Boolean, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class WeekStatus(str, enum.Enum):
    """Lifecycle state of a week, set by the user (not the importer)."""

    not_started = "not_started"
    in_progress = "in_progress"
    done = "done"
    late = "late"  # user-edited: behind plan but still working it
    skipped = "skipped"


class Week(Base):
    __tablename__ = "weeks"

    # Roadmap plan number (1..56). Unique across the whole plan - the importer
    # is idempotent on this column.
    number: Mapped[int] = mapped_column(Integer, primary_key=True)
    phase_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("phases.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # --- Plan fields (importer-owned, upserted on every import) ---
    theme: Mapped[str] = mapped_column(String(300), nullable=False)
    resources: Mapped[str] = mapped_column(Text, nullable=False, default="")
    deliverable: Mapped[str] = mapped_column(Text, nullable=False, default="")
    hours_min: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    hours_max: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    # True for known buffer weeks (19-22, 33-34) flagged in the roadmap notes.
    buffer: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # Label like "Semaines 11-12" when a row spans multiple plan weeks.
    week_label: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # --- User state (never touched by the importer) ---
    status: Mapped[WeekStatus] = mapped_column(
        Enum(WeekStatus, name="week_status", native_enum=False, length=20),
        nullable=False,
        default=WeekStatus.not_started,
    )
    actual_hours: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    recap_sunday: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_at: Mapped[str | None] = mapped_column(String(40), nullable=True)

    phase: Mapped["Phase"] = relationship(back_populates="weeks")  # noqa: F821

    def __repr__(self) -> str:
        return f"<Week number={self.number} theme={self.theme[:40]!r}>"