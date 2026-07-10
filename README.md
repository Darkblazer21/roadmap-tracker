# Roadmap Tracker

A **standalone, offline** local app that tracks a 52-56 week backend/cloud
engineering study roadmap ("Parcours 12-14 mois → Backend / Cloud Engineer
Remote"). It tells you whether you are on time, how many hours you actually
logged, drafts your Sunday recap for you, and verifies your GitHub commit
activity landed within each week's window.

Built with the **same stack the roadmap teaches**: Python, FastAPI, PostgreSQL,
Docker, Redis, and a minimal React frontend.

## Features

- **Start-date anchored timeline** — set one date; the app computes the current
  week and flags weeks ahead/behind the plan.
- **Pomodoro engine** — 25/5 ×4 → 15 min break, then a 2-hour break after the
  8th completed cycle. Completed pomodoros automatically count toward the
  week's hours and cap alerts.
- **Day-to-day tracking** — daily logging of topic, blockers, and what you
  learned, rolled up into per-week hour totals vs. the planned min/max ranges.
- **Hours dashboards** — per-day / per-week / per-phase aggregations with a
  GitHub-style activity heatmap and range bars.
- **Sunday recap generator** — drafts the 3-line weekly recap (succès /
  blocages / prochaine étape) from the week's data; one click to copy.
- **GitHub on-time check** — syncs commits from your tracked repos and shows
  ✅ / ⚠️ / ❌ per week (≥1 commit inside the week's 7-day window).
- **Deviation alerts** — banner when you fall more than 2 weeks behind, with
  buffer-week awareness for the dense phases (19-22, 33-34).
- **Roadmap importer** — parses `roadmap.md` into the database on first boot
  (idempotent by week number).
- **Thin JWT auth** — single seeded user (local-only).

## Stack

| Layer      | Technology                                            |
| ---------- | ----------------------------------------------------- |
| Backend    | FastAPI, Uvicorn, SQLAlchemy 2.0 (async), Alembic    |
| Database   | PostgreSQL 16                                         |
| Cache/TB   | Redis 7 (pomodoro state, rate limiting)              |
| Scheduler  | APScheduler (nightly GitHub sync)                    |
| Auth       | python-jose (JWT) + passlib (bcrypt)                 |
| Frontend   | React 18 + Vite + TypeScript + Tailwind + Recharts   |
| Containers | Docker + Docker Compose                               |

## Architecture

```
Browser (localhost:5173)
  React + Vite + Tailwind + TanStack Query
        │  REST + JSON (proxied to :8000 in dev)
        ▼
FastAPI (localhost:8000)
  • Pydantic v2 schemas
  • SQLAlchemy 2.0 async ORM
  • APScheduler (pomodoro timers, weekly cron)
  • httpx (GitHub API)
        │                       │
        ▼                       ▼
  PostgreSQL 16            Redis 7
  (persistent)             (pomodoro state)
```

All three services run via `docker compose up`.

## Getting started

### Prerequisites

- Docker 24+ and Docker Compose v2+
- Node.js 20+ and npm (for the frontend dev server)
- Git

### Setup

```bash
# 1. Copy the environment template and edit secrets
cp .env.example .env
#    - set JWT_SECRET to a long random string
#    - set SEED_PASSWORD to your login password

# 2. Start the backend stack (api + db + redis)
docker compose up -d --build

# 3. Install + run the frontend dev server
cd frontend
npm install
npm run dev
```

Then open:

- Frontend: http://localhost:5173
- API docs (Swagger UI): http://localhost:8000/docs
- Health check: http://localhost:8000/health

### Verify the stack

```bash
docker compose ps          # all three services should be healthy
curl http://localhost:8000/health   # {"status":"ok"}
```

## Project structure

```
roadmap-manager/
├── roadmap.md              # the study roadmap (seed source for the importer)
├── docker-compose.yml      # api + db + redis
├── Dockerfile              # multi-stage Python image
├── requirements.txt
├── alembic/                # DB migrations
├── app/
│   ├── main.py             # FastAPI app, lifespan, /health
│   ├── config.py           # pydantic-settings (from .env)
│   ├── db.py               # async engine + session + Base
│   ├── models/             # SQLAlchemy ORM models (added from M1)
│   ├── schemas/             # Pydantic request/response (added from M1)
│   ├── routers/             # API routers (weeks, sessions, pomodoro, ...)
│   └── services/            # business logic (github_sync, recap_generator, ...)
└── frontend/
    ├── package.json
    ├── vite.config.ts
    └── src/
        ├── main.tsx
        ├── App.tsx
        └── index.css
```

## Roadmap of the tracker itself

| Milestone | Scope                                                              | Status |
| --------- | ------------------------------------------------------------------ | ------ |
| M0        | Scaffold & infra (compose, Dockerfile, app shell, frontend)       | ✅      |
| M1        | Roadmap importer + weeks read API + read-only week list UI         | ☐      |
| M2        | Settings (start date), week clock, JWT auth, settings UI           | ☐      |
| M3        | Sessions model, manual focus log, per-week hours bar              | ☐      |
| M4        | Pomodoro engine (Redis state machine) + timer widget               | ☐      |
| M5        | Daily log + Sunday recap generator                                 | ☐      |
| M6        | GitHub sync + per-week commit verdict + night cron               | ☐      |
| M7        | Deviation alerts, buffer awareness, heatmap calendar, export      | ☐      |
| M8        | Tests (pytest ≥12), polish, docs, screenshots                     | ☐      |

## Development

```bash
# Backend: source mounts + --reload are enabled when RELOAD=1 in .env
docker compose up -d

# Tail logs
docker compose logs -f api

# Run a migration
docker compose exec api alembic revision --autogenerate -m "describe change"
docker compose exec api alembic upgrade head

# Frontend hot reload
cd frontend && npm run dev
```

## Testing

```bash
# Backend tests (added in M8)
docker compose exec api pytest -v
```

## License

MIT