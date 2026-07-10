"""Roadmap markdown parser.

Pure functions that turn the study plan's markdown into structured Python
data. No database access - the seeder in ``app.services.importer`` consumes
the output. Keeping parsing separate makes it trivial to unit-test.

The parser understands the specific shape of ``roadmap.md``:

* Phase headers: ``### Mois 1–1.5 – Python solide (Semaines 1–6)``
* Table rows: ``| 1 | Bases absolues | Python Crash Course ... | Script IMC ... | 12–16 h |``
* Ranges: ``11–12`` expands to weeks 11 and 12; ``55+`` to 55 and 56.
* Hours: ``12–16 h`` → (12.0, 16.0); ``—`` / ``variable`` → (0.0, 0.0).
* Block-quote notes after a table become phase notes; ``⚠️`` lines listing
  "Semaines 19–22 denses" flag those weeks as buffers.
* Duplicate week numbers (e.g. 44-47 appear twice) are merged: the second
  entry's theme / resources / deliverable are appended to the first.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# En-dash (U+2013) is used throughout roadmap.md for ranges and hours.
_EN_DASH = "\u2013"
_EM_DASH = "\u2014"

# Lines starting with ### containing "Mois" mark a phase.
_PHASE_HEADER_RE = re.compile(r"^###\s+(.+)$")
# A markdown table separator row: |---|---|
_TABLE_SEP_RE = re.compile(r"^\|[\s\-:|]+\|\s*$")
# A blockquote line: "> ..."
_BLOCKQUOTE_RE = re.compile(r"^>\s?(.*)$")

# "Semaines 19–22" or "semaines 33–34" inside a note.
_BUFFER_REF_RE = re.compile(r"[Ss]emaines\s+(\d+)\s*[\u2013\-]\s*(\d+)")


@dataclass
class ParsedWeek:
    number: int
    theme: str
    resources: str
    deliverable: str
    hours_min: float
    hours_max: float
    week_label: str  # original cell, e.g. "11–12" or "55+"
    buffer: bool = False


@dataclass
class ParsedPhase:
    key: str
    title: str
    position: int
    subtitle: str | None = None
    notes: str | None = None
    weeks: list[ParsedWeek] = field(default_factory=list)
    buffer_weeks: set[int] = field(default_factory=set)


# --------------------------------------------------------------------------- #
# Pure helpers
# --------------------------------------------------------------------------- #


def _slugify(text: str) -> str:
    """Turn a phase title into a stable ASCII key for idempotent upserts."""
    slug = text.lower()
    slug = re.sub(r"[^\w\s\u2013\-]", "", slug)
    slug = re.sub(r"[\s\u2013\-]+", "-", slug.strip())
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-") or "phase"


def _expand_week_range(cell: str, max_week: int = 56) -> list[int]:
    """Expand a week-cell into individual week numbers.

    Handles: ``1`` → [1], ``11–12`` → [11, 12], ``39–42`` → [39..42],
    ``55+`` → [55, 56].
    """
    cell = cell.strip()
    # "55+" → weeks 55 to max_week
    if cell.endswith("+"):
        start = int(re.sub(r"[^\d]", "", cell))
        return list(range(start, max_week + 1))
    # range with en-dash or hyphen: "11–12", "39-42"
    m = re.match(r"(\d+)\s*[\u2013\-]\s*(\d+)", cell)
    if m:
        return list(range(int(m.group(1)), int(m.group(2)) + 1))
    # single number
    m = re.match(r"(\d+)", cell)
    if m:
        return [int(m.group(1))]
    return []


def _parse_hours(cell: str) -> tuple[float, float]:
    """Parse a hours cell like ``12–16 h`` → (12.0, 16.0).

    Returns (0, 0) for ``—`` / ``variable`` / unparseable cells.
    """
    cell = cell.strip()
    if not cell or cell.startswith(_EM_DASH) or cell == "—" or cell.lower() == "variable":
        return 0.0, 0.0
    m = re.match(r"(\d+(?:\.\d+)?)\s*[\u2013\-]\s*(\d+(?:\.\d+)?)", cell)
    if m:
        return float(m.group(1)), float(m.group(2))
    m = re.match(r"(\d+(?:\.\d+)?)", cell)
    if m:
        v = float(m.group(1))
        return v, v
    return 0.0, 0.0


def _split_table_row(line: str) -> list[str]:
    """Split a markdown table row by ``|`` and strip+clean each cell."""
    parts = line.split("|")
    # drop the leading/trailing empty from the leading/trailing pipe
    if parts and parts[0].strip() == "":
        parts = parts[1:]
    if parts and parts[-1].strip() == "":
        parts = parts[:-1]
    return [p.strip() for p in parts]


# --------------------------------------------------------------------------- #
# Main parser
# --------------------------------------------------------------------------- #


def parse_roadmap(markdown: str) -> list[ParsedPhase]:
    """Parse the full roadmap markdown into a list of phases with weeks.

    Phases without a table (e.g. the closing ``## Conseils finaux``) are
    skipped automatically - only headers containing "Mois" are treated as
    real phases.
    """
    lines = markdown.splitlines()
    phases: list[ParsedPhase] = []
    current: ParsedPhase | None = None
    in_table = False
    position = 0
    seen_weeks: dict[int, ParsedWeek] = {}  # for merging duplicates

    for line in lines:
        # --- Phase header ---
        hdr = _PHASE_HEADER_RE.match(line)
        if hdr:
            title = hdr.group(1).strip()
            # Only accept headers that look like a study phase
            if "Mois" not in title and "mois" not in title:
                current = None
                in_table = False
                continue
            position += 1

            # Extract subtitle "(Semaines 1–6)" if present
            subtitle = None
            sub_m = re.search(r"\(([^)]+)\)", title)
            if sub_m:
                subtitle = sub_m.group(1)

            key = _slugify(title)
            current = ParsedPhase(key=key, title=title, position=position, subtitle=subtitle)
            phases.append(current)
            in_table = False
            continue

        if current is None:
            continue

        # --- Table separator row ---
        if _TABLE_SEP_RE.match(line):
            in_table = True
            continue

        # --- Table data row ---
        if in_table and line.startswith("|") and not line.startswith("|-"):
            cells = _split_table_row(line)
            # Need at least 5 columns: week, theme, resources, deliverable, hours
            if len(cells) < 5:
                continue
            week_label = cells[0]
            theme = cells[1]
            resources = cells[2]
            deliverable = cells[3]
            hours_min, hours_max = _parse_hours(cells[4])

            numbers = _expand_week_range(week_label)
            for num in numbers:
                if num in seen_weeks:
                    # Merge duplicate: append theme/resources/deliverable
                    existing = seen_weeks[num]
                    existing.theme = f"{existing.theme} | {theme}"
                    existing.resources = f"{existing.resources} | {resources}"
                    existing.deliverable = f"{existing.deliverable} | {deliverable}"
                    # Take the max of hours ranges (more demanding)
                    existing.hours_min = max(existing.hours_min, hours_min)
                    existing.hours_max = max(existing.hours_max, hours_max)
                else:
                    w = ParsedWeek(
                        number=num,
                        theme=theme,
                        resources=resources,
                        deliverable=deliverable,
                        hours_min=hours_min,
                        hours_max=hours_max,
                        week_label=week_label,
                    )
                    seen_weeks[num] = w
                    current.weeks.append(w)
            continue

        # --- Blockquote / notes ---
        bq = _BLOCKQUOTE_RE.match(line)
        if bq and not line.startswith("|"):
            note_text = bq.group(1).strip()
            # Split multiline buffered note in lines array
            if current.notes is None:
                current.notes = note_text
            else:
                current.notes += f"\n{note_text}"

            # Detect buffer week references
            for m in _BUFFER_REF_RE.finditer(line):
                lo, hi = int(m.group(1)), int(m.group(2))
                if "idense" in line.lower() or "buffer" in line.lower():
                    for n in range(lo, hi + 1):
                        current.buffer_weeks.add(n)
            continue

        # Non-table, non-header, non-quote line: could be a phase description
        # (e.g. "Objectif : Chat textuel..."). Only capture if before table.
        if line.strip() and not in_table and current:
            # Don't overwrite an existing subtitle-like description
            if current.subtitle and line.strip().startswith(current.subtitle):
                continue
            # Could store as part of notes later if needed; skip for now.
            pass

    # Apply buffer flags to the weeks
    for phase in phases:
        for w in phase.weeks:
            if w.number in phase.buffer_weeks:
                w.buffer = True

    return phases