"""Tests for validation functions."""

from __future__ import annotations

from unittest.mock import MagicMock

from custom_components.autolock.validation import (
    validate_delay,
    validate_lock_entity,
    validate_schedule,
    validate_sensor_entity,
)


def test_validate_lock_entity():
    """Test validate_lock_entity."""
    hass = MagicMock()
    state = MagicMock()
    hass.states.get.return_value = state

    assert validate_lock_entity(hass, "lock.test") is True
    assert validate_lock_entity(hass, "binary_sensor.test") is False


def test_validate_sensor_entity():
    """Test validate_sensor_entity."""
    hass = MagicMock()
    state = MagicMock()
    hass.states.get.return_value = state

    assert validate_sensor_entity(hass, "binary_sensor.test") is True
    assert validate_sensor_entity(hass, "lock.test") is False


def test_validate_delay():
    """Test validate_delay."""
    assert validate_delay(1, 10, 5) is True
    assert validate_delay(1, 10, 0) is False
    assert validate_delay(1, 10, 11) is False


def test_validate_schedule():
    """Test validate_schedule."""
    assert validate_schedule("22:00", "06:00") is True
    assert validate_schedule("09:00", "17:00") is True
    assert validate_schedule("invalid", "06:00") is False
    assert validate_schedule("22:00", "invalid") is False
