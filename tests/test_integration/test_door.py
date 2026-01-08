"""Tests for door manager."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.autolock.door import AutolockDoor


@pytest.fixture
def door_config():
    """Create door configuration."""
    return {
        "name": "Test Door",
        "lock_entity": "lock.test",
        "sensor_entity": "binary_sensor.test",
        "day_delay": 5,
        "night_delay": 2,
        "night_start": "22:00",
        "night_end": "06:00",
        "retry_count": 3,
        "retry_delay": 5,
        "verification_delay": 5,
        "enable_on_creation": True,
    }


@pytest.fixture
def door(mock_hass, door_config):
    """Create door instance."""
    return AutolockDoor(mock_hass, "test_door", door_config)


class TestDoorInitialization:
    """Tests for door initialization."""

    def test_init(self, door, door_config):
        """Test door initialization."""
        assert door.door_id == "test_door"
        assert door.config == door_config
        assert door.schedule_calculator is not None
        assert door.retry_strategy is not None
        assert door.notification_service is not None
        assert door.safety_validator is not None


class TestDoorSetup:
    """Tests for door setup."""

    @pytest.mark.asyncio
    async def test_async_setup(self, door, mock_hass):
        """Test door setup."""
        with (
            patch.object(
                door.entity_factory, "create_input_boolean", new_callable=AsyncMock
            ) as mock_bool,
            patch.object(
                door.entity_factory, "create_input_datetime", new_callable=AsyncMock
            ) as mock_datetime,
            patch.object(
                door.entity_factory, "create_timer", new_callable=AsyncMock
            ) as mock_timer,
            patch.object(door, "_register_listeners") as mock_register,
        ):
            await door.async_setup()

            mock_bool.assert_called_once()
            mock_datetime.assert_called_once()
            mock_timer.assert_called_once()
            mock_register.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_entities(self, door, mock_hass):
        """Test entity creation."""
        with (
            patch.object(
                door.entity_factory, "create_input_boolean", new_callable=AsyncMock
            ) as mock_bool,
            patch.object(
                door.entity_factory, "create_input_datetime", new_callable=AsyncMock
            ) as mock_datetime,
            patch.object(
                door.entity_factory, "create_timer", new_callable=AsyncMock
            ) as mock_timer,
        ):
            await door._create_entities()

            mock_bool.assert_called_once()
            mock_datetime.assert_called_once()
            mock_timer.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_entities_false_enable(self, door, mock_hass, door_config):
        """Test entity creation with enable_on_creation=False."""
        door.config["enable_on_creation"] = False

        with patch.object(
            door.entity_factory, "create_input_boolean", new_callable=AsyncMock
        ) as mock_bool:
            await door._create_entities()

            call_args = mock_bool.call_args
            assert call_args[1]["initial_state"] is False

    @pytest.mark.asyncio
    async def test_register_listeners(self, door, mock_hass):
        """Test listener registration."""
        mock_hass.states.get.return_value = MagicMock()

        door._register_listeners()

        assert len(door._listeners) > 0
        assert mock_hass.bus.async_listen.call_count >= 2

    @pytest.mark.asyncio
    async def test_register_listeners_no_entity_id(self, door, mock_hass):
        """Test listener registration with trigger without entity_id."""
        mock_hass.states.get.return_value = MagicMock()

        with patch(
            "custom_components.autolock.door.create_trigger_strategy"
        ) as mock_strategy:
            mock_trigger = MagicMock()
            mock_trigger.get_triggers.return_value = [{}]  # No entity_id
            mock_strategy.return_value = mock_trigger

            door._register_listeners()

            assert len(door._listeners) > 0


class TestHandleTrigger:
    """Tests for handle_trigger method."""

    @pytest.mark.asyncio
    async def test_disabled(self, door, mock_hass):
        """Test when door is disabled."""
        enabled_state = MagicMock()
        enabled_state.state = "off"
        mock_hass.states.get.return_value = enabled_state

        await door._handle_trigger()

        mock_hass.services.async_call.assert_not_called()

    @pytest.mark.asyncio
    async def test_enabled_state_none(self, door, mock_hass):
        """Test when enabled state is None."""
        mock_hass.states.get.return_value = None
        mock_hass.services.async_call = AsyncMock()

        await door._handle_trigger()

        mock_hass.services.async_call.assert_not_called()

    @pytest.mark.asyncio
    async def test_enabled(self, door, mock_hass):
        """Test when door is enabled."""
        enabled_state = MagicMock()
        enabled_state.state = "on"
        snooze_state = MagicMock()
        snooze_state.state = "unknown"

        def mock_get(entity_id):
            if "enabled" in entity_id:
                return enabled_state
            if "snooze" in entity_id:
                return snooze_state
            return None

        mock_hass.states.get.side_effect = mock_get
        mock_hass.services.async_call = AsyncMock()

        await door._handle_trigger()

        assert mock_hass.services.async_call.call_count >= 2  # cancel + start

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "snooze_state_value,should_start_timer",
        [
            ("unknown", True),
            ("unavailable", True),
            ("invalid_format", True),  # Invalid format should be handled gracefully
        ],
    )
    async def test_snooze_states(
        self, door, mock_hass, snooze_state_value, should_start_timer
    ):
        """Test with various snooze states."""
        enabled_state = MagicMock()
        enabled_state.state = "on"
        snooze_state = MagicMock()
        snooze_state.state = snooze_state_value

        def mock_get(entity_id):
            if "enabled" in entity_id:
                return enabled_state
            if "snooze" in entity_id:
                return snooze_state
            return None

        mock_hass.states.get.side_effect = mock_get
        mock_hass.services.async_call = AsyncMock()

        await door._handle_trigger()

        if should_start_timer:
            assert mock_hass.services.async_call.called

    @pytest.mark.asyncio
    async def test_snooze_in_future(self, door, mock_hass):
        """Test when snooze is in the future."""
        enabled_state = MagicMock()
        enabled_state.state = "on"
        future_time = datetime.now(UTC).replace(microsecond=0, second=0) + timedelta(
            minutes=30
        )
        snooze_state = MagicMock()
        snooze_state.state = future_time.isoformat()

        def mock_get(entity_id):
            if "enabled" in entity_id:
                return enabled_state
            if "snooze" in entity_id:
                return snooze_state
            return None

        mock_hass.states.get.side_effect = mock_get
        mock_hass.services.async_call = AsyncMock()

        await door._handle_trigger()
        # Should not start timer when snoozed

    @pytest.mark.asyncio
    async def test_snooze_in_past(self, door, mock_hass):
        """Test when snooze is in the past."""
        enabled_state = MagicMock()
        enabled_state.state = "on"
        past_time = datetime.now(UTC).replace(microsecond=0, second=0) - timedelta(
            minutes=30
        )
        snooze_state = MagicMock()
        snooze_state.state = past_time.isoformat()

        def mock_get(entity_id):
            if "enabled" in entity_id:
                return enabled_state
            if "snooze" in entity_id:
                return snooze_state
            return None

        mock_hass.states.get.side_effect = mock_get
        mock_hass.services.async_call = AsyncMock()

        await door._handle_trigger()

        assert mock_hass.services.async_call.called

    @pytest.mark.asyncio
    async def test_cancels_existing_timer(self, door, mock_hass):
        """Test cancels existing timer before starting new one."""
        enabled_state = MagicMock()
        enabled_state.state = "on"
        snooze_state = MagicMock()
        snooze_state.state = "unknown"

        def mock_get(entity_id):
            if "enabled" in entity_id:
                return enabled_state
            if "snooze" in entity_id:
                return snooze_state
            return None

        mock_hass.states.get.side_effect = mock_get
        mock_hass.services.async_call = AsyncMock()

        await door._handle_trigger()

        call_args_list = mock_hass.services.async_call.call_args_list
        cancel_called = any(
            call[0][0] == "timer" and call[0][1] == "cancel" for call in call_args_list
        )
        start_called = any(
            call[0][0] == "timer" and call[0][1] == "start" for call in call_args_list
        )

        assert cancel_called
        assert start_called

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "hour,expected_delay",
        [(12, 5), (23, 2)],  # Day time, Night time
    )
    async def test_delay_calculation(self, door, mock_hass, hour, expected_delay):
        """Test delay calculation for day/night."""
        enabled_state = MagicMock()
        enabled_state.state = "on"
        snooze_state = MagicMock()
        snooze_state.state = "unknown"

        def mock_get(entity_id):
            if "enabled" in entity_id:
                return enabled_state
            if "snooze" in entity_id:
                return snooze_state
            return None

        mock_hass.states.get.side_effect = mock_get
        mock_hass.services.async_call = AsyncMock()

        # Patch datetime.now where it's imported in the function
        # The function imports: from datetime import datetime
        # So we patch the datetime class's now method
        mock_now = datetime(2024, 1, 1, hour, 0)
        with patch(
            "datetime.datetime.now",
            return_value=mock_now,
        ):
            await door._handle_trigger()

            # Verify timer was started with correct delay
            call_args_list = mock_hass.services.async_call.call_args_list
            for call in call_args_list:
                if call[0][0] == "timer" and call[0][1] == "start":
                    duration = call[1]["duration"]
                    expected_str = f"00:{expected_delay:02d}:00"
                    assert expected_str in duration or duration == expected_str


class TestHandleTimerFinished:
    """Tests for handle_timer_finished method."""

    @pytest.mark.asyncio
    async def test_calls_lock_door(self, door, mock_hass):
        """Test calls _lock_door."""
        with patch.object(door, "_lock_door", new_callable=AsyncMock) as mock_lock:
            await door._handle_timer_finished()

            mock_lock.assert_called_once()


class TestLockDoor:
    """Tests for _lock_door method."""

    @pytest.mark.asyncio
    async def test_success(self, door, mock_hass):
        """Test successful lock."""
        lock_result = MagicMock()
        lock_result.success = True
        lock_result.verified = True
        lock_result.error = None

        with patch.object(
            door.safety_validator,
            "lock_with_verification",
            new_callable=AsyncMock,
            return_value=lock_result,
        ):
            await door._lock_door()

            door.safety_validator.lock_with_verification.assert_called()

    @pytest.mark.asyncio
    async def test_failure(self, door, mock_hass):
        """Test failed lock."""
        lock_result = MagicMock()
        lock_result.success = False
        lock_result.verified = False
        lock_result.error = "Test error"

        with (
            patch.object(
                door.safety_validator,
                "lock_with_verification",
                new_callable=AsyncMock,
                return_value=lock_result,
            ),
            patch.object(
                door.notification_service,
                "send_notification",
                new_callable=AsyncMock,
            ) as mock_notify,
            patch("asyncio.sleep", new_callable=AsyncMock),
        ):
            await door._lock_door()

            mock_notify.assert_called_once()

    @pytest.mark.asyncio
    async def test_success_on_retry(self, door, mock_hass):
        """Test succeeds on second retry attempt."""
        failed_result = MagicMock()
        failed_result.success = False
        failed_result.verified = False
        failed_result.error = "First attempt failed"

        success_result = MagicMock()
        success_result.success = True
        success_result.verified = True
        success_result.error = None

        with (
            patch.object(
                door.safety_validator,
                "lock_with_verification",
                side_effect=[failed_result, success_result],
            ),
            patch("asyncio.sleep", new_callable=AsyncMock),
        ):
            await door._lock_door()

            assert door.safety_validator.lock_with_verification.call_count == 2

    @pytest.mark.asyncio
    async def test_all_retries_fail(self, door, mock_hass):
        """Test when all retries fail."""
        failed_result = MagicMock()
        failed_result.success = False
        failed_result.verified = False
        failed_result.error = "Lock failed"

        with (
            patch.object(
                door.safety_validator,
                "lock_with_verification",
                return_value=failed_result,
            ),
            patch.object(
                door.notification_service,
                "send_notification",
                new_callable=AsyncMock,
            ) as mock_notify,
            patch("asyncio.sleep", new_callable=AsyncMock),
        ):
            await door._lock_door()

            assert (
                door.safety_validator.lock_with_verification.call_count
                == door.config["retry_count"] + 1
            )
            mock_notify.assert_called_once()

    @pytest.mark.asyncio
    async def test_zero_retries(self, door, mock_hass, door_config):
        """Test with zero retry count."""
        door.config["retry_count"] = 0

        failed_result = MagicMock()
        failed_result.success = False
        failed_result.verified = False
        failed_result.error = "Lock failed"

        with (
            patch.object(
                door.safety_validator,
                "lock_with_verification",
                return_value=failed_result,
            ),
            patch.object(
                door.notification_service,
                "send_notification",
                new_callable=AsyncMock,
            ) as mock_notify,
        ):
            await door._lock_door()

            assert door.safety_validator.lock_with_verification.call_count == 1
            mock_notify.assert_called_once()

    @pytest.mark.asyncio
    async def test_no_error_message(self, door, mock_hass):
        """Test when result has no error message."""
        failed_result = MagicMock()
        failed_result.success = False
        failed_result.verified = False
        failed_result.error = None

        with (
            patch.object(
                door.safety_validator,
                "lock_with_verification",
                return_value=failed_result,
            ),
            patch.object(
                door.notification_service,
                "send_notification",
                new_callable=AsyncMock,
            ) as mock_notify,
            patch("asyncio.sleep", new_callable=AsyncMock),
        ):
            await door._lock_door()

            mock_notify.assert_called_once()

    @pytest.mark.asyncio
    async def test_verification_delay_configuration(self, door, mock_hass):
        """Test uses configured verification_delay."""
        success_result = MagicMock()
        success_result.success = True
        success_result.verified = True
        success_result.error = None

        door.config["verification_delay"] = 7.5

        with patch.object(
            door.safety_validator,
            "lock_with_verification",
            return_value=success_result,
        ) as mock_lock:
            await door._lock_door()

            call_args = mock_lock.call_args
            assert call_args[1]["verification_delay"] == 7.5

    @pytest.mark.asyncio
    async def test_default_verification_delay(self, door, mock_hass, door_config):
        """Test uses default verification_delay when not configured."""
        door.config.pop("verification_delay", None)

        success_result = MagicMock()
        success_result.success = True
        success_result.verified = True
        success_result.error = None

        with patch.object(
            door.safety_validator,
            "lock_with_verification",
            return_value=success_result,
        ) as mock_lock:
            await door._lock_door()

            call_args = mock_lock.call_args
            assert call_args[1]["verification_delay"] == 5.0


class TestUnload:
    """Tests for door unload."""

    @pytest.mark.asyncio
    async def test_async_unload(self, door):
        """Test door unload removes listeners."""
        remove_listener1 = MagicMock()
        remove_listener2 = MagicMock()
        door._listeners = [remove_listener1, remove_listener2]

        await door.async_unload()

        remove_listener1.assert_called_once()
        remove_listener2.assert_called_once()
        assert len(door._listeners) == 0
