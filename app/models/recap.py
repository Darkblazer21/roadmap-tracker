"""Recap model - the Sunday 3-line summary for a roadmap week.

Unique on week_id. When the user clicks "Generate" the service drafts the
three fields from sessions + daily logs + github events; saving persists the
(possibly edited) version. The week detail page shows the latest recap.
"""

from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Recap(Base):
    __tablename__ = "recaps"

    week_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("weeks.number", ondelete="CASCADE"), primary_key=True
    )
    successes: Mapped[str | None] = mapped_column(Text, nullable=True)
    blockers: Mapped[str | None] = mapped_column(Text, nullable=True)
    next_step: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[str] = mapped_column(String(40), nullable=False, server_default=func.now())

    def __repr__(self) -> str:
        return f"<Recap week={self.week_id}>"