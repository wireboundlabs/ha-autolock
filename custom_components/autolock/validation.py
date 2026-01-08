"""Validation functions for AutoLock integration.

Uses helpers for generic validation, adds autolock-specific validation.
"""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.core import HomeAssistant
import voluptuous as vol

from .const import (
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
from .helpers.entity_validation import (
    validate_entity_domain,
    validate_entity_exists,
)

_LOGGER = logging.getLogger(__name__)


def validate_lock_entity(hass: HomeAssistant, entity_id: str) -> bool:
    """Validate that entity exists and is a lock.

    Args:
        hass: Home Assistant instance
        entity_id: Entity ID to validate

    Returns:
        True if valid lock entity, False otherwise
    """
    return validate_entity_domain(hass, entity_id, "lock")


def validate_sensor_entity(hass: HomeAssistant, entity_id: str) -> bool:
    """Validate that entity exists and is a binary_sensor.

    Args:
        hass: Home Assistant instance
        entity_id: Entity ID to validate

    Returns:
        True if valid binary_sensor entity, False otherwise
    """
    return validate_entity_domain(hass, entity_id, "binary_sensor")


def validate_delay(min_value: int, max_value: int, value: int) -> bool:
    """Validate delay value is within range.

    Args:
        min_value: Minimum allowed value
        max_value: Maximum allowed value
        value: Value to validate

    Returns:
        True if value is in range, False otherwise
    """
    return min_value <= value <= max_value


def validate_schedule(start_time: str, end_time: str) -> bool:
    """Validate schedule time strings.

    Args:
        start_time: Start time string (HH:MM format)
        end_time: End time string (HH:MM format)

    Returns:
        True if valid schedule, False otherwise
    """
    try:
        from .helpers.schedule import parse_time_string

        parse_time_string(start_time)
        parse_time_string(end_time)
        return True
    except ValueError:
        return False


# Voluptuous schemas for config flow
SCHEMA_BASE = vol.Schema(
    {
        vol.Required("name"): str,
        vol.Required("lock_entity"): str,
    }
)

SCHEMA_SENSOR = vol.Schema(
    {
        vol.Optional("sensor_entity"): str,
    }
)

SCHEMA_TIMING = vol.Schema(
    {
        vol.Required("day_delay", default=5): vol.All(
            vol.Coerce(int),
            vol.Range(min=MIN_DAY_DELAY, max=MAX_DAY_DELAY),
        ),
        vol.Required("night_delay", default=2): vol.All(
            vol.Coerce(int),
            vol.Range(min=MIN_NIGHT_DELAY, max=MAX_NIGHT_DELAY),
        ),
        vol.Required("night_start"): str,  # HH:MM format
        vol.Required("night_end"): str,  # HH:MM format
    }
)

SCHEMA_RETRY = vol.Schema(
    {
        vol.Required("retry_count", default=3): vol.All(
            vol.Coerce(int),
            vol.Range(min=MIN_RETRY_COUNT, max=MAX_RETRY_COUNT),
        ),
        vol.Required("retry_delay", default=5): vol.All(
            vol.Coerce(int),
            vol.Range(min=MIN_RETRY_DELAY, max=MAX_RETRY_DELAY),
        ),
        vol.Required("verification_delay", default=5): vol.All(
            vol.Coerce(int),
            vol.Range(min=MIN_VERIFICATION_DELAY, max=MAX_VERIFICATION_DELAY),
        ),
    }
)

SCHEMA_OPTIONS = vol.Schema(
    {
        vol.Required("enable_on_creation", default=True): bool,
    }
)

