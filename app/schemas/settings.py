"""Settings schemas."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class SettingsOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    start_date: date | None = None
    timezone: str
    tracked_repos: list[str] = Field(default_factory=list)
    pomo_work_min: int
    pomo_short_break_min: int
    pomo_long_break_min: int
    pomo_marathon_break_min: int
    pomo_cycles_per_set: int
    pomo_cycles_per_marathon: int
    weekly_target_min: int
    weekly_target_max: int


class SettingsPatch(BaseModel):
    start_date: date | None = None
    timezone: str | None = None
    tracked_repos: list[str] | None = None
    pomo_work_min: int | None = Field(default=None, ge=1, le=180)
    pomo_short_break_min: int | None = Field(default=None, ge=1, le=60)
    pomo_long_break_min: int | None = Field(default=None, ge=1, le=120)
    pomo_marathon_break_min: int | None = Field(default=None, ge=1, le=240)
    pomo_cycles_per_set: int | None = Field(default=None, ge=1, le=12)
    pomo_cycles_per_marathon: int | None = Field(default=None, ge=1, le=24)
    weekly_target_min: int | None = Field(default=None, ge=0, le=80)
    weekly_target_max: int | None = Field(default=None, ge=0, le=80)