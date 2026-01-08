"""Extended tests for safety validator."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.autolock.const import LOCK_STATE_LOCKED, LOCK_STATE_UNLOCKED
from custom_components.autolock.safety import SafetyValidator


@pytest.mark.asyncio
async def test_verify_lock_state_success(mock_hass):
    """Test verify_lock_state with success."""
    lock_state = MagicMock()
    lock_state.state = LOCK_STATE_LOCKED

    def mock_get(entity_id):
        return lock_state

    mock_hass.states.get.side_effect = mock_get

    validator = SafetyValidator(mock_hass)

    with patch("asyncio.sleep", new_callable=AsyncMock):
        verified, reason = await validator.verify_lock_state(
            "lock.test", LOCK_STATE_LOCKED, timeout=1.0
        )

        assert verified is True
        assert reason is None


@pytest.mark.asyncio
async def test_verify_lock_state_timeout(mock_hass):
    """Test verify_lock_state with timeout."""
    lock_state = MagicMock()
    lock_state.state = LOCK_STATE_UNLOCKED  # Never reaches locked

    def mock_get(entity_id):
        return lock_state

    mock_hass.states.get.side_effect = mock_get

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
async def test_lock_with_verification_success(mock_hass):
    """Test lock_with_verification with success."""
    lock_state = MagicMock()
    lock_state.state = LOCK_STATE_UNLOCKED
    locked_state = MagicMock()
    locked_state.state = LOCK_STATE_LOCKED

    state_calls = [lock_state, locked_state]

    def mock_get(entity_id):
        return state_calls.pop(0) if state_calls else locked_state

    mock_hass.states.get.side_effect = mock_get
    mock_hass.services.async_call = AsyncMock()

    validator = SafetyValidator(mock_hass)

    with (
        patch("asyncio.sleep", new_callable=AsyncMock),
        patch("asyncio.get_event_loop") as mock_loop,
    ):
        mock_loop.return_value.time.side_effect = [0.0, 0.1]  # Quick verification

        result = await validator.lock_with_verification(
            "lock.test", verification_delay=0.1
        )

        assert result.success is True
        assert result.verified is True
        assert result.error is None


@pytest.mark.asyncio
async def test_lock_with_verification_pre_check_fails(mock_hass):
    """Test lock_with_verification when pre-check fails."""
    lock_state = MagicMock()
    lock_state.state = LOCK_STATE_LOCKED  # Already locked

    mock_hass.states.get.return_value = lock_state

    validator = SafetyValidator(mock_hass)

    result = await validator.lock_with_verification("lock.test")

    assert result.success is False
    assert result.verified is False
    assert "already locked" in result.error.lower()


@pytest.mark.asyncio
async def test_lock_with_verification_service_fails(mock_hass):
    """Test lock_with_verification when service call fails."""
    lock_state = MagicMock()
    lock_state.state = LOCK_STATE_UNLOCKED

    mock_hass.states.get.return_value = lock_state
    mock_hass.services.async_call = AsyncMock(side_effect=Exception("Service error"))

    validator = SafetyValidator(mock_hass)

    result = await validator.lock_with_verification("lock.test", verification_delay=0.0)

    assert result.success is False
    assert result.verified is False
    assert "Service error" in result.error


@pytest.mark.asyncio
async def test_lock_with_verification_verification_fails(mock_hass):
    """Test lock_with_verification when verification fails."""
    lock_state = MagicMock()
    lock_state.state = LOCK_STATE_UNLOCKED  # Never locks

    mock_hass.states.get.return_value = lock_state
    mock_hass.services.async_call = AsyncMock()

    validator = SafetyValidator(mock_hass)

    with (
        patch("asyncio.sleep", new_callable=AsyncMock),
        patch("asyncio.get_event_loop") as mock_loop,
    ):
        # Mock time to simulate timeout
        # First call: start_time (0.0)
        # Second call: elapsed check (6.0, which is > timeout of 5.0)
        time_mock = MagicMock()
        time_mock.side_effect = [0.0, 6.0]  # Start, then timeout
        mock_loop.return_value.time = time_mock

        result = await validator.lock_with_verification(
            "lock.test", verification_delay=0.1
        )

        assert result.success is False
        assert result.verified is False
        assert "verification failed" in result.error.lower()
