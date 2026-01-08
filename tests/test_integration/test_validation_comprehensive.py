"""Comprehensive tests for validation functions."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from custom_components.autolock.validation import (
    SCHEMA_BASE,
    SCHEMA_OPTIONS,
    SCHEMA_RETRY,
    SCHEMA_SENSOR,
    SCHEMA_TIMING,
    validate_delay,
    validate_lock_entity,
    validate_schedule,
    validate_sensor_entity,
)


def test_validate_lock_entity_valid():
    """Test validate_lock_entity with valid lock entity."""
    hass = MagicMock()
    state = MagicMock()
    hass.states.get.return_value = state

    with patch(
        "custom_components.autolock.validation.validate_entity_domain",
        return_value=True,
    ):
        assert validate_lock_entity(hass, "lock.test") is True


def test_validate_lock_entity_invalid():
    """Test validate_lock_entity with invalid entity."""
    hass = MagicMock()
    state = MagicMock()
    hass.states.get.return_value = state

    with patch(
        "custom_components.autolock.validation.validate_entity_domain",
        return_value=False,
    ):
        assert validate_lock_entity(hass, "binary_sensor.test") is False


def test_validate_sensor_entity_valid():
    """Test validate_sensor_entity with valid sensor entity."""
    hass = MagicMock()
    state = MagicMock()
    hass.states.get.return_value = state

    with patch(
        "custom_components.autolock.validation.validate_entity_domain",
        return_value=True,
    ):
        assert validate_sensor_entity(hass, "binary_sensor.test") is True


def test_validate_sensor_entity_invalid():
    """Test validate_sensor_entity with invalid entity."""
    hass = MagicMock()
    state = MagicMock()
    hass.states.get.return_value = state

    with patch(
        "custom_components.autolock.validation.validate_entity_domain",
        return_value=False,
    ):
        assert validate_sensor_entity(hass, "lock.test") is False


def test_validate_delay_in_range():
    """Test validate_delay with value in range."""
    assert validate_delay(1, 10, 5) is True
    assert validate_delay(1, 10, 1) is True
    assert validate_delay(1, 10, 10) is True


def test_validate_delay_below_min():
    """Test validate_delay with value below minimum."""
    assert validate_delay(1, 10, 0) is False
    assert validate_delay(5, 10, 4) is False


def test_validate_delay_above_max():
    """Test validate_delay with value above maximum."""
    assert validate_delay(1, 10, 11) is False
    assert validate_delay(1, 10, 20) is False


def test_validate_schedule_valid():
    """Test validate_schedule with valid times."""
    with patch("custom_components.autolock.helpers.schedule.parse_time_string") as mock_parse:
        mock_parse.return_value = None  # No exception
        assert validate_schedule("22:00", "06:00") is True
        assert validate_schedule("09:00", "17:00") is True
        assert mock_parse.call_count == 4  # Called twice per validate_schedule


def test_validate_schedule_invalid_start():
    """Test validate_schedule with invalid start time."""
    with patch("custom_components.autolock.helpers.schedule.parse_time_string") as mock_parse:
        mock_parse.side_effect = ValueError("Invalid time")
        assert validate_schedule("invalid", "06:00") is False


def test_validate_schedule_invalid_end():
    """Test validate_schedule with invalid end time."""
    with patch("custom_components.autolock.helpers.schedule.parse_time_string") as mock_parse:
        # First call succeeds, second fails
        call_count = 0

        def side_effect(*args):
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                raise ValueError("Invalid time")
            return None

        mock_parse.side_effect = side_effect
        assert validate_schedule("22:00", "invalid") is False


def test_schema_base():
    """Test SCHEMA_BASE schema."""
    # Valid data
    valid_data = {"name": "Test Door", "lock_entity": "lock.test"}
    result = SCHEMA_BASE(valid_data)
    assert result["name"] == "Test Door"
    assert result["lock_entity"] == "lock.test"

    # Missing required fields should raise
    with pytest.raises(Exception):  # voluptuous.Invalid
        SCHEMA_BASE({"name": "Test Door"})


def test_schema_sensor():
    """Test SCHEMA_SENSOR schema."""
    # With sensor
    data = {"sensor_entity": "binary_sensor.test"}
    result = SCHEMA_SENSOR(data)
    assert result["sensor_entity"] == "binary_sensor.test"

    # Without sensor (optional)
    data = {}
    result = SCHEMA_SENSOR(data)
    assert "sensor_entity" not in result or result.get("sensor_entity") is None


def test_schema_timing():
    """Test SCHEMA_TIMING schema."""
    # Valid data
    data = {
        "day_delay": 5,
        "night_delay": 2,
        "night_start": "22:00",
        "night_end": "06:00",
    }
    result = SCHEMA_TIMING(data)
    assert result["day_delay"] == 5
    assert result["night_delay"] == 2

    # Test defaults
    data = {
        "night_start": "22:00",
        "night_end": "06:00",
    }
    result = SCHEMA_TIMING(data)
    assert result["day_delay"] == 5  # Default
    assert result["night_delay"] == 2  # Default

    # Invalid range should raise
    with pytest.raises(Exception):  # voluptuous.Invalid
        SCHEMA_TIMING(
            {
                "day_delay": 300,  # Above max
                "night_delay": 2,
                "night_start": "22:00",
                "night_end": "06:00",
            }
        )


def test_schema_retry():
    """Test SCHEMA_RETRY schema."""
    # Valid data
    data = {"retry_count": 3, "retry_delay": 5, "verification_delay": 5}
    result = SCHEMA_RETRY(data)
    assert result["retry_count"] == 3
    assert result["retry_delay"] == 5
    assert result["verification_delay"] == 5

    # Test defaults
    data = {}
    result = SCHEMA_RETRY(data)
    assert result["retry_count"] == 3  # Default
    assert result["retry_delay"] == 5  # Default
    assert result["verification_delay"] == 5  # Default

    # Invalid range should raise
    with pytest.raises(Exception):  # voluptuous.Invalid
        SCHEMA_RETRY({"retry_count": 10, "retry_delay": 5, "verification_delay": 5})


def test_schema_options():
    """Test SCHEMA_OPTIONS schema."""
    # Valid data
    data = {"enable_on_creation": True}
    result = SCHEMA_OPTIONS(data)
    assert result["enable_on_creation"] is True

    # Test default
    data = {}
    result = SCHEMA_OPTIONS(data)
    assert result["enable_on_creation"] is True  # Default
