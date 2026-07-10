# Roadmap Tracker

A **standalone, offline** local app that tracks a 52–56 week backend/cloud
engineering study roadmap ("Parcours 12–14 mois → Backend / Cloud Engineer
Remote"). It tells you whether you are on time, how many hours you actually
logged, drafts your Sunday recap for you, and verifies your GitHub commit
activity landed within each week's window.

Built with the **same stack the roadmap teaches**: Python, FastAPI, PostgreSQL,
Docker, Redis, and a minimal React frontend.

## Features

- **Bilingual UI (EN/FR)** — a language toggle in the header switches between
  English and French instantly; your preference is saved in localStorage.
- **Start-date anchored timeline** — set one date; the app computes the current
  week and flags weeks ahead/behind the plan.
- **Pomodoro engine** — 25/5 ×4 → 15 min break, then a 2-hour break after the
  8th completed cycle. Completed pomodoros automatically count toward the
  week's hours and cap alerts.
- **Day-to-day tracking** — daily logging of topic, blockers, and what you
  learned, rolled up into per-week hour totals vs. the planned min/max ranges.
- **Hours dashboards** — per-day / per-week / per-phase aggregations with
  range bars and cap alerts (green = in range, yellow = under-min, red =
  over-cap burnout warning).
- **Sunday recap generator** — drafts the 3-line weekly recap (succès /
  blocages / prochaine étape) from the week's data; one click to copy as
  Markdown for Notion/README.
- **GitHub on-time check** — syncs commits from your tracked repos and shows
  ✅ / ⚠️ / ❌ per week (≥1 commit inside the week's 7-day window).
- **Deviation alerts** — banner when you fall more than 2 weeks behind, with
  buffer-week awareness for the dense phases (19–22, 33–34).
- **Reset all progress** — wipe sessions, daily logs, recaps, and week
  statuses from the Settings page without touching your config (start date,
  pomodoro settings, tracked repos).
- **Roadmap importer** — parses `roadmap.md` into the database on first boot
  (idempotent by week number).
- **Thin JWT auth** — single seeded user (local-only).
- **Resilient navigation** — ErrorBoundary catches page render errors and
  shows a recovery UI; route-level code splitting with React.lazy keeps the
  initial bundle small; fetch timeout prevents hung-requests from freezing
  the UI.

## Stack

| Layer      | Technology                                            |
| ---------- | ----------------------------------------------------- |
| Backend    | FastAPI, Uvicorn, SQLAlchemy 2.0 (async), Alembic    |
| Database   | PostgreSQL 16                                         |
| Cache/Timer| Redis 7 (pomodoro state machine)                     |
| Scheduler  | APScheduler (nightly GitHub sync)                    |
| Auth       | python-jose (JWT) + passlib (bcrypt)                 |
| HTTP       | httpx (GitHub REST API)                              |
| Frontend   | React 18 + Vite + TypeScript + Tailwind + Recharts   |
| i18n       | Custom context-based (en/fr), localStorage-persisted |
| Containers | Docker + Docker Compose                               |

## Architecture

```
Browser (localhost:5173)
  React + Vite + Tailwind + TanStack Query
  • React.lazy code-splitting (per-page chunks)
  • ErrorBoundary + AbortController timeout
  • i18n provider (EN/FR toggle)
        │  REST + JSON (proxied to :8000 in dev)
        ▼
FastAPI (localhost:8000)
  • Pydantic v2 schemas
  • SQLAlchemy 2.0 async ORM
  • APScheduler (nightly GitHub sync at 03:00)
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
#    - set GITHUB_TOKEN to a personal access token (public_repo scope)

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

### First-time setup in the app

1. **Log in** with the `SEED_USERNAME` / `SEED_PASSWORD` from your `.env`.
2. Go to **Settings** → set your **start date** (the date your roadmap begins).
3. Add your **GitHub repositories** to track (format: `owner/repo`).
4. Go to **Dashboard** — you should see the current week highlighted.
5. Go to **GitHub** → click **Sync now** to fetch your commits.

## Pages

| Page | Route | Description |
|------|-------|-------------|
| Dashboard | `/` | Current week, hours summary, deviation banner, progress bar, quick actions |
| Weeks | `/weeks` | All 7 phases with 56 weeks in an accordion; status dots, hours, buffer flags |
| Week detail | `/weeks/:n` | Single week: theme, resources, deliverable, hours bar, log session form |
| Daily log | `/daily-log` | Today's study log (topic, learned, blockers) + history per week |
| Sunday recap | `/recap` | Generate a 3-line draft from the week's data, edit, copy as Markdown |
| GitHub check | `/github` | Per-week commit verdict matrix (✅/⚠️/❌) + sync button |
| Settings | `/settings` | Start date, pomodoro config, tracked repos, weekly targets, reset progress |

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/auth/login` | Get JWT token |
| `GET` | `/api/auth/me` | Current user |
| `GET` | `/api/weeks` | All phases with weeks |
| `GET` | `/api/weeks/:n` | Single week details |
| `PATCH` | `/api/weeks/:n` | Update week status/hours/recap (auth) |
| `GET`/`PATCH` | `/api/settings` | Read/update settings (auth) |
| `POST` | `/api/settings/reset` | Reset all progress (auth) |
| `GET` | `/api/settings/current-week` | Current calendar week (auth) |
| `POST` | `/api/sessions` | Log a study session (auth) |
| `GET` | `/api/sessions?week_id=n` | List sessions for a week (auth) |
| `GET` | `/api/sessions/aggregate?week_id=n` | Hours aggregate + cap alerts (auth) |
| `DELETE` | `/api/sessions/:id` | Delete a session (auth) |
| `POST`/`GET` | `/api/pomo/start\|pause\|resume\|stop\|state` | Pomodoro timer control (auth) |
| `POST` | `/api/daily-logs` | Create/update daily log (auth) |
| `GET` | `/api/daily-logs?week_id=n` | List daily logs for a week (auth) |
| `POST` | `/api/recaps/:n/generate` | Generate recap draft (auth) |
| `PUT` | `/api/recaps/:n` | Save edited recap (auth) |
| `POST` | `/api/github/sync` | Trigger GitHub sync (auth) |
| `GET` | `/api/github/verdicts` | Per-week commit verdict matrix (auth) |
| `GET` | `/api/github/events` | Cached GitHub events (auth) |
| `GET` | `/api/dashboard` | Dashboard summary (auth) |
| `GET` | `/api/export/all.json` | Full export as JSON (auth) |
| `GET` | `/api/export/sessions.csv` | Sessions as CSV (auth) |
| `GET` | `/health` | Health check (no auth) |
| `GET` | `/docs` | Swagger UI (no auth) |

## Project structure

```
roadmap-manager/
├── roadmap.md              # the study roadmap (seed source for the importer)
├── docker-compose.yml      # api + db + redis
├── Dockerfile              # multi-stage Python image
├── requirements.txt
├── pytest.ini              # pytest config (asyncio_mode=auto)
├── alembic/                # DB migrations (7 revisions)
├── app/
│   ├── main.py             # FastAPI app, lifespan, /health
│   ├── config.py           # pydantic-settings (from .env)
│   ├── db.py               # async engine + session + Base
│   ├── roadmap_parser.py   # markdown table parser -> ParsedPhase/Week
│   ├── models/             # Phase, Week, User, AppSettings, Session,
│   │                       #   DailyLog, Recap, GithubEvent, GithubSyncState
│   ├── schemas/            # Pydantic v2 request/response per entity
│   ├── routers/            # auth, weeks, sessions, pomodoro, daily_logs,
│   │                       #   recaps, github, dashboard, export, settings
│   ├── services/           # security, week_clock, hours_aggregator,
│   │                       #   pomodoro_machine, recap_generator,
│   │                       #   github_sync, week_verdict, deviation,
│   │                       #   scheduler, redis_client, importer
│   └── tests/              # 21 tests (parser, week_clock, API, JWT)
└── frontend/
    ├── package.json
    ├── vite.config.ts      # dev proxy to :8000
    └── src/
        ├── main.tsx        # I18nProvider + QueryClientProvider
        ├── App.tsx         # AuthGate, Layout, lazy routes, ErrorBoundary
        ├── lib/
        │   ├── api.ts      # authFetch (AbortController timeout), types
        │   └── i18n.tsx    # translations (en/fr), useT() hook
        ├── components/
        │   ├── PomodoroWidget.tsx   # ring timer in header
        │   ├── LogSessionForm.tsx    # manual session entry
        │   ├── WeekHoursBar.tsx      # Recharts bar vs plan range
        │   ├── LanguageToggle.tsx   # EN/FR switch button
        │   ├── ErrorBoundary.tsx    # crash recovery UI
        │   └── PageFallback.tsx      # animated loading spinner
        └── pages/
            ├── DashboardPage.tsx
            ├── WeeksListPage.tsx
            ├── WeekDetailPage.tsx
            ├── DailyLogPage.tsx
            ├── SundayRecapPage.tsx
            ├── GithubVerdictsPage.tsx
            ├── SettingsPage.tsx
            └── LoginPage.tsx
```

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

# Type-check frontend
cd frontend && npm run lint

# Production build
cd frontend && npm run build
```

## Testing

```bash
# Create the test database (one-time)
docker compose exec db psql -U roadmap -d roadmap_tracker -c \
  "CREATE DATABASE roadmap_tracker_test;"

# Run all 21 tests
docker compose exec api pytest -v
```

Tests cover:
- Roadmap markdown parser (phases, hour ranges, buffer weeks, range expansion)
- Week clock math (current week, week window, on-track computation)
- API routes (login, JWT protection, week patching, auth flow)

## Tech notes

### Navigation stability

The app uses three layers to prevent page-transition freezes:

1. **ErrorBoundary** — wraps every route; catches render crashes and shows a
   recovery UI with "Back to dashboard" / "Reload" buttons.
2. **AbortController timeout** — every fetch in `authFetch` has a 12-second
   timeout, so a hung backend never freezes the UI. React-query's cancellation
   signal is chained in, so stale queries abort on route changes.
3. **Safe data guards** — all pages check `if (!data)` before rendering, so
   a brief undefined state (during cache invalidation) shows the loading
   spinner instead of crashing.

### Code splitting

Each page is a separate JS chunk via `React.lazy` + `Suspense`. The main
bundle is ~254 KB (gzip 81 KB); Recharts only loads when a page with charts
is visited. A fade-in animation (0.18s) plays on every route change.

### i18n

A custom context-based system with ~200 strings in both `en` and `fr`.
Language preference is stored in `localStorage` under `rt_lang`, defaults to
French. The `useT()` hook returns a `t(key, params?)` function that
interpolates `{name}` placeholders.

## License

MIT