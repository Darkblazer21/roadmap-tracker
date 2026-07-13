"""Pomodoro state machine, Redis-backed.

A work cycle (25 min) is followed by a short break (5 min); every
``pomo_cycles_per_set`` cycles the short break becomes a long break (15 min);
every ``pomo_cycles_per_marathon`` cycles the break becomes the 2-hour
"marathon" break. Completed work cycles auto-log a ``Session(pomodoro)``
row against the chosen roadmap week and bump ``Week.actual_hours`` so the
``hours_max`` cap alert (M3) fires immediately.

State shape stored in Redis under key ``pomo:state``::

    {
        "phase": "working|short_break|long_break|marathon_break|paused",
        "cycle_count": 0,
        "target_ends_at": 1736000000.0,   # unix epoch seconds; null when paused
        "paused_remaining_sec": 0,         # set only when phase == "paused"
        "week_id": 1,                       # roadmap week this run belongs to
        "run_started_at": 1736000000.0      # for display
    }

Transitions are advanced lazily: every time ``sync_state`` is called (polling),
if ``target_ends_at <= now``, we apply the next transition (and emit a session
for ended work cycles). When the browser was closed for a long time we cap the
catch-up loop to avoid inserting hundreds of stale rows in one tick; the next
poll continues.
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any

import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.session import Session, SessionType
from app.services.hours_aggregator import bump_week_actual_hours

REDIS_KEY = "pomo:state"

# Maximum number of transitions processed in a single ``sync_state`` call.
# Anything more is queued for the next poll to bound fan-out surprises.
_MAX_TRANSITIONS_PER_SYNC = 16


# --- Phase names -------------------------------------------------------- #


class Phase:
    WORKING = "working"
    SHORT_BREAK = "short_break"
    LONG_BREAK = "long_break"
    MARATHON_BREAK = "marathon_break"
    PAUSED = "paused"
    IDLE = "idle"


@dataclass
class PomoState:
    phase: str
    cycle_count: int
    target_ends_at: float | None
    paused_remaining_sec: float
    week_id: int
    run_started_at: float


@dataclass
class PomoView:
    """Serializable view returned to the API."""

    phase: str
    cycle_count: int
    week_id: int | None
    target_ends_at: float | None
    remaining_sec: float
    paused: bool

    # Display helpers for the frontend.
    work_min: int
    short_break_min: int
    long_break_min: int
    marathon_break_min: int
    cycles_per_set: int
    cycles_per_marathon: int

    cycles_in_set: int
    set_count: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# --- Pomo config snapshot ----------------------------------------------- #


@dataclass
class PomoConfig:
    work_sec: int
    short_break_sec: int
    long_break_sec: int
    marathon_break_sec: int
    cycles_per_set: int
    cycles_per_marathon: int

    @classmethod
    def from_minutes(
        cls,
        work_min: int,
        short_break_min: int,
        long_break_min: int,
        marathon_break_min: int,
        cycles_per_set: int,
        cycles_per_marathon: int,
    ) -> "PomoConfig":
        return cls(
            work_sec=work_min * 60,
            short_break_sec=short_break_min * 60,
            long_break_sec=long_break_min * 60,
            marathon_break_sec=marathon_break_min * 60,
            cycles_per_set=cycles_per_set,
            cycles_per_marathon=cycles_per_marathon,
        )


# --- State helpers ------------------------------------------------------ #


def _now() -> float:
    return time.time()


def _encode(state: PomoState) -> str:
    return json.dumps(asdict(state))


def _decode(raw: str) -> PomoState:
    d = json.loads(raw)
    return PomoState(**d)


async def _load(r: redis.Redis) -> PomoState | None:
    raw = await r.get(REDIS_KEY)
    if raw is None:
        return None
    try:
        return _decode(raw)
    except (json.JSONDecodeError, TypeError, ValueError):
        # Corrupt or legacy state in Redis: drop it and fall back to idle
        # instead of 500-ing the request.
        await _clear(r)
        return None


async def _save(r: redis.Redis, state: PomoState) -> None:
    await r.set(REDIS_KEY, _encode(state))


async def _clear(r: redis.Redis) -> None:
    await r.delete(REDIS_KEY)


# --- Public API --------------------------------------------------------- #


async def start_timer(
    r: redis.Redis,
    week_id: int,
    cfg: PomoConfig,
) -> PomoState:
    """Begin a fresh working cycle (cycle_count=0). Replaces any prior state."""
    now = _now()
    state = PomoState(
        phase=Phase.WORKING,
        cycle_count=0,
        target_ends_at=now + cfg.work_sec,
        paused_remaining_sec=0,
        week_id=week_id,
        run_started_at=now,
    )
    await _save(r, state)
    return state


async def stop_timer(r: redis.Redis) -> None:
    """Forget the entire pomodoro run."""
    await _clear(r)


async def pause_timer(r: redis.Redis) -> PomoState | None:
    """Freeze the clock. Records remaining seconds for later resume."""
    state = await _load(r)
    if state is None or state.phase == Phase.PAUSED:
        return state
    remaining = max(0.0, (state.target_ends_at or 0) - _now())
    state.paused_remaining_sec = remaining
    state.phase = Phase.PAUSED
    await _save(r, state)
    return state


async def resume_timer(r: redis.Redis) -> PomoState | None:
    """Restart the clock from where pause left off."""
    state = await _load(r)
    if state is None or state.phase != Phase.PAUSED:
        return state
    state.phase = Phase.WORKING if state.cycle_count == 0 else Phase.SHORT_BREAK
    # The front-end never pauses a break mid-flight in practice (we auto-
    # transition), so if we paused while working we resume working, otherwise
    # fall back to a fresh short break. Simplified.
    state.phase = Phase.WORKING if state.paused_remaining_sec <= 0 else state.phase
    state.target_ends_at = _now() + max(0.1, state.paused_remaining_sec)
    state.paused_remaining_sec = 0
    await _save(r, state)
    return state


async def sync_state(
    r: redis.Redis,
    db: AsyncSession,
    cfg: PomoConfig,
    *,
    log_sessions: bool = True,
) -> PomoView:
    """Apply any pending transitions then return the up-to-date view.

    ``log_sessions`` allows tests to run the FSM without touching the DB.
    """
    state = await _load(r)
    if state is None:
        return _idle_view(cfg)

    # Catch-up loop: apply each due transition. The first WORKING → break
    # transition emits a pomodoro Session for the just-finished cycle.
    transitions = 0
    events: list[dict[str, Any]] = []
    # Never advance a paused timer: its target_ends_at is frozen at the
    # pre-pause deadline, so a passed deadline must not trigger a transition
    # (that would silently un-pause and discard paused_remaining_sec).
    while (
        state.phase != Phase.PAUSED
        and state.target_ends_at is not None
        and state.target_ends_at <= _now()
    ):
        if transitions >= _MAX_TRANSITIONS_PER_SYNC:
            break
        transitions += 1
        events.append(_advance(state, cfg))

    if events and log_sessions:
        # Persist sessions for completed work cycles, bump the week's hours.
        for ev in events:
            if ev["kind"] == "work_completed":
                session = Session(
                    week_id=state.week_id,
                    type=SessionType.pomodoro,
                    duration_sec=ev["duration_sec"],
                    started_at=datetime.fromtimestamp(ev["started_at"], tz=timezone.utc),
                    ended_at=datetime.fromtimestamp(ev["ended_at"], tz=timezone.utc),
                    notes="pomodoro (auto)",
                )
                db.add(session)
                await db.flush()
        await bump_week_actual_hours(db, state.week_id)
        await db.commit()

    if transitions:
        await _save(r, state)

    return _build_view(state, cfg)


# --- FSM transition ---------------------------------------------------- #


def _advance(state: PomoState, cfg: PomoConfig) -> dict[str, Any]:
    """Mutate ``state`` in place; return the event describing what happened."""
    ended_at = state.target_ends_at if state.target_ends_at is not None else _now()
    event: dict[str, Any] = {"kind": "phase_ended", "ended_at": ended_at}

    if state.phase == Phase.WORKING:
        # We just finished a work cycle.
        state.cycle_count += 1
        duration_sec = float(cfg.work_sec)
        event = {
            "kind": "work_completed",
            "duration_sec": duration_sec,
            "started_at": ended_at - duration_sec,
            "ended_at": ended_at,
        }
        # Pick the next break.
        if state.cycle_count % cfg.cycles_per_marathon == 0:
            state.phase = Phase.MARATHON_BREAK
            next_sec = cfg.marathon_break_sec
        elif state.cycle_count % cfg.cycles_per_set == 0:
            state.phase = Phase.LONG_BREAK
            next_sec = cfg.long_break_sec
        else:
            state.phase = Phase.SHORT_BREAK
            next_sec = cfg.short_break_sec
        state.target_ends_at = max(ended_at, _now()) + next_sec
        return event

    # We just finished a break: go back to working.
    state.phase = Phase.WORKING
    state.target_ends_at = max(ended_at, _now()) + cfg.work_sec
    return event


# --- View builders ----------------------------------------------------- #


def _idle_view(cfg: PomoConfig) -> PomoView:
    return PomoView(
        phase=Phase.IDLE,
        cycle_count=0,
        week_id=None,
        target_ends_at=None,
        remaining_sec=0.0,
        paused=False,
        work_min=cfg.work_sec // 60,
        short_break_min=cfg.short_break_sec // 60,
        long_break_min=cfg.long_break_sec // 60,
        marathon_break_min=cfg.marathon_break_sec // 60,
        cycles_per_set=cfg.cycles_per_set,
        cycles_per_marathon=cfg.cycles_per_marathon,
        cycles_in_set=0,
        set_count=0,
    )


def _build_view(state: PomoState, cfg: PomoConfig) -> PomoView:
    paused = state.phase == Phase.PAUSED
    phase_for_remaining = Phase.WORKING if paused else state.phase
    if paused:
        remaining = state.paused_remaining_sec
    elif state.target_ends_at is None:
        remaining = 0.0
    else:
        remaining = max(0.0, state.target_ends_at - _now())

    cycle_count = state.cycle_count
    cycles_per_set = cfg.cycles_per_set
    set_index = cycle_count % cycles_per_set  # 0..3
    set_count = cycle_count // cycles_per_set

    return PomoView(
        phase=phase_for_remaining,
        cycle_count=cycle_count,
        week_id=state.week_id,
        target_ends_at=state.target_ends_at,
        remaining_sec=remaining,
        paused=paused,
        work_min=cfg.work_sec // 60,
        short_break_min=cfg.short_break_sec // 60,
        long_break_min=cfg.long_break_sec // 60,
        marathon_break_min=cfg.marathon_break_sec // 60,
        cycles_per_set=cycles_per_set,
        cycles_per_marathon=cfg.cycles_per_marathon,
        cycles_in_set=set_index if set_index > 0 else (cycles_per_set if cycle_count > 0 else 0),
        set_count=set_count,
    )