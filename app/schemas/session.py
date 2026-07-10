"""Session schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.session import SessionType


class SessionCreate(BaseModel):
    """Manual log entry. ``duration_sec`` is required; ended_at optional."""

    week_id: int = Field(..., description="Roadmap week number the session counts toward")
    type: SessionType = Field(default=SessionType.focus)
    duration_sec: float = Field(..., gt=0, description="Focus duration in seconds")
    started_at: datetime | None = Field(
        default=None, description="When it happened; defaults to now() server-side"
    )
    ended_at: datetime | None = None
    notes: str | None = None


class SessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    week_id: int
    type: SessionType
    started_at: datetime
    ended_at: datetime | None
    duration_sec: float
    notes: str | None


class WeekAggregate(BaseModel):
    """Per-week hour rollup returned by GET /sessions/aggregate."""

    week_id: int
    total_sec: float
    total_hours: float
    by_type: dict[str, float]  # {"focus": 7200.0, "pomodoro": 1500.0}
    by_day: dict[str, float]  # {"2026-07-10": 7200.0, ...}
    session_count: int
    # Comparison vs the week's plan range (filled by the router).
    hours_min: float
    hours_max: float
    actual_hours: float  # same as total_hours, for convenience
    over_cap: bool
    under_min: bool
    in_range: bool