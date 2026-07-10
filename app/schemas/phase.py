"""Phase schemas."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class PhaseOut(BaseModel):
    """Lightweight phase (no weeks)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    key: str
    title: str
    position: int
    subtitle: str | None = None
    notes: str | None = None


class PhaseWithWeeks(PhaseOut):
    """Phase with its ordered weeks - the shape the list endpoint returns."""

    weeks: list["WeekOut"] = []


# Avoid circular import at module load: define the forward ref target here.
from app.schemas.week import WeekOut  # noqa: E402

PhaseWithWeeks.model_rebuild()