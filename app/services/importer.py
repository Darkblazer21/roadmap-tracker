"""Database seeder: idempotently upsert phases and weeks from parsed roadmap.

The seeder never overwrites user-owned fields (``status``, ``actual_hours``,
``recap_sunday``, ``reviewed_at``). Only the plan fields imported from
``roadmap.md`` are updated on every run, so editing the markdown and
re-importing is safe.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.phase import Phase
from app.models.week import Week
from app.roadmap_parser import ParsedPhase


async def seed_from_parsed(
    session: AsyncSession,
    parsed_phases: list[ParsedPhase],
) -> tuple[int, int]:
    """Upsert phases and weeks. Returns (phases_upserted, weeks_upserted)."""
    n_phases = 0
    n_weeks = 0

    for pp in parsed_phases:
        # --- Upsert phase by key ---
        phase_result = await session.execute(select(Phase).where(Phase.key == pp.key))
        phase: Phase | None = phase_result.scalar_one_or_none()

        if phase is None:
            phase = Phase(
                key=pp.key,
                title=pp.title,
                position=pp.position,
                subtitle=pp.subtitle,
                notes=pp.notes,
            )
            session.add(phase)
            await session.flush()  # get the id
            n_phases += 1
        else:
            # Update plan fields only
            phase.title = pp.title
            phase.position = pp.position
            phase.subtitle = pp.subtitle
            phase.notes = pp.notes
            n_phases += 1

        # --- Upsert weeks by number ---
        for pw in pp.weeks:
            week_result = await session.execute(select(Week).where(Week.number == pw.number))
            week: Week | None = week_result.scalar_one_or_none()

            if week is None:
                week = Week(
                    number=pw.number,
                    phase_id=phase.id,
                    theme=pw.theme,
                    resources=pw.resources,
                    deliverable=pw.deliverable,
                    hours_min=pw.hours_min,
                    hours_max=pw.hours_max,
                    buffer=pw.buffer,
                    week_label=pw.week_label,
                )
                session.add(week)
                n_weeks += 1
            else:
                # Update plan fields only, preserve user state
                week.phase_id = phase.id
                week.theme = pw.theme
                week.resources = pw.resources
                week.deliverable = pw.deliverable
                week.hours_min = pw.hours_min
                week.hours_max = pw.hours_max
                week.buffer = pw.buffer
                week.week_label = pw.week_label
                n_weeks += 1

    await session.commit()
    return n_phases, n_weeks


async def sync_database(session: AsyncSession, markdown: str) -> tuple[int, int]:
    """Parse the markdown then seed. Convenience wrapper for the lifespan."""
    from app.roadmap_parser import parse_roadmap

    parsed = parse_roadmap(markdown)
    return await seed_from_parsed(session, parsed)