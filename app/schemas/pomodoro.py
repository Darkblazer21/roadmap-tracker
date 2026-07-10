"""Pomodoro schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class PomoStart(BaseModel):
    """Body of POST /api/pomo/start."""

    week_id: int | None = Field(
        default=None,
        description=(
            "Roadmap week to log this pomo against. "
            "Defaults to the week computed from settings.start_date."
        ),
    )


class PomoStateView(BaseModel):
    """Live timer view returned by GET /api/pomo/state."""

    phase: str
    cycle_count: int
    week_id: int | None
    target_ends_at: float | None
    remaining_sec: float
    paused: bool

    work_min: int
    short_break_min: int
    long_break_min: int
    marathon_break_min: int
    cycles_per_set: int
    cycles_per_marathon: int

    cycles_in_set: int
    set_count: int