"""Daily log schemas."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class DailyLogBase(BaseModel):
    week_id: int
    log_date: date
    topic: str | None = None
    learned: str | None = None
    blockers: str | None = None
    hours_override: float | None = Field(default=None, ge=0)


class DailyLogOut(DailyLogBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


class DailyLogPatch(BaseModel):
    """Partial update of a daily log by id."""

    topic: str | None = None
    learned: str | None = None
    blockers: str | None = None
    hours_override: float | None = Field(default=None, ge=0)