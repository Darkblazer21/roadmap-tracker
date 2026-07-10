"""Application settings loaded from environment variables (see .env.example).

Centralizes every configurable knob a single-user local app needs:
database / Redis URLs, JWT signing, the seeded login, GitHub token scope,
the roadmap markdown source path, CORS origins and the uvicorn reload flag.
"""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ---------- PostgreSQL ----------
    database_url: str = (
        "postgresql+asyncpg://roadmap:roadmap@db:5432/roadmap_tracker"
    )

    # ---------- Redis ----------
    redis_url: str = "redis://redis:6379/0"

    # ---------- JWT auth ----------
    jwt_secret: str = "change-me-to-a-long-random-string"
    jwt_alg: str = "HS256"
    access_token_expire_min: int = 10080

    # ---------- Seed user (single-user local app) ----------
    seed_username: str = "kingbrems"
    seed_password: str = "change-me"

    # ---------- GitHub sync (M6+) ----------
    github_token: str = ""

    # ---------- Roadmap source ----------
    roadmap_md_path: str = "/app/roadmap.md"

    # ---------- App ----------
    cors_origins: str = (
        "http://localhost:5173,http://localhost:8000"
    )
    reload: int = 1

    # ---------- Pomodoro defaults (minutes) ----------
    # Cycle: 25 work / 5 short break x4, then a 15 min long break;
    # after the 8th completed work cycle a 2-hour "marathon" break.
    pomo_work_min: int = 25
    pomo_short_break_min: int = 5
    pomo_long_break_min: int = 15
    pomo_marathon_break_min: int = 120
    # Work cycles per "set": take the long break instead of a short one
    # every time work cycles % pomo_cycles_per_set == 0.
    pomo_cycles_per_set: int = 4
    # Work cycles per "marathon": take the 2h marathon break instead of
    # the long break every time work cycles % pomo_cycles_per_marathon == 0.
    pomo_cycles_per_marathon: int = 8

    @property
    def cors_origin_list(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.cors_origins.split(",")
            if origin.strip()
        ]

    @property
    def roadmap_path(self) -> Path:
        return Path(self.roadmap_md_path)


settings = Settings()