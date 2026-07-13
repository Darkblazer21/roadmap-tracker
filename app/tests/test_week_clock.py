"""Unit tests for week_clock math (no DB required)."""

from datetime import date

from app.services.week_clock import current_week_number, is_on_track, week_window


def test_current_week_week1():
    assert current_week_number(date(2026, 7, 6), date(2026, 7, 6)) == 1
    assert current_week_number(date(2026, 7, 6), date(2026, 7, 12)) == 1


def test_current_week_week2():
    assert current_week_number(date(2026, 7, 6), date(2026, 7, 13)) == 2


def test_future_start_returns_none():
    assert current_week_number(date(2026, 12, 1), date(2026, 7, 10)) is None


def test_week_window_bounds():
    start, end = week_window(1, date(2026, 7, 6))
    assert start.day == 6
    assert end.day == 13  # exclusive end


def test_week_window_week5():
    start, end = week_window(5, date(2026, 7, 6))
    # Week 5 = start_date + (5-1)*7 = July 6 + 28 days = Aug 3
    assert start.day == 3
    assert start.month == 8


def test_is_on_track_on_time():
    on_track, gap = is_on_track(date(2026, 7, 6), 1, date(2026, 7, 10))
    assert on_track is True
    assert gap == 0


def test_is_on_track_behind():
    on_track, gap = is_on_track(date(2026, 7, 6), 5, date(2026, 7, 20))
    # cal_week at 7/20 with start 7/6 = floor(14/7)+1 = 3; first_incomplete=5
    # gap = 3 - 5 = -2 → abs <= 2 → on_track
    assert gap == -2


def test_is_on_track_far_behind():
    on_track, gap = is_on_track(date(2026, 7, 6), 10, date(2026, 7, 20))
    # cal_week=3, first_incomplete=10 → gap = 3-10 = -7, abs > 2 → not on_track
    assert on_track is False
    assert gap == -7