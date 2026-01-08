"""Tests for schedule calculator."""

from __future__ import annotations

from datetime import datetime, time

import pytest

from custom_components.autolock.helpers.schedule import (
    ScheduleCalculator,
    ScheduleConfig,
    is_time_in_range,
    parse_time_string,
)


def test_parse_time_string():
    """Test parsing time string."""
    result = parse_time_string("22:00")
    assert result == time(22, 0)

    result = parse_time_string("06:30")
    assert result == time(6, 30)

    with pytest.raises(ValueError):
        parse_time_string("invalid")


def test_is_time_in_range_normal():
    """Test time in range for normal range."""
    now = datetime(2024, 1, 1, 12, 0)  # Noon
    start = time(9, 0)
    end = time(17, 0)

    assert is_time_in_range(now, start, end) is True

    # Before range
    now = datetime(2024, 1, 1, 8, 0)
    assert is_time_in_range(now, start, end) is False

    # After range
    now = datetime(2024, 1, 1, 18, 0)
    assert is_time_in_range(now, start, end) is False


def test_is_time_in_range_midnight_crossing():
    """Test time in range for midnight crossing."""
    # Night schedule: 22:00 to 06:00
    start = time(22, 0)
    end = time(6, 0)

    # During night (before midnight)
    now = datetime(2024, 1, 1, 23, 0)
    assert is_time_in_range(now, start, end) is True

    # During night (after midnight)
    now = datetime(2024, 1, 1, 2, 0)
    assert is_time_in_range(now, start, end) is True

    # During day
    now = datetime(2024, 1, 1, 12, 0)
    assert is_time_in_range(now, start, end) is False


def test_schedule_calculator_get_delay():
    """Test schedule calculator delay calculation."""
    calculator = ScheduleCalculator()

    # Day time
    now = datetime(2024, 1, 1, 12, 0)
    schedule = ScheduleConfig.from_strings("22:00", "06:00")
    delay = calculator.get_delay(now, day_delay=5, night_delay=2, schedule=schedule)
    assert delay == 5

    # Night time
    now = datetime(2024, 1, 1, 23, 0)
    delay = calculator.get_delay(now, day_delay=5, night_delay=2, schedule=schedule)
    assert delay == 2

    # No schedule
    delay = calculator.get_delay(now, day_delay=5, night_delay=2, schedule=None)
    assert delay == 5


def test_schedule_config_from_strings_exception():
    """Test ScheduleConfig.from_strings with invalid time."""
    with pytest.raises(ValueError):
        ScheduleConfig.from_strings("invalid", "06:00")


def test_schedule_calculator_is_time_in_range():
    """Test ScheduleCalculator.is_time_in_range static method."""
    calculator = ScheduleCalculator()
    now = datetime(2024, 1, 1, 12, 0)
    start = time(9, 0)
    end = time(17, 0)

    assert calculator.is_time_in_range(now, start, end) is True


def test_schedule_calculator_parse_time_string():
    """Test ScheduleCalculator.parse_time_string static method (line 53)."""
    calculator = ScheduleCalculator()
    result = calculator.parse_time_string("22:00")
    assert result == time(22, 0)

    result = calculator.parse_time_string("06:30")
    assert result == time(6, 30)

    with pytest.raises(ValueError):
        calculator.parse_time_string("invalid")