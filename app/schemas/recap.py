"""Recap schemas."""

from __future__ import annotations

from pydantic import BaseModel


class RecapDraft(BaseModel):
    """Generated draft - returned but not persisted until the user saves."""

    week_id: int
    successes: str
    blockers: str
    next_step: str


class RecapSave(BaseModel):
    """User-edited saved version."""

    week_id: int
    successes: str | None = None
    blockers: str | None = None
    next_step: str | None = None


class RecapOut(RecapSave):
    updated_at: str | None = None