"""Phase model - a top-level group of weeks (e.g. "Mois 1-1.5 - Python solide").

Phases are seeded from the ``### Mois ...`` headers in roadmap.md and own a
collection of weeks. Order is preserved by ``position`` for sidebar display.
"""

from __future__ import annotations

from sqlalchemy import Integer, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Phase(Base):
    __tablename__ = "phases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # Stable key derived from the header line (e.g. "mois-1-1-5-python-solide").
    # Used for idempotent upserts by the importer.
    key: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    # Human-readable title shown in the UI, e.g. "Mois 1-1.5 - Python solide".
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    # Ordering of phases in the sidebar / accordion.
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # Optional subtitle / months range parsed from the header.
    subtitle: Mapped[str | None] = mapped_column(String(200), nullable=True)
    # Free-form notes block (the ``> `` blockquote lines that follow a phase header,
    # e.g. buffer warnings) - kept for display under the phase.
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    weeks: Mapped[list["Week"]] = relationship(
        back_populates="phase",
        cascade="all, delete-orphan",
        order_by="Week.number",
    )

    def __repr__(self) -> str:
        return f"<Phase id={self.id} key={self.key!r} title={self.title!r}>"