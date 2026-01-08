"""Comprehensive tests for safety validator."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.autolock.const import LOCK_STATE_LOCKED, LOCK_STATE_UNLOCKED
from custom_components.autolock.safety import LockResult, SafetyValidator


@pytest.mark.asyncio
async def test_can_lock_missing_lock_entity(mock_hass):
    """Test can_lock when lock entity doesn't exist."""
    mock_hass.states.get.return_value = None

    validator = SafetyValidator(mock_hass)
    can_lock, reason = validator.can_lock("lock.test")

    assert can_lock is False
    assert "not found" in reason.lower()


@pytest.mark.asyncio
async def test_can_lock_no_sensor(mock_hass):
    """Test can_lock without sensor entity."""
    lock_state = MagicMock()
    lock_state.state = LOCK_STATE_UNLOCKED
    mock_hass.states.get.return_value = lock_state

    validator = SafetyValidator(mock_hass)
    can_lock, reason = validator.can_lock("lock.test", sensor_entity=None)

    assert can_lock is True
    assert reason is None


@pytest.mark.asyncio
async def test_can_lock_missing_sensor_entity(mock_hass):
    """Test can_lock when sensor entity doesn't exist."""
    lock_state = MagicMock()
    lock_state.state = LOCK_STATE_UNLOCKED

    def mock_get(entity_id):
        if "lock" in entity_id:
            return lock_state
        return None  # Sensor not found

    mock_hass.states.get.side_effect = mock_get

    validator = SafetyValidator(mock_hass)
    can_lock, reason = validator.can_lock("lock.test", "binary_sensor.test")

    assert can_lock is False
    assert "not found" in reason.lower()


@pytest.mark.asyncio
async def test_verify_lock_state_missing_entity(mock_hass):
    """Test verify_lock_state when entity doesn't exist."""
    mock_hass.states.get.return_value = None

    validator = SafetyValidator(mock_hass)

    with patch("asyncio.sleep", new_callable=AsyncMock):
        verified, reason = await validator.verify_lock_state(
            "lock.test", LOCK_STATE_LOCKED, timeout=1.0
        )

        assert verified is False
        assert "not found" in reason.lower()


@pytest.mark.asyncio
async def test_verify_lock_state_success_immediate(mock_hass):
    """Test verify_lock_state succeeds immediately."""
    lock_state = MagicMock()
    lock_state.state = LOCK_STATE_LOCKED

    mock_hass.states.get.return_value = lock_state

    validator = SafetyValidator(mock_hass)

    with patch("asyncio.sleep", new_callable=AsyncMock):
        verified, reason = await validator.verify_lock_state(
            "lock.test", LOCK_STATE_LOCKED, timeout=1.0
        )

        assert verified is True
        assert reason is None


@pytest.mark.asyncio
async def test_verify_lock_state_success_after_poll(mock_hass):
    """Test verify_lock_state succeeds after polling."""
    unlocked_state = MagicMock()
    unlocked_state.state = LOCK_STATE_UNLOCKED
    locked_state = MagicMock()
    locked_state.state = LOCK_STATE_LOCKED

    state_calls = [unlocked_state, unlocked_state, locked_state]

    def mock_get(entity_id):
        return state_calls.pop(0) if state_calls else locked_state

    mock_hass.states.get.side_effect = mock_get

    validator = SafetyValidator(mock_hass)

    with (
        patch("asyncio.sleep", new_callable=AsyncMock),
        patch("asyncio.get_event_loop") as mock_loop,
    ):
        # Mock time progression
        time_values = [0.0, 0.1, 0.2, 0.3]
        mock_loop.return_value.time.side_effect = iter(time_values)

        verified, reason = await validator.verify_lock_state(
            "lock.test", LOCK_STATE_LOCKED, timeout=1.0
        )

        assert verified is True
        assert reason is None


@pytest.mark.asyncio
async def test_verify_lock_state_timeout(mock_hass):
    """Test verify_lock_state times out."""
    lock_state = MagicMock()
    lock_state.state = LOCK_STATE_UNLOCKED  # Never reaches locked

    mock_hass.states.get.return_value = lock_state

    validator = SafetyValidator(mock_hass)

    with (
        patch("asyncio.sleep", new_callable=AsyncMock),
        patch("asyncio.get_event_loop") as mock_loop,
    ):
        # Mock time to simulate timeout
        mock_loop.return_value.time.side_effect = [0.0, 2.0]  # Start, then timeout

        verified, reason = await validator.verify_lock_state(
            "lock.test", LOCK_STATE_LOCKED, timeout=1.0
        )

        assert verified is False
        assert "timeout" in reason.lower() or "did not reach" in reason.lower()


@pytest.mark.asyncio
async def test_lock_with_verification_pre_check_fails_door_open(mock_hass):
    """Test lock_with_verification when door is open."""
    lock_state = MagicMock()
    lock_state.state = LOCK_STATE_UNLOCKED
    sensor_state = MagicMock()
    sensor_state.state = "off"  # Door open

    def mock_get(entity_id):
        if "lock" in entity_id:
            return lock_state
        return sensor_state

    mock_hass.states.get.side_effect = mock_get

    validator = SafetyValidator(mock_hass)

    result = await validator.lock_with_verification(
        "lock.test", sensor_entity="binary_sensor.test"
    )

    assert result.success is False
    assert result.verified is False
    assert "open" in result.error.lower()


@pytest.mark.asyncio
async def test_lock_with_verification_service_call_success(mock_hass):
    """Test lock_with_verification with successful service call."""
    unlocked_state = MagicMock()
    unlocked_state.state = LOCK_STATE_UNLOCKED
    locked_state = MagicMock()
    locked_state.state = LOCK_STATE_LOCKED

    state_calls = [unlocked_state, locked_state]

    def mock_get(entity_id):
        return state_calls.pop(0) if state_calls else locked_state

    mock_hass.states.get.side_effect = mock_get
    mock_hass.services.async_call = AsyncMock()

    validator = SafetyValidator(mock_hass)

    with (
        patch("asyncio.sleep", new_callable=AsyncMock),
        patch("asyncio.get_event_loop") as mock_loop,
    ):
        mock_loop.return_value.time.side_effect = [0.0, 0.1]

        result = await validator.lock_with_verification(
            "lock.test", verification_delay=0.1
        )

        assert result.success is True
        assert result.verified is True
        assert result.error is None
        mock_hass.services.async_call.assert_called_once()


@pytest.mark.asyncio
async def test_lock_with_verification_with_sensor(mock_hass):
    """Test lock_with_verification with sensor entity."""
    unlocked_state = MagicMock()
    unlocked_state.state = LOCK_STATE_UNLOCKED
    locked_state = MagicMock()
    locked_state.state = LOCK_STATE_LOCKED
    sensor_state = MagicMock()
    sensor_state.state = "on"  # Door closed

    state_calls = [unlocked_state, sensor_state, locked_state]

    def mock_get(entity_id):
        if "sensor" in entity_id:
            return sensor_state
        return state_calls.pop(0) if state_calls else locked_state

    mock_hass.states.get.side_effect = mock_get
    mock_hass.services.async_call = AsyncMock()

    validator = SafetyValidator(mock_hass)

    with (
        patch("asyncio.sleep", new_callable=AsyncMock),
        patch("asyncio.get_event_loop") as mock_loop,
    ):
        mock_loop.return_value.time.side_effect = [0.0, 0.1]

        result = await validator.lock_with_verification(
            "lock.test",
            verification_delay=0.1,
            sensor_entity="binary_sensor.test",
        )

        assert result.success is True
        assert result.verified is True


@pytest.mark.asyncio
async def test_lock_result_dataclass():
    """Test LockResult dataclass."""
    result = LockResult(success=True, verified=True, error=None)
    assert result.success is True
    assert result.verified is True
    assert result.error is None

    result2 = LockResult(success=False, verified=False, error="Test error")
    assert result2.success is False
    assert result2.verified is False
    assert result2.error == "Test error"
