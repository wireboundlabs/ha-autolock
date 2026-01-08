"""Tests for door manager."""

from __future__ import annotations

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
async def test_door_init(door, door_config):
    """Test door initialization."""
    assert door.door_id == "test_door"
    assert door.config == door_config
    assert door.schedule_calculator is not None
    assert door.retry_strategy is not None
    assert door.notification_service is not None
    assert door.safety_validator is not None


@pytest.mark.asyncio
async def test_async_setup(door, mock_hass):
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
async def test_register_listeners(door, mock_hass):
    """Test listener registration."""
    mock_hass.states.get.return_value = MagicMock()

    door._register_listeners()

    assert len(door._listeners) > 0
    assert mock_hass.bus.async_listen.call_count >= 2


@pytest.mark.asyncio
async def test_handle_trigger_disabled(door, mock_hass):
    """Test handle trigger when door is disabled."""
    enabled_state = MagicMock()
    enabled_state.state = "off"
    mock_hass.states.get.return_value = enabled_state

    await door._handle_trigger()

    # Should return early, no timer started
    mock_hass.services.async_call.assert_not_called()


@pytest.mark.asyncio
async def test_handle_trigger_enabled(door, mock_hass):
    """Test handle trigger when door is enabled."""
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

    # Should start timer
    assert mock_hass.services.async_call.call_count >= 2  # cancel + start


@pytest.mark.asyncio
async def test_handle_timer_finished(door, mock_hass):
    """Test handle timer finished."""
    with patch.object(door, "_lock_door", new_callable=AsyncMock) as mock_lock:
        await door._handle_timer_finished()

        mock_lock.assert_called_once()


@pytest.mark.asyncio
async def test_lock_door_success(door, mock_hass):
    """Test lock door with success."""
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
async def test_lock_door_failure(door, mock_hass):
    """Test lock door with failure."""
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

        mock_notify.assert_called_once()


@pytest.mark.asyncio
async def test_async_unload(door):
    """Test door unload."""
    door._listeners = [lambda: None, lambda: None]

    await door.async_unload()

    assert len(door._listeners) == 0
