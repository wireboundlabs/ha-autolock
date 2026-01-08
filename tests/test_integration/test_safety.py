"""Tests for safety validator."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from custom_components.autolock.const import LOCK_STATE_LOCKED, LOCK_STATE_UNLOCKED
from custom_components.autolock.safety import SafetyValidator


@pytest.mark.asyncio
async def test_can_lock_success(mock_hass):
    """Test can_lock with valid conditions."""
    # Mock lock state
    lock_state = MagicMock()
    lock_state.state = LOCK_STATE_UNLOCKED
    mock_hass.states.get.return_value = lock_state

    validator = SafetyValidator(mock_hass)
    can_lock, reason = validator.can_lock("lock.test", "binary_sensor.test")

    assert can_lock is True
    assert reason is None


@pytest.mark.asyncio
async def test_can_lock_already_locked(mock_hass):
    """Test can_lock when lock is already locked."""
    lock_state = MagicMock()
    lock_state.state = LOCK_STATE_LOCKED
    mock_hass.states.get.return_value = lock_state

    validator = SafetyValidator(mock_hass)
    can_lock, reason = validator.can_lock("lock.test")

    assert can_lock is False
    assert "already locked" in reason.lower()


@pytest.mark.asyncio
async def test_can_lock_door_open(mock_hass):
    """Test can_lock when door is open."""
    lock_state = MagicMock()
    lock_state.state = LOCK_STATE_UNLOCKED
    sensor_state = MagicMock()
    sensor_state.state = "off"  # Door open

    def mock_get(entity_id):
        if "lock" in entity_id:
            return lock_state
        return sensor_state

    mock_hass.states.get = MagicMock(side_effect=mock_get)

    validator = SafetyValidator(mock_hass)
    can_lock, reason = validator.can_lock("lock.test", "binary_sensor.test")

    assert can_lock is False
    assert "open" in reason.lower()

