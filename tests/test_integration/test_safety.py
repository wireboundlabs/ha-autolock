"""Tests for safety validator."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.autolock.const import LOCK_STATE_LOCKED, LOCK_STATE_UNLOCKED
from custom_components.autolock.safety import LockResult, SafetyValidator


class TestCanLock:
    """Tests for can_lock method."""

    @pytest.mark.asyncio
    async def test_success_with_sensor(self, mock_hass):
        """Test with valid conditions including sensor."""
        lock_state = MagicMock()
        lock_state.state = LOCK_STATE_UNLOCKED
        sensor_state = MagicMock()
        sensor_state.state = "on"  # Door closed

        def mock_get(entity_id):
            if "lock" in entity_id:
                return lock_state
            return sensor_state

        mock_hass.states.get.side_effect = mock_get

        validator = SafetyValidator(mock_hass)
        can_lock, reason = validator.can_lock("lock.test", "binary_sensor.test")

        assert can_lock is True
        assert reason is None

    @pytest.mark.asyncio
    async def test_success_no_sensor(self, mock_hass):
        """Test with valid conditions without sensor."""
        lock_state = MagicMock()
        lock_state.state = LOCK_STATE_UNLOCKED
        mock_hass.states.get.return_value = lock_state

        validator = SafetyValidator(mock_hass)
        can_lock, reason = validator.can_lock("lock.test", sensor_entity=None)

        assert can_lock is True
        assert reason is None

    @pytest.mark.asyncio
    async def test_already_locked(self, mock_hass):
        """Test when lock is already locked."""
        lock_state = MagicMock()
        lock_state.state = LOCK_STATE_LOCKED
        mock_hass.states.get.return_value = lock_state

        validator = SafetyValidator(mock_hass)
        can_lock, reason = validator.can_lock("lock.test")

        assert can_lock is False
        assert "already locked" in reason.lower()

    @pytest.mark.asyncio
    async def test_lock_entity_not_found(self, mock_hass):
        """Test when lock entity doesn't exist."""
        mock_hass.states.get.return_value = None

        validator = SafetyValidator(mock_hass)
        can_lock, reason = validator.can_lock("lock.test")

        assert can_lock is False
        assert "not found" in reason.lower()

    @pytest.mark.asyncio
    async def test_door_open(self, mock_hass):
        """Test when door is open."""
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
        can_lock, reason = validator.can_lock("lock.test", "binary_sensor.test")

        assert can_lock is False
        assert "open" in reason.lower()

    @pytest.mark.asyncio
    async def test_sensor_entity_not_found(self, mock_hass):
        """Test when sensor entity doesn't exist."""
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
    @pytest.mark.parametrize(
        "sensor_state",
        ["off", "unavailable", "unknown", ""],
    )
    async def test_invalid_sensor_states(self, mock_hass, sensor_state):
        """Test with various invalid sensor states."""
        lock_state = MagicMock()
        lock_state.state = LOCK_STATE_UNLOCKED
        sensor_state_obj = MagicMock()
        sensor_state_obj.state = sensor_state

        def mock_get(entity_id):
            if "lock" in entity_id:
                return lock_state
            return sensor_state_obj

        mock_hass.states.get.side_effect = mock_get

        validator = SafetyValidator(mock_hass)
        can_lock, reason = validator.can_lock("lock.test", "binary_sensor.test")

        assert can_lock is False


class TestVerifyLockState:
    """Tests for verify_lock_state method."""

    @pytest.mark.asyncio
    async def test_success_immediate(self, mock_hass):
        """Test succeeds immediately."""
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
    async def test_success_after_polling(self, mock_hass):
        """Test succeeds after polling."""
        unlocked_state = MagicMock()
        unlocked_state.state = LOCK_STATE_UNLOCKED
        locked_state = MagicMock()
        locked_state.state = LOCK_STATE_LOCKED

        call_count = 0

        def mock_get(entity_id):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return unlocked_state
            return locked_state

        mock_hass.states.get.side_effect = mock_get

        validator = SafetyValidator(mock_hass)

        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            verified, reason = await validator.verify_lock_state(
                "lock.test", LOCK_STATE_LOCKED, timeout=10.0
            )

            assert verified is True
            assert reason is None
            assert mock_sleep.call_count >= 1

    @pytest.mark.asyncio
    async def test_timeout(self, mock_hass):
        """Test times out correctly."""
        unlocked_state = MagicMock()
        unlocked_state.state = LOCK_STATE_UNLOCKED

        mock_hass.states.get.return_value = unlocked_state

        validator = SafetyValidator(mock_hass)

        with patch("asyncio.sleep", new_callable=AsyncMock):
            verified, reason = await validator.verify_lock_state(
                "lock.test", LOCK_STATE_LOCKED, timeout=0.1
            )

            assert verified is False
            assert "timeout" in reason.lower() or "did not reach" in reason.lower()

    @pytest.mark.asyncio
    async def test_entity_not_found(self, mock_hass):
        """Test when entity doesn't exist."""
        mock_hass.states.get.return_value = None

        validator = SafetyValidator(mock_hass)

        with patch("asyncio.sleep", new_callable=AsyncMock):
            verified, reason = await validator.verify_lock_state(
                "lock.test", LOCK_STATE_LOCKED, timeout=1.0
            )

            assert verified is False
            assert "not found" in reason.lower()

    @pytest.mark.asyncio
    async def test_entity_disappears(self, mock_hass):
        """Test when entity disappears during polling."""
        lock_state = MagicMock()
        lock_state.state = LOCK_STATE_UNLOCKED

        call_count = 0

        def mock_get(entity_id):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return lock_state
            return None  # Entity disappears

        mock_hass.states.get.side_effect = mock_get

        validator = SafetyValidator(mock_hass)

        with patch("asyncio.sleep", new_callable=AsyncMock):
            verified, reason = await validator.verify_lock_state(
                "lock.test", LOCK_STATE_LOCKED, timeout=10.0
            )

            assert verified is False
            assert "not found" in reason.lower()

    @pytest.mark.asyncio
    async def test_different_expected_state(self, mock_hass):
        """Test with different expected state."""
        unlocked_state = MagicMock()
        unlocked_state.state = LOCK_STATE_UNLOCKED

        mock_hass.states.get.return_value = unlocked_state

        validator = SafetyValidator(mock_hass)

        with patch("asyncio.sleep", new_callable=AsyncMock):
            verified, reason = await validator.verify_lock_state(
                "lock.test", LOCK_STATE_UNLOCKED, timeout=0.1
            )

            assert verified is True
            assert reason is None


class TestLockWithVerification:
    """Tests for lock_with_verification method."""

    @pytest.mark.asyncio
    async def test_success(self, mock_hass):
        """Test successful lock with verification."""
        lock_state = MagicMock()
        lock_state.state = LOCK_STATE_UNLOCKED
        locked_state = MagicMock()
        locked_state.state = LOCK_STATE_LOCKED

        call_count = 0

        def mock_get(entity_id):
            nonlocal call_count
            call_count += 1
            if call_count <= 1:
                return lock_state
            return locked_state

        mock_hass.states.get.side_effect = mock_get
        mock_hass.services.async_call = AsyncMock()

        validator = SafetyValidator(mock_hass)

        with patch("asyncio.sleep", new_callable=AsyncMock):
            result = await validator.lock_with_verification(
                "lock.test", verification_delay=0.1
            )

            assert result.success is True
            assert result.verified is True
            assert result.error is None

    @pytest.mark.asyncio
    async def test_success_with_sensor(self, mock_hass):
        """Test successful lock with sensor entity."""
        lock_state = MagicMock()
        lock_state.state = LOCK_STATE_UNLOCKED
        sensor_state = MagicMock()
        sensor_state.state = "on"  # Door closed
        locked_state = MagicMock()
        locked_state.state = LOCK_STATE_LOCKED

        call_count = 0

        def mock_get(entity_id):
            nonlocal call_count
            call_count += 1
            if "lock" in entity_id:
                if call_count <= 2:
                    return lock_state
                return locked_state
            return sensor_state

        mock_hass.states.get.side_effect = mock_get
        mock_hass.services.async_call = AsyncMock()

        validator = SafetyValidator(mock_hass)

        with patch("asyncio.sleep", new_callable=AsyncMock):
            result = await validator.lock_with_verification(
                "lock.test",
                verification_delay=0.1,
                sensor_entity="binary_sensor.test",
            )

            assert result.success is True
            assert result.verified is True

    @pytest.mark.asyncio
    async def test_pre_check_fails_lock_not_found(self, mock_hass):
        """Test when pre-check fails - lock not found."""
        mock_hass.states.get.return_value = None

        validator = SafetyValidator(mock_hass)

        result = await validator.lock_with_verification(
            "lock.test", verification_delay=0.1
        )

        assert result.success is False
        assert result.verified is False
        assert "not found" in result.error.lower()
        mock_hass.services.async_call.assert_not_called()

    @pytest.mark.asyncio
    async def test_pre_check_fails_already_locked(self, mock_hass):
        """Test when pre-check fails - already locked."""
        lock_state = MagicMock()
        lock_state.state = LOCK_STATE_LOCKED
        mock_hass.states.get.return_value = lock_state

        validator = SafetyValidator(mock_hass)

        result = await validator.lock_with_verification(
            "lock.test", verification_delay=0.1
        )

        assert result.success is False
        assert "already locked" in result.error.lower()
        mock_hass.services.async_call.assert_not_called()

    @pytest.mark.asyncio
    async def test_pre_check_fails_door_open(self, mock_hass):
        """Test when pre-check fails - door open."""
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
            "lock.test",
            verification_delay=0.1,
            sensor_entity="binary_sensor.test",
        )

        assert result.success is False
        assert "open" in result.error.lower()
        mock_hass.services.async_call.assert_not_called()

    @pytest.mark.asyncio
    async def test_service_call_exception(self, mock_hass):
        """Test when service call raises exception."""
        lock_state = MagicMock()
        lock_state.state = LOCK_STATE_UNLOCKED
        mock_hass.states.get.return_value = lock_state
        mock_hass.services.async_call = AsyncMock(
            side_effect=Exception("Service error")
        )

        validator = SafetyValidator(mock_hass)

        result = await validator.lock_with_verification(
            "lock.test", verification_delay=0.1
        )

        assert result.success is False
        assert result.verified is False
        assert "error" in result.error.lower() or "failed" in result.error.lower()

    @pytest.mark.asyncio
    async def test_verification_timeout(self, mock_hass):
        """Test when verification times out."""
        unlocked_state = MagicMock()
        unlocked_state.state = LOCK_STATE_UNLOCKED

        mock_hass.states.get.return_value = unlocked_state
        mock_hass.services.async_call = AsyncMock()

        validator = SafetyValidator(mock_hass)

        with patch("asyncio.sleep", new_callable=AsyncMock):
            result = await validator.lock_with_verification(
                "lock.test", verification_delay=0.1
            )

            assert result.success is False
            assert result.verified is False
            assert (
                "verification" in result.error.lower()
                or "did not reach" in result.error.lower()
            )

    @pytest.mark.asyncio
    async def test_zero_verification_delay(self, mock_hass):
        """Test with zero verification delay."""
        lock_state = MagicMock()
        lock_state.state = LOCK_STATE_UNLOCKED
        locked_state = MagicMock()
        locked_state.state = LOCK_STATE_LOCKED

        call_count = 0

        def mock_get(entity_id):
            nonlocal call_count
            call_count += 1
            if call_count <= 1:
                return lock_state
            return locked_state

        mock_hass.states.get.side_effect = mock_get
        mock_hass.services.async_call = AsyncMock()

        validator = SafetyValidator(mock_hass)

        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            await validator.lock_with_verification("lock.test", verification_delay=0.0)

            assert mock_sleep.called


class TestLockResult:
    """Tests for LockResult dataclass."""

    def test_defaults(self):
        """Test default values."""
        result = LockResult(success=True, verified=True)
        assert result.success is True
        assert result.verified is True
        assert result.error is None

    def test_with_error(self):
        """Test with error message."""
        result = LockResult(success=False, verified=False, error="Test error")
        assert result.success is False
        assert result.verified is False
        assert result.error == "Test error"
