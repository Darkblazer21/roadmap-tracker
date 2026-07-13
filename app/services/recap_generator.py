"""Sunday recap generator: aggregates the week's data into a 3-line draft.

Pulls from:
  - sessions (total hours, count, by type)
  - daily_logs (topics learned, blockers) - the main texture
  - week plan fields (scheduled theme + deliverable) to suggest next step

The draft is in French (matches the roadmap's "3 lignes succès / blocages /
prochaine étape" convention). The user edits + saves the final ``Recap`` row.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.daily_log import DailyLog
from app.models.session import Session
from app.models.week import Week
from app.schemas.recap import RecapDraft


class WeekNotFoundError(Exception):
    """Raised when a recap is requested for a week that does not exist."""


async def generate_draft(db: AsyncSession, week_id: int) -> RecapDraft:
    """Build the Sunday recap draft for week ``week_id``."""
    week = await db.get(Week, week_id)
    if week is None:
        raise WeekNotFoundError(week_id)

    sessions = (
        await db.execute(select(Session).where(Session.week_id == week_id))
    ).scalars().all()
    daily_logs = (
        await db.execute(
            select(DailyLog).where(DailyLog.week_id == week_id).order_by(DailyLog.log_date)
        )
    ).scalars().all()

    total_hours = sum(s.duration_sec for s in sessions) / 3600.0
    by_type: dict[str, float] = defaultdict(float)
    by_day: dict[str, float] = defaultdict(float)
    for s in sessions:
        by_type[s.type.value] += s.duration_sec / 3600.0
        day_key = s.started_at.strftime("%Y-%m-%d") if isinstance(s.started_at, datetime) else ""
        by_day[day_key] += s.duration_sec / 3600.0

    # --- Successes line ---
    n_days_active = len({k for k in by_day if k})
    pomo_h = by_type.get("pomodoro", 0.0)
    successes_parts: list[str] = []
    if total_hours > 0:
        successes_parts.append(f"{total_hours:.1f}h cumulées cette semaine")
    if n_days_active > 0:
        successes_parts.append(f"activité sur {n_days_active} jour(s)")
    if pomo_h > 0:
        pomo_count = int(pomo_h * 60 / 25)
        successes_parts.append(f"{pomo_count} pomos complétés")
    topics = [dl.topic for dl in daily_logs if dl.topic]
    if topics:
        successes_parts.append("sujets : " + ", ".join(topics[:3]))
    successes_line = " ; ".join(p for p in successes_parts if p) or "Pas d'activité enregistrée."

    # --- Blockers line ---
    blockers = [dl.blockers for dl in daily_logs if dl.blockers and dl.blockers.strip()]
    if blockers:
        blockers_line = " ; ".join(blockers)
    elif week.status.value == "late":
        blockers_line = "Semaine marquée en retard - revoir le planning."
    else:
        blockers_line = "Aucun blocage noté."

    # --- Next step line ---
    next_parts: list[str] = [f"Semaine {week.number + 1} :"]
    next_week = (
        await db.execute(select(Week).where(Week.number == week_id + 1))
    ).scalar_one_or_none()
    if next_week is not None:
        next_parts.append(f"thème « {next_week.theme} »")
        if next_week.deliverable:
            # Keep the deliverable hint short so the line stays readable.
            short = next_week.deliverable.split("(")[0].strip()[:80]
            next_parts.append(f"livrable : {short}")
    else:
        next_parts.append("plan terminé - orientation finale : portfolio / candidatures remote.")
    if blockers:
        next_parts.append("- lever les blocages ci-dessus")
    next_step_line = " ".join(next_parts).strip() or "Continuer le plan."

    return RecapDraft(
        week_id=week_id,
        successes=successes_line,
        blockers=blockers_line,
        next_step=next_step_line,
    )