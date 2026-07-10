"""Unit tests for the roadmap markdown parser (no DB required)."""

from app.roadmap_parser import parse_roadmap


SAMPLE_MARKDOWN = """\
# Titre

## Timeline globale

### Mois 1 – Test (Semaines 1–3)
| Semaine | Thème principal | Ressources | Livrable | Heures |
|---------|-----------------|------------|----------|--------|
| 1       | Bases           | Crash Course chap. 1–5 | Script IMC | 12–16 h |
| 2–3     | Fonctions       | Crash Course chap. 6–8 | Lecture CSV | 14–18 h |

> Semaines 2–3 denses : prévoir un buffer d'1–2 semaines si besoin.

### Mois 2 – Suite (Semaines 4–5)
| Semaine | Focus | Ressources | Livrable | Heures |
|---------|-------|------------|----------|--------|
| 4       | Suite | Doc | API | 18–25 h |
| 5       | —    | —  | —    | —       |
"""


def test_parses_phases():
    phases = parse_roadmap(SAMPLE_MARKDOWN)
    assert len(phases) == 2
    assert "mois-1" in phases[0].key
    assert "test" in phases[0].title.lower()
    assert "mois-2" in phases[1].key


def test_expands_week_ranges():
    phases = parse_roadmap(SAMPLE_MARKDOWN)
    weeks = phases[0].weeks
    numbers = [w.number for w in weeks]
    assert numbers == [1, 2, 3]


def test_parses_hours_range():
    phases = parse_roadmap(SAMPLE_MARKDOWN)
    w1 = phases[0].weeks[0]
    assert w1.hours_min == 12.0
    assert w1.hours_max == 16.0


def test_hours_dash_becomes_zero():
    phases = parse_roadmap(SAMPLE_MARKDOWN)
    w5 = phases[1].weeks[1]
    assert w5.hours_min == 0.0
    assert w5.hours_max == 0.0


def test_buffer_week_detection():
    phases = parse_roadmap(SAMPLE_MARKDOWN)
    w2 = next(w for w in phases[0].weeks if w.number == 2)
    w3 = next(w for w in phases[0].weeks if w.number == 3)
    w1 = next(w for w in phases[0].weeks if w.number == 1)
    assert w2.buffer is True
    assert w3.buffer is True
    assert w1.buffer is False


def test_phase_notes_captured():
    phases = parse_roadmap(SAMPLE_MARKDOWN)
    assert phases[0].notes is not None
    assert "buffer" in phases[0].notes.lower()