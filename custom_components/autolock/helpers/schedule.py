"""Generic day/night schedule calculator for Home Assistant integrations.

This module provides reusable schedule logic that can be used by any integration
needing day/night schedules (lights, thermostats, locks, etc.).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time
from typing import Final

# Time format for parsing
TIME_FORMAT: Final = "%H:%M"


@dataclass
class ScheduleConfig:
    """Configuration for day/night schedule."""

    start_time: time
    end_time: time

    @classmethod
    def from_strings(cls, start_str: str, end_str: str) -> ScheduleConfig:
        """Create schedule config from time strings (HH:MM format)."""
        return cls(
            start_time=parse_time_string(start_str),
            end_time=parse_time_string(end_str),
        )


class ScheduleCalculator:
    """Generic calculator for day/night schedule logic.

    Handles schedule calculations including midnight crossing edge cases.
    Pure functions - no side effects, no HA dependencies.
    """

    @staticmethod
    def parse_time_string(time_str: str) -> time:
        """Parse time string in HH:MM format to time object.

        Args:
            time_str: Time string in HH:MM format (e.g., "22:00")

        Returns:
            time object

        Raises:
            ValueError: If time string is invalid
        """
        return parse_time_string(time_str)

    @staticmethod
    def is_time_in_range(now: datetime, start_time: time, end_time: time) -> bool:
        """Check if current time is within the specified range.

        Handles midnight crossing (e.g., 22:00-06:00).

        Args:
            now: Current datetime
            start_time: Start time
            end_time: End time

        Returns:
            True if current time is in range, False otherwise
        """
        return is_time_in_range(now, start_time, end_time)

    @staticmethod
    def is_night_time(now: datetime, schedule: ScheduleConfig) -> bool:
        """Determine if current time is in night schedule.

        Args:
            now: Current datetime
            schedule: Schedule configuration

        Returns:
            True if in night schedule, False otherwise
        """
        return is_time_in_range(now, schedule.start_time, schedule.end_time)

    @staticmethod
    def get_delay(
        now: datetime,
        day_delay: int,
        night_delay: int,
        schedule: ScheduleConfig | None,
    ) -> int:
        """Get appropriate delay based on current time and schedule.

        Args:
            now: Current datetime
            day_delay: Delay in minutes for day time
            night_delay: Delay in minutes for night time
            schedule: Schedule configuration (None means always use day_delay)

        Returns:
            Delay in minutes
        """
        if schedule is None:
            return day_delay

        if ScheduleCalculator.is_night_time(now, schedule):
            return night_delay
        return day_delay


def parse_time_string(time_str: str) -> time:
    """Parse time string in HH:MM format to time object.

    Args:
        time_str: Time string in HH:MM format (e.g., "22:00")

    Returns:
        time object

    Raises:
        ValueError: If time string is invalid
    """
    try:
        return datetime.strptime(time_str, TIME_FORMAT).time()
    except ValueError as err:
        raise ValueError(f"Invalid time format: {time_str}. Expected HH:MM") from err


def is_time_in_range(now: datetime, start_time: time, end_time: time) -> bool:
    """Check if current time is within the specified range.

    Handles midnight crossing (e.g., 22:00-06:00 means 22:00 to 06:00 next day).

    Args:
        now: Current datetime
        start_time: Start time
        end_time: End time

    Returns:
        True if current time is in range, False otherwise
    """
    current_time = now.time()

    # Handle midnight crossing (e.g., 22:00-06:00)
    if start_time > end_time:
        # Range crosses midnight
        return current_time >= start_time or current_time <= end_time

    # Normal range (e.g., 09:00-17:00)
    return start_time <= current_time <= end_time

