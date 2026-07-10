"""Week schemas."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.models.week import WeekStatus


class WeekOut(BaseModel):
    """Full week as returned by GET endpoints."""

    model_config = ConfigDict(from_attributes=True)

    number: int
    phase_id: int
    theme: str
    resources: str
    deliverable: str
    hours_min: float
    hours_max: float
    buffer: bool
    week_label: str | None = None
    status: WeekStatus
    actual_hours: float
    recap_sunday: str | None = None
    reviewed_at: str | None = None


class WeekPatch(BaseModel):
    """Partial update of a week's user state (auth-protected).

    Only user-owned fields are mutable; plan fields (theme, hours_min, ...)
    are importer-controlled and not patchable from the API.
    """

    actual_hours: float | None = Field(default=None, ge=0)
    recap_sunday: str | None = None
    reviewed_at: str | None = None
    status: WeekStatus | None = None