"""DailyLog model - one row per day of study (free-form notes + blockers).

Daily logs are distinct from ``Session`` (which measures *time*): they capture
*qualitative* state - today's topic, what you learned, what's stuck - and are
rolled up into the Sunday recap draft by ``recap_generator``.

A (week_id, date) pair is unique. ``hours_override`` lets the user correct the
hours for a day if sessions didn't cover something they read offline.
"""

from __future__ import annotations

from sqlalchemy import Date, Float, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class DailyLog(Base):
    __tablename__ = "daily_logs"
    __table_args__ = (UniqueConstraint("week_id", "log_date", name="uq_daily_week_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    week_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("weeks.number", ondelete="CASCADE"), nullable=False, index=True
    )
    log_date: Mapped[str] = mapped_column(Date, nullable=False, index=True)
    topic: Mapped[str | None] = mapped_column(String(300), nullable=True)
    learned: Mapped[str | None] = mapped_column(Text, nullable=True)
    blockers: Mapped[str | None] = mapped_column(Text, nullable=True)
    # When non-null, overrides the session-derived hours for the recap.
    hours_override: Mapped[float | None] = mapped_column(Float, nullable=True)

    def __repr__(self) -> str:
        return f"<DailyLog id={self.id} week={self.week_id} date={self.log_date}>"