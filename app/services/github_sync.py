"""GitHub sync service.

Pulls the most recent commits from each tracked repo (settings.tracked_repos)
via the GitHub REST API and persists them to ``github_events``. Sync is
idempotent: commits are deduplicated by the unique (repo, sha) index, so
re-running is safe and effectively incremental in practice (GitHub returns
newest-first; commits already in our table are skipped without writes).

The token is read from ``settings.github_token`` (env var ``GITHUB_TOKEN``).
A ``GithubSyncState`` row tracks the last sync time per repo for UI display.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.github_event import GithubEvent, GithubEventKind, GithubSyncState

logger = logging.getLogger(__name__)

GITHUB_API = "https://api.github.com"
# Cap how many pages we walk per sync to bound runtime. 100 commits per page
# => up to ~500 recent commits per repo, plenty for personal study repos.
MAX_PAGES_PER_REPO = 5


def _parse_link_header(link: str) -> str | None:
    if not link:
        return None
    for part in link.split(","):
        section = part.strip()
        if 'rel="next"' in section:
            start = section.find("<") + 1
            end = section.find(">", start)
            if start > 0 and end > start:
                return section[start:end]
    return None


def _to_event(repo: str, item: dict) -> GithubEvent | None:
    """Convert a GitHub commit JSON object to a ``GithubEvent`` row."""
    try:
        sha = item["sha"]
        commit = item.get("commit", {})
        message = (commit.get("message", "") or "")[:2000]
        author_block = commit.get("author", {}) or {}
        author = (item.get("author") or {}).get("login") or author_block.get("name")
        authored_iso = author_block.get("date")
        if not authored_iso:
            return None
        authored_at = datetime.fromisoformat(authored_iso.replace("Z", "+00:00"))
    except (KeyError, ValueError):
        return None
    return GithubEvent(
        repo=repo,
        sha=sha,
        kind=GithubEventKind.commit,
        message=message,
        author=author,
        authored_at=authored_at,
    )


async def sync_repo(
    db: AsyncSession,
    client: httpx.AsyncClient,
    repo: str,
) -> int:
    """Sync one repo. Returns the count of *new* commits persisted."""
    repo = repo.strip()
    if not repo or "/" not in repo:
        logger.warning("Skipping malformed repo: %r", repo)
        return 0

    cursor = (
        await db.execute(
            select(GithubSyncState).where(GithubSyncState.repo == repo)
        )
    ).scalar_one_or_none()
    if cursor is None:
        cursor = GithubSyncState(repo=repo)
        db.add(cursor)
        await db.flush()

    existing_shas = set(
        (
            await db.execute(
                select(GithubEvent.sha).where(GithubEvent.repo == repo)
            )
        ).scalars().all()
    )

    new_count = 0
    next_url: str | None = None
    params: dict[str, str] = {"per_page": "100"}

    for page_index in range(MAX_PAGES_PER_REPO):
        if next_url:
            res = await client.get(next_url)
            res.raise_for_status()
            items = res.json()
            next_url = _parse_link_header(res.headers.get("link", ""))
        else:
            url = f"{GITHUB_API}/repos/{repo}/commits"
            res = await client.get(url, params=params)
            if res.status_code == 409:
                # Empty repository.
                break
            res.raise_for_status()
            items = res.json()
            next_url = _parse_link_header(res.headers.get("link", ""))

        if not items:
            break

        for item in items:
            ev = _to_event(repo, item)
            if ev is None or ev.sha in existing_shas:
                continue
            existing_shas.add(ev.sha)
            db.add(ev)
            new_count += 1

        await db.commit()
        if not next_url:
            break

    cursor.last_synced_at = datetime.now(timezone.utc)
    await db.commit()

    logger.info("github_sync: repo=%s new=%d total=%d", repo, new_count, len(existing_shas))
    return new_count


async def sync_all(db: AsyncSession, repos: list[str]) -> dict[str, int]:
    """Sync every tracked repo. Returns {repo: new_count} (-1 on error)."""
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if settings.github_token:
        headers["Authorization"] = f"Bearer {settings.github_token}"

    results: dict[str, int] = {}
    async with httpx.AsyncClient(headers=headers, timeout=30) as client:
        for repo in repos:
            try:
                results[repo] = await sync_repo(db, client, repo)
            except Exception as exc:  # noqa: BLE001
                logger.error("github_sync error on %s: %s", repo, exc)
                results[repo] = -1
    return results