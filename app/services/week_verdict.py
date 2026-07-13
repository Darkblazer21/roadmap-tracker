"""Week verdict: for each tracked repo × each roadmap week, decide
✅ on-time / ⚠️ activity-but-outside-window / ❌ no-commits.

A commit is "on-time" for week ``n`` if it falls inside that week's 7-day
window as defined by ``week_clock.week_window(n, start_date)``. When the
start_date isn't configured yet, every verdict is reported as "deferred".
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.github_event import GithubEvent
from app.models.settings import AppSettings
from app.models.week import Week
from app.services.week_clock import week_window

VERDICT_ON_TIME = "on_time"
VERDICT_LATE = "late"
VERDICT_MISSING = "missing"
VERDICT_DEFERRED = "deferred"
VERDICT_FUTURE = "future"


def verdict_to_emoji(v: str) -> str:
    return {
        VERDICT_ON_TIME: "✅",
        VERDICT_LATE: "⚠️",
        VERDICT_MISSING: "❌",
        VERDICT_DEFERRED: "⏸",
        VERDICT_FUTURE: "—",
    }.get(v, "?")


async def compute_verdicts(
    db: AsyncSession,
    weeks_back: int = 56,
) -> dict[str, dict[int, dict[str, object]]]:
    """Return ``{repo: {week_number: {verdict, count, latest_at}}}``.

    Only weeks up to the current calendar week are graded; future weeks are
    marked ``future`` and weeks before ``start_date`` is set are ``deferred``.
    """
    settings = (
        await db.execute(select(AppSettings).where(AppSettings.id == 1))
    ).scalar_one_or_none()
    if settings is None:
        return {}

    repos = settings.tracked_repos or []
    if not repos:
        return {}

    if settings.start_date is None:
        return {repo: {} for repo in repos}

    start = settings.start_date
    tz = settings.timezone

    # Calendar current week (evaluated in the user's configured timezone).
    from app.services.week_clock import current_week_number

    cal_week = current_week_number(start, tz=tz) or 0

    # Collect events per repo.
    result: dict[str, dict[int, dict[str, object]]] = {repo: {} for repo in repos}
    events = (
        await db.execute(select(GithubEvent).order_by(GithubEvent.authored_at.desc()))
    ).scalars().all()

    per_repo_week_events: dict[str, dict[int, list[GithubEvent]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for ev in events:
        if ev.repo not in result:
            continue
        week_n = _week_number_for(ev, start, tz)
        if week_n is not None:
            per_repo_week_events[ev.repo][week_n].append(ev)

    # Fetch all plan weeks so we know valid week numbers.
    plan_weeks = (
        await db.execute(select(Week).order_by(Week.number))
    ).scalars().all()
    plan_week_numbers = {w.number for w in plan_weeks}

    for repo in repos:
        for n in range(1, cal_week + 1):
            if n not in plan_week_numbers:
                continue
            window_start, window_end = week_window(n, start, tz)
            evs = per_repo_week_events[repo].get(n, [])

            if evs:
                # Any commit inside the window?
                inside = [
                    e for e in evs
                    if _in_window(e, window_start, window_end)
                ]
                latest_at = max(
                    (e.authored_at for e in evs), default=None
                )
                if inside:
                    result[repo][n] = {
                        "verdict": VERDICT_ON_TIME,
                        "count": len(inside),
                        "latest_at": latest_at.isoformat() if latest_at else None,
                    }
                else:
                    # Commits exist but none inside the window.
                    result[repo][n] = {
                        "verdict": VERDICT_LATE,
                        "count": len(evs),
                        "latest_at": latest_at.isoformat() if latest_at else None,
                    }
            else:
                result[repo][n] = {
                    "verdict": VERDICT_MISSING,
                    "count": 0,
                    "latest_at": None,
                }

        # Future weeks get a "future" marker for the UI.
        for n in range(cal_week + 1, max(plan_week_numbers) + 1):
            if n in plan_week_numbers:
                result[repo][n] = {
                    "verdict": VERDICT_FUTURE,
                    "count": 0,
                    "latest_at": None,
                }

    return result


def _week_number_for(ev: GithubEvent, start: date, tz: str | None = None) -> int | None:
    """Map a commit's authored_at to a roadmap week number (or None).

    The commit instant is mapped to the user's local date so week bucketing
    matches the week windows (which are also computed in ``tz``).
    """
    dt = ev.authored_at
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    from app.services.week_clock import _resolve_zone, current_week_number

    zone = _resolve_zone(tz)
    local_date = dt.astimezone(zone).date() if zone is not None else dt.date()
    return current_week_number(start, local_date)


def _in_window(ev: GithubEvent, window_start: datetime, window_end: datetime) -> bool:
    dt = ev.authored_at
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    ws = window_start.replace(tzinfo=timezone.utc) if window_start.tzinfo is None else window_start
    we = window_end.replace(tzinfo=timezone.utc) if window_end.tzinfo is None else window_end
    return ws <= dt < we