"""Tests for entity validation helpers."""

from __future__ import annotations

from unittest.mock import MagicMock

from custom_components.autolock.helpers.entity_validation import (
    get_entity_domain,
    validate_entity_available,
    validate_entity_domain,
    validate_entity_exists,
    validate_entity_state,
)


def test_validate_entity_exists():
    """Test validate_entity_exists."""
    hass = MagicMock()
    hass.states.get.return_value = MagicMock()

    assert validate_entity_exists(hass, "lock.test") is True
    assert validate_entity_exists(hass, "") is False

    hass.states.get.return_value = None
    assert validate_entity_exists(hass, "lock.test") is False


def test_validate_entity_domain():
    """Test validate_entity_domain."""
    hass = MagicMock()
    state = MagicMock()
    hass.states.get.return_value = state

    assert validate_entity_domain(hass, "lock.test", "lock") is True
    assert validate_entity_domain(hass, "lock.test", "binary_sensor") is False

    # Test when entity doesn't exist
    hass.states.get.return_value = None
    assert validate_entity_domain(hass, "lock.test", "lock") is False


def test_validate_entity_state():
    """Test validate_entity_state."""
    hass = MagicMock()
    state = MagicMock()
    state.state = "locked"
    hass.states.get.return_value = state

    assert validate_entity_state(hass, "lock.test", ["locked", "unlocked"]) is True
    assert validate_entity_state(hass, "lock.test", ["unlocked"]) is False

    # Test when entity doesn't exist
    hass.states.get.return_value = None
    assert validate_entity_state(hass, "lock.test", ["locked"]) is False

    # Test when entity exists but state becomes None between calls (line 91)
    # This simulates a race condition where entity exists initially but is removed
    # First call (in validate_entity_exists) returns a state, second call returns None
    state_mock = MagicMock()
    hass.states.get.side_effect = [state_mock, None]
    assert validate_entity_state(hass, "lock.test", ["locked"]) is False
    # Reset to use return_value again
    hass.states.get.side_effect = None
    hass.states.get.return_value = state

    # Test with empty allowed states
    hass.states.get.return_value = state
    assert validate_entity_state(hass, "lock.test", []) is False


def test_validate_entity_available():
    """Test validate_entity_available."""
    hass = MagicMock()
    state = MagicMock()
    state.state = "locked"
    hass.states.get.return_value = state

    assert validate_entity_available(hass, "lock.test") is True

    state.state = "unavailable"
    assert validate_entity_available(hass, "lock.test") is False

    # Test when entity doesn't exist (line 117)
    hass.states.get.return_value = None
    assert validate_entity_available(hass, "lock.test") is False

    # Test when entity exists but state becomes None between calls (line 121)
    # This simulates a race condition where entity exists initially but is removed
    # First call (in validate_entity_exists) returns a state, second call returns None
    state_mock = MagicMock()
    hass.states.get.side_effect = [state_mock, None]
    assert validate_entity_available(hass, "lock.test") is False
    # Reset to use return_value again
    hass.states.get.side_effect = None
    hass.states.get.return_value = state

    # Test with "unknown" state
    state.state = "unknown"
    hass.states.get.return_value = state
    assert validate_entity_available(hass, "lock.test") is False

    # Test with "None" state
    state.state = "None"
    hass.states.get.return_value = state
    assert validate_entity_available(hass, "lock.test") is False


def test_get_entity_domain():
    """Test get_entity_domain."""
    hass = MagicMock()
    state = MagicMock()
    hass.states.get.return_value = state

    assert get_entity_domain(hass, "lock.test") == "lock"
    assert get_entity_domain(hass, "binary_sensor.door") == "binary_sensor"
    assert get_entity_domain(hass, "invalid") is None

    # get_entity_domain doesn't check if entity exists, just extracts from entity_id
    # So it will still return the domain even if entity doesn't exist
    hass.states.get.return_value = None
    assert get_entity_domain(hass, "lock.test") == "lock"
