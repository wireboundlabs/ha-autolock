"""Tests for validation functions and schemas."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
import voluptuous as vol

from custom_components.autolock.const import (
    MAX_DAY_DELAY,
    MAX_NIGHT_DELAY,
    MAX_RETRY_COUNT,
    MAX_RETRY_DELAY,
    MAX_VERIFICATION_DELAY,
    MIN_DAY_DELAY,
    MIN_NIGHT_DELAY,
    MIN_RETRY_COUNT,
    MIN_RETRY_DELAY,
    MIN_VERIFICATION_DELAY,
)
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


class TestValidateLockEntity:
    """Tests for validate_lock_entity."""

    def test_valid_lock_entity(self):
        """Test with valid lock entity."""
        hass = MagicMock()
        state = MagicMock()
        state.state = "locked"
        hass.states.get.return_value = state

        assert validate_lock_entity(hass, "lock.test") is True

    def test_invalid_domain(self):
        """Test with wrong domain."""
        hass = MagicMock()
        state = MagicMock()
        state.state = "on"
        hass.states.get.return_value = state

        assert validate_lock_entity(hass, "binary_sensor.test") is False

    def test_entity_not_found(self):
        """Test when entity doesn't exist."""
        hass = MagicMock()
        hass.states.get.return_value = None

        assert validate_lock_entity(hass, "lock.nonexistent") is False

    def test_empty_string(self):
        """Test with empty string."""
        hass = MagicMock()
        hass.states.get.return_value = None

        assert validate_lock_entity(hass, "") is False

    def test_no_domain_separator(self):
        """Test with entity ID missing domain separator."""
        hass = MagicMock()
        hass.states.get.return_value = None

        assert validate_lock_entity(hass, "invalid") is False


class TestValidateSensorEntity:
    """Tests for validate_sensor_entity."""

    def test_valid_sensor_entity(self):
        """Test with valid sensor entity."""
        hass = MagicMock()
        state = MagicMock()
        state.state = "on"
        hass.states.get.return_value = state

        assert validate_sensor_entity(hass, "binary_sensor.test") is True

    def test_invalid_domain(self):
        """Test with wrong domain."""
        hass = MagicMock()
        state = MagicMock()
        state.state = "locked"
        hass.states.get.return_value = state

        assert validate_sensor_entity(hass, "lock.test") is False

    def test_entity_not_found(self):
        """Test when entity doesn't exist."""
        hass = MagicMock()
        hass.states.get.return_value = None

        assert validate_sensor_entity(hass, "binary_sensor.nonexistent") is False

    def test_empty_string(self):
        """Test with empty string."""
        hass = MagicMock()
        hass.states.get.return_value = None

        assert validate_sensor_entity(hass, "") is False

    def test_no_domain_separator(self):
        """Test with entity ID missing domain separator."""
        hass = MagicMock()
        hass.states.get.return_value = None

        assert validate_sensor_entity(hass, "invalid") is False


class TestValidateDelay:
    """Tests for validate_delay."""

    @pytest.mark.parametrize(
        "min_val,max_val,value,expected",
        [
            (1, 10, 5, True),
            (1, 10, 1, True),  # At minimum
            (1, 10, 10, True),  # At maximum
            (1, 10, 0, False),  # Below minimum
            (1, 10, 11, False),  # Above maximum
            (1, 10, -1, False),  # Negative
            (5, 5, 5, True),  # Zero range at value
            (5, 5, 4, False),  # Zero range below
            (5, 5, 6, False),  # Zero range above
        ],
    )
    def test_validate_delay(self, min_val, max_val, value, expected):
        """Test validate_delay with various values."""
        assert validate_delay(min_val, max_val, value) is expected


class TestValidateSchedule:
    """Tests for validate_schedule."""

    @pytest.mark.parametrize(
        "start,end,expected",
        [
            ("22:00", "06:00", True),
            ("09:00", "17:00", True),
            ("00:00", "23:59", True),
            ("23:59", "00:00", True),  # Midnight crossing
            ("12:00", "12:00", True),  # Same time
            ("invalid", "06:00", False),
            ("22:00", "invalid", False),
            ("25:00", "06:00", False),  # Invalid hour
            ("22:60", "06:00", False),  # Invalid minute
            ("22:00", "25:00", False),
            ("22:00", "06:60", False),
            ("", "06:00", False),  # Empty string
            ("22:00", "", False),
            ("2200", "06:00", False),  # Missing colon
            ("22:00", "0600", False),
            ("ab:cd", "06:00", False),  # Non-numeric
            ("22:00", "ab:cd", False),
        ],
    )
    def test_validate_schedule(self, start, end, expected):
        """Test validate_schedule with various inputs."""
        assert validate_schedule(start, end) is expected


class TestSchemaBase:
    """Tests for SCHEMA_BASE."""

    def test_valid_data(self):
        """Test with valid data."""
        data = {"name": "Test Door", "lock_entity": "lock.test"}
        result = SCHEMA_BASE(data)
        assert result["name"] == "Test Door"
        assert result["lock_entity"] == "lock.test"

    def test_missing_name(self):
        """Test with missing name."""
        with pytest.raises(vol.Invalid):
            SCHEMA_BASE({"lock_entity": "lock.test"})

    def test_missing_lock_entity(self):
        """Test with missing lock_entity."""
        with pytest.raises(vol.Invalid):
            SCHEMA_BASE({"name": "Test Door"})

    def test_empty_name(self):
        """Test with empty name."""
        with pytest.raises(vol.Invalid):
            SCHEMA_BASE({"name": "", "lock_entity": "lock.test"})

    def test_empty_lock_entity(self):
        """Test with empty lock_entity."""
        with pytest.raises(vol.Invalid):
            SCHEMA_BASE({"name": "Test", "lock_entity": ""})


class TestSchemaSensor:
    """Tests for SCHEMA_SENSOR."""

    def test_with_sensor(self):
        """Test with sensor entity."""
        data = {"sensor_entity": "binary_sensor.test"}
        result = SCHEMA_SENSOR(data)
        assert result["sensor_entity"] == "binary_sensor.test"

    def test_without_sensor(self):
        """Test without sensor (optional)."""
        data = {}
        result = SCHEMA_SENSOR(data)
        assert "sensor_entity" not in result or result.get("sensor_entity") is None

    def test_empty_string(self):
        """Test with empty string sensor."""
        with pytest.raises(vol.Invalid):
            SCHEMA_SENSOR({"sensor_entity": ""})


class TestSchemaTiming:
    """Tests for SCHEMA_TIMING."""

    def test_valid_data(self):
        """Test with valid data."""
        data = {
            "day_delay": 5,
            "night_delay": 2,
            "night_start": "22:00",
            "night_end": "06:00",
        }
        result = SCHEMA_TIMING(data)
        assert result["day_delay"] == 5
        assert result["night_delay"] == 2

    def test_defaults(self):
        """Test default values."""
        data = {"night_start": "22:00", "night_end": "06:00"}
        result = SCHEMA_TIMING(data)
        assert result["day_delay"] == 5
        assert result["night_delay"] == 2

    def test_minimum_values(self):
        """Test with minimum allowed values."""
        data = {
            "day_delay": MIN_DAY_DELAY,
            "night_delay": MIN_NIGHT_DELAY,
            "night_start": "22:00",
            "night_end": "06:00",
        }
        result = SCHEMA_TIMING(data)
        assert result["day_delay"] == MIN_DAY_DELAY
        assert result["night_delay"] == MIN_NIGHT_DELAY

    def test_maximum_values(self):
        """Test with maximum allowed values."""
        data = {
            "day_delay": MAX_DAY_DELAY,
            "night_delay": MAX_NIGHT_DELAY,
            "night_start": "22:00",
            "night_end": "06:00",
        }
        result = SCHEMA_TIMING(data)
        assert result["day_delay"] == MAX_DAY_DELAY
        assert result["night_delay"] == MAX_NIGHT_DELAY

    def test_below_minimum(self):
        """Test with value below minimum."""
        with pytest.raises(vol.Invalid):
            SCHEMA_TIMING(
                {
                    "day_delay": MIN_DAY_DELAY - 1,
                    "night_delay": 2,
                    "night_start": "22:00",
                    "night_end": "06:00",
                }
            )

    def test_above_maximum(self):
        """Test with value above maximum."""
        with pytest.raises(vol.Invalid):
            SCHEMA_TIMING(
                {
                    "day_delay": MAX_DAY_DELAY + 1,
                    "night_delay": 2,
                    "night_start": "22:00",
                    "night_end": "06:00",
                }
            )

    def test_string_coercion(self):
        """Test string values are coerced to int."""
        data = {
            "day_delay": "5",
            "night_delay": "2",
            "night_start": "22:00",
            "night_end": "06:00",
        }
        result = SCHEMA_TIMING(data)
        assert isinstance(result["day_delay"], int)
        assert result["day_delay"] == 5


class TestSchemaRetry:
    """Tests for SCHEMA_RETRY."""

    def test_valid_data(self):
        """Test with valid data."""
        data = {"retry_count": 3, "retry_delay": 5, "verification_delay": 5}
        result = SCHEMA_RETRY(data)
        assert result["retry_count"] == 3
        assert result["retry_delay"] == 5
        assert result["verification_delay"] == 5

    def test_defaults(self):
        """Test default values."""
        data = {}
        result = SCHEMA_RETRY(data)
        assert result["retry_count"] == 3
        assert result["retry_delay"] == 5
        assert result["verification_delay"] == 5

    def test_minimum_values(self):
        """Test with minimum allowed values."""
        data = {
            "retry_count": MIN_RETRY_COUNT,
            "retry_delay": MIN_RETRY_DELAY,
            "verification_delay": MIN_VERIFICATION_DELAY,
        }
        result = SCHEMA_RETRY(data)
        assert result["retry_count"] == MIN_RETRY_COUNT
        assert result["retry_delay"] == MIN_RETRY_DELAY
        assert result["verification_delay"] == MIN_VERIFICATION_DELAY

    def test_maximum_values(self):
        """Test with maximum allowed values."""
        data = {
            "retry_count": MAX_RETRY_COUNT,
            "retry_delay": MAX_RETRY_DELAY,
            "verification_delay": MAX_VERIFICATION_DELAY,
        }
        result = SCHEMA_RETRY(data)
        assert result["retry_count"] == MAX_RETRY_COUNT
        assert result["retry_delay"] == MAX_RETRY_DELAY
        assert result["verification_delay"] == MAX_VERIFICATION_DELAY

    def test_below_minimum(self):
        """Test with value below minimum."""
        with pytest.raises(vol.Invalid):
            SCHEMA_RETRY(
                {
                    "retry_count": MIN_RETRY_COUNT - 1,
                    "retry_delay": 5,
                    "verification_delay": 5,
                }
            )

    def test_above_maximum(self):
        """Test with value above maximum."""
        with pytest.raises(vol.Invalid):
            SCHEMA_RETRY(
                {
                    "retry_count": MAX_RETRY_COUNT + 1,
                    "retry_delay": 5,
                    "verification_delay": 5,
                }
            )

    def test_string_coercion(self):
        """Test string values are coerced to int."""
        data = {"retry_count": "3", "retry_delay": "5", "verification_delay": "5"}
        result = SCHEMA_RETRY(data)
        assert isinstance(result["retry_count"], int)
        assert result["retry_count"] == 3


class TestSchemaOptions:
    """Tests for SCHEMA_OPTIONS."""

    def test_valid_true(self):
        """Test with True value."""
        data = {"enable_on_creation": True}
        result = SCHEMA_OPTIONS(data)
        assert result["enable_on_creation"] is True

    def test_valid_false(self):
        """Test with False value."""
        data = {"enable_on_creation": False}
        result = SCHEMA_OPTIONS(data)
        assert result["enable_on_creation"] is False

    def test_default(self):
        """Test default value."""
        data = {}
        result = SCHEMA_OPTIONS(data)
        assert result["enable_on_creation"] is True

    def test_invalid_type(self):
        """Test with invalid type."""
        with pytest.raises(vol.Invalid):
            SCHEMA_OPTIONS({"enable_on_creation": "true"})
