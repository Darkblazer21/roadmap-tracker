"""AppSettings model - a single-row table holding all global config.

Enforced single-row via a CHECK constraint on id = 1 (the seeder always uses
id=1). Holds the roadmap start_date (the anchor for ``current_week``), the
tracked GitHub repos, pomodoro config overrides, and weekly target range.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from sqlalchemy import JSON, CheckConstraint, Date, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class AppSettings(Base):
    __tablename__ = "app_settings"
    __table_args__ = (CheckConstraint("id = 1", name="single_row_settings"),)

    # Always id=1; the CHECK constraint guarantees only one settings row.
    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)

    # The anchor: week 1 starts on this date. Null until the user sets it.
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Timezone for week-window math (IANA name, e.g. "Africa/Dakar").
    # Stored as string; week_clock uses zoneinfo if available.
    timezone: Mapped[str] = mapped_column(String(60), nullable=False, default="UTC")

    # Tracked GitHub repos: list of "owner/repo" strings.
    tracked_repos: Mapped[list[Any]] = mapped_column(JSON, nullable=False, default=list)

    # Pomodoro config overrides (minutes). When null/0, fall back to .env defaults.
    pomo_work_min: Mapped[int] = mapped_column(Integer, nullable=False, default=25)
    pomo_short_break_min: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    pomo_long_break_min: Mapped[int] = mapped_column(Integer, nullable=False, default=15)
    pomo_marathon_break_min: Mapped[int] = mapped_column(Integer, nullable=False, default=120)
    pomo_cycles_per_short_set: Mapped[int] = mapped_column(Integer, nullable=False, default=4)
    pomo_cycles_per_long_break: Mapped[int] = mapped_column(Integer, nullable=False, default=8)

    # Weekly hour target range (independent of per-week roadmap ranges).
    weekly_target_min: Mapped[int] = mapped_column(Integer, nullable=False, default=15)
    weekly_target_max: Mapped[int] = mapped_column(Integer, nullable=False, default=25)

    def __repr__(self) -> str:
        return f"<AppSettings id={self.id} start_date={self.start_date!r}>"