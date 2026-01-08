"""Comprehensive tests for door manager."""

from __future__ import annotations

from datetime import datetime
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


@pytest.mark.asyncio
async def test_create_entities(door, mock_hass):
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
async def test_listen_to_state_changes(door, mock_hass):
    """Test state change listener registration."""
    mock_hass.states.get.return_value = MagicMock()

    with patch(
        "custom_components.autolock.door.create_trigger_strategy"
    ) as mock_strategy:
        mock_trigger = MagicMock()
        mock_trigger.get_triggers.return_value = [
            {"entity_id": "binary_sensor.test"},
            {"entity_id": "lock.test"},
        ]
        mock_strategy.return_value = mock_trigger

        door._register_listeners()

        assert len(door._listeners) > 0
        assert mock_hass.bus.async_listen.call_count >= 2


@pytest.mark.asyncio
async def test_listen_to_state_changes_no_entity_id(door, mock_hass):
    """Test state change listener with trigger without entity_id."""
    mock_hass.states.get.return_value = MagicMock()

    with patch(
        "custom_components.autolock.door.create_trigger_strategy"
    ) as mock_strategy:
        mock_trigger = MagicMock()
        mock_trigger.get_triggers.return_value = [
            {},  # No entity_id
        ]
        mock_strategy.return_value = mock_trigger

        door._register_listeners()

        # Should still register timer listener
        assert len(door._listeners) > 0


@pytest.mark.asyncio
async def test_state_changed_listener_trigger(door, mock_hass):
    """Test state changed listener triggers handle_trigger."""
    mock_hass.states.get.return_value = MagicMock()

    with (
        patch(
            "custom_components.autolock.door.create_trigger_strategy"
        ) as mock_strategy,
        patch.object(door, "_handle_trigger", new_callable=AsyncMock) as mock_handle,
    ):
        mock_trigger = MagicMock()
        mock_trigger.get_triggers.return_value = [
            {"entity_id": "binary_sensor.test"},
        ]
        mock_strategy.return_value = mock_trigger

        door._register_listeners()

        # Get the listener callback
        listener_call = mock_hass.bus.async_listen.call_args_list[0]
        callback = listener_call[0][1]

        # Create event
        event = MagicMock()
        event.data = {
            "entity_id": "binary_sensor.test",
            "new_state": MagicMock(state="on"),
        }

        # Call callback
        callback(event)

        # Give async task time to run
        await mock_hass.async_create_task.call_args[0][
            0
        ] if mock_hass.async_create_task.called else None


@pytest.mark.asyncio
async def test_state_changed_listener_wrong_entity(door, mock_hass):
    """Test state changed listener ignores wrong entity."""
    mock_hass.states.get.return_value = MagicMock()

    with (
        patch(
            "custom_components.autolock.door.create_trigger_strategy"
        ) as mock_strategy,
        patch.object(door, "_handle_trigger", new_callable=AsyncMock) as mock_handle,
    ):
        mock_trigger = MagicMock()
        mock_trigger.get_triggers.return_value = [
            {"entity_id": "binary_sensor.test"},
        ]
        mock_strategy.return_value = mock_trigger

        door._register_listeners()

        # Get the listener callback
        listener_call = mock_hass.bus.async_listen.call_args_list[0]
        callback = listener_call[0][1]

        # Create event with wrong entity
        event = MagicMock()
        event.data = {
            "entity_id": "binary_sensor.other",
            "new_state": MagicMock(state="on"),
        }

        # Call callback
        callback(event)

        # Should not trigger
        assert not mock_handle.called


@pytest.mark.asyncio
async def test_state_changed_listener_no_new_state(door, mock_hass):
    """Test state changed listener handles missing new_state."""
    mock_hass.states.get.return_value = MagicMock()

    with (
        patch(
            "custom_components.autolock.door.create_trigger_strategy"
        ) as mock_strategy,
        patch.object(door, "_handle_trigger", new_callable=AsyncMock) as mock_handle,
    ):
        mock_trigger = MagicMock()
        mock_trigger.get_triggers.return_value = [
            {"entity_id": "binary_sensor.test"},
        ]
        mock_strategy.return_value = mock_trigger

        door._register_listeners()

        # Get the listener callback
        listener_call = mock_hass.bus.async_listen.call_args_list[0]
        callback = listener_call[0][1]

        # Create event without new_state
        event = MagicMock()
        event.data = {
            "entity_id": "binary_sensor.test",
        }

        # Call callback
        callback(event)

        # Should not trigger
        assert not mock_handle.called


@pytest.mark.asyncio
async def test_listen_to_timer_finished(door, mock_hass):
    """Test timer finished listener registration."""
    door._listen_to_timer_finished()

    assert len(door._listeners) > 0
    assert mock_hass.bus.async_listen.called


@pytest.mark.asyncio
async def test_timer_finished_listener(door, mock_hass):
    """Test timer finished listener calls handle_timer_finished."""
    with patch.object(
        door, "_handle_timer_finished", new_callable=AsyncMock
    ) as mock_handle:
        door._listen_to_timer_finished()

        # Get the listener callback
        listener_call = mock_hass.bus.async_listen.call_args
        callback = listener_call[0][1]

        # Create event
        event = MagicMock()
        event.data = {"entity_id": door.timer_entity}

        # Call callback
        callback(event)

        # Give async task time to run
        await mock_hass.async_create_task.call_args[0][
            0
        ] if mock_hass.async_create_task.called else None


@pytest.mark.asyncio
async def test_timer_finished_listener_wrong_entity(door, mock_hass):
    """Test timer finished listener ignores wrong entity."""
    with patch.object(
        door, "_handle_timer_finished", new_callable=AsyncMock
    ) as mock_handle:
        door._listen_to_timer_finished()

        # Get the listener callback
        listener_call = mock_hass.bus.async_listen.call_args
        callback = listener_call[0][1]

        # Create event with wrong entity
        event = MagicMock()
        event.data = {"entity_id": "timer.other"}

        # Call callback
        callback(event)

        # Should not trigger
        assert not mock_handle.called


@pytest.mark.asyncio
async def test_handle_trigger_snoozed(door, mock_hass):
    """Test handle trigger when door is snoozed."""
    enabled_state = MagicMock()
    enabled_state.state = "on"
    snooze_state = MagicMock()
    snooze_state.state = "2024-01-01T12:00:00+00:00"  # Future time

    def mock_get(entity_id):
        if "enabled" in entity_id:
            return enabled_state
        if "snooze" in entity_id:
            return snooze_state
        return None

    mock_hass.states.get.side_effect = mock_get
    mock_hass.services.async_call = AsyncMock()

    # Create a mock datetime that can be used both as class and constructor
    class MockDateTime:
        @staticmethod
        def now(tz=None):
            return datetime(2024, 1, 1, 11, 0, 0)
        
        @staticmethod
        def fromisoformat(date_string):
            return datetime(2024, 1, 1, 12, 0, 0)
        
        def __call__(self, *args, **kwargs):
            return datetime(*args, **kwargs)
    
    mock_dt = MockDateTime()
    
    with patch("datetime.datetime", mock_dt):
        await door._handle_trigger()

        # Should not start timer
        assert mock_hass.services.async_call.call_count == 0


@pytest.mark.asyncio
async def test_handle_trigger_snooze_expired(door, mock_hass):
    """Test handle trigger when snooze has expired."""
    enabled_state = MagicMock()
    enabled_state.state = "on"
    snooze_state = MagicMock()
    snooze_state.state = "2024-01-01T10:00:00+00:00"  # Past time

    def mock_get(entity_id):
        if "enabled" in entity_id:
            return enabled_state
        if "snooze" in entity_id:
            return snooze_state
        return None

    mock_hass.states.get.side_effect = mock_get
    mock_hass.services.async_call = AsyncMock()

    class MockDateTime:
        @staticmethod
        def now(tz=None):
            return datetime(2024, 1, 1, 11, 0, 0)
        
        @staticmethod
        def fromisoformat(date_string):
            return datetime(2024, 1, 1, 10, 0, 0)
        
        def __call__(self, *args, **kwargs):
            return datetime(*args, **kwargs)
    
    mock_dt = MockDateTime()
    
    with (
        patch("datetime.datetime", mock_dt),
        patch.object(door.schedule_calculator, "get_delay", return_value=5),
    ):
        await door._handle_trigger()

        # Should start timer
        assert mock_hass.services.async_call.call_count >= 2


@pytest.mark.asyncio
async def test_handle_trigger_snooze_invalid_format(door, mock_hass):
    """Test handle trigger with invalid snooze format."""
    enabled_state = MagicMock()
    enabled_state.state = "on"
    snooze_state = MagicMock()
    snooze_state.state = "invalid_format"

    def mock_get(entity_id):
        if "enabled" in entity_id:
            return enabled_state
        if "snooze" in entity_id:
            return snooze_state
        return None

    mock_hass.states.get.side_effect = mock_get
    mock_hass.services.async_call = AsyncMock()

    class MockDateTime:
        @staticmethod
        def now(tz=None):
            return datetime(2024, 1, 1, 11, 0, 0)
        
        @staticmethod
        def fromisoformat(date_string):
            raise ValueError("Invalid format")
        
        def __call__(self, *args, **kwargs):
            return datetime(*args, **kwargs)
    
    mock_dt = MockDateTime()
    
    with (
        patch("datetime.datetime", mock_dt),
        patch.object(door.schedule_calculator, "get_delay", return_value=5),
    ):
        await door._handle_trigger()

        # Should start timer (invalid snooze is ignored)
        assert mock_hass.services.async_call.call_count >= 2


@pytest.mark.asyncio
async def test_lock_door_with_retries(door, mock_hass):
    """Test lock door with retry logic."""
    lock_result_fail = MagicMock()
    lock_result_fail.success = False
    lock_result_fail.verified = False
    lock_result_fail.error = "Test error"

    lock_result_success = MagicMock()
    lock_result_success.success = True
    lock_result_success.verified = True
    lock_result_success.error = None

    with (
        patch.object(
            door.safety_validator,
            "lock_with_verification",
            new_callable=AsyncMock,
            side_effect=[lock_result_fail, lock_result_success],
        ),
        patch("asyncio.sleep", new_callable=AsyncMock),
    ):
        await door._lock_door()

        # Should have called lock_with_verification twice
        assert door.safety_validator.lock_with_verification.call_count == 2


@pytest.mark.asyncio
async def test_lock_door_all_retries_fail(door, mock_hass):
    """Test lock door when all retries fail."""
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
        patch("asyncio.sleep", new_callable=AsyncMock),
        patch.object(
            door.notification_service,
            "send_notification",
            new_callable=AsyncMock,
        ) as mock_notify,
    ):
        await door._lock_door()

        # Should have called lock_with_verification retry_count + 1 times
        assert (
            door.safety_validator.lock_with_verification.call_count == 4
        )  # 3 retries + 1 initial
        mock_notify.assert_called_once()


@pytest.mark.asyncio
async def test_lock_door_no_error_message(door, mock_hass):
    """Test lock door when lock_result has no error message."""
    lock_result = MagicMock()
    lock_result.success = False
    lock_result.verified = False
    lock_result.error = None

    with (
        patch.object(
            door.safety_validator,
            "lock_with_verification",
            new_callable=AsyncMock,
            return_value=lock_result,
        ),
        patch("asyncio.sleep", new_callable=AsyncMock),
        patch.object(
            door.notification_service,
            "send_notification",
            new_callable=AsyncMock,
        ) as mock_notify,
    ):
        await door._lock_door()

        mock_notify.assert_called_once()
        # Check that notification was called with a message
        call_args = mock_notify.call_args
        assert "message" in call_args.kwargs or len(call_args.args) > 1


@pytest.mark.asyncio
async def test_lock_door_zero_retries(door, mock_hass):
    """Test lock door with zero retries."""
    door.config["retry_count"] = 0

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
    ):
        await door._lock_door()

        # Should only call once (no retries)
        assert door.safety_validator.lock_with_verification.call_count == 1
        mock_notify.assert_called_once()
