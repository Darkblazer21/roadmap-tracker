"""GithubEvent model - a cached commit/PR row from GitHub.

Events are stored after a sync so the per-week verdict can be answered from
the database without re-fetching every page. ``repo`` is "owner/repo".
``kind`` discriminates commits from PRs (M6 only fetches commits; PRs left
for later). ``authored_at`` is the commit's author date so it can be mapped
to a roadmap week via ``week_clock``.
"""

from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, Integer, String, BigInteger, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class GithubEventKind(str, enum.Enum):
    commit = "commit"
    pr = "pr"


class GithubEvent(Base):
    __tablename__ = "github_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    repo: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    sha: Mapped[str] = mapped_column(String(40), nullable=False)
    kind: Mapped[GithubEventKind] = mapped_column(
        Enum(GithubEventKind, name="github_event_kind", native_enum=False, length=20),
        nullable=False,
        default=GithubEventKind.commit,
    )
    message: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    author: Mapped[str | None] = mapped_column(String(200), nullable=True)
    authored_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    pr_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    merged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_github_events_repo_sha", "repo", "sha", unique=True),
    )

    def __repr__(self) -> str:
        return f"<GithubEvent {self.repo}@{self.sha[:8]} at={self.authored_at}>"


class GithubSyncState(Base):
    """Per-repo sync cursor: the last commit SHA seen, so we can page forward
    incrementally instead of refetching the entire history each night."""

    __tablename__ = "github_sync_state"

    repo: Mapped[str] = mapped_column(String(200), primary_key=True)
    last_sha: Mapped[str | None] = mapped_column(String(40), nullable=True)
    last_synced_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    def __repr__(self) -> str:
        return f"<GithubSyncState {self.repo} last={self.last_sha}>"