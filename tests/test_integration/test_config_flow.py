"""Tests for config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.autolock.config_flow import (
    AutoLockConfigFlow,
    AutoLockOptionsFlowHandler,
)


@pytest.fixture
def flow():
    """Create config flow instance."""
    return AutoLockConfigFlow()


@pytest.mark.asyncio
async def test_async_step_user_no_input(flow, mock_hass):
    """Test user step with no input (initial form)."""
    flow.hass = mock_hass

    result = await flow.async_step_user(None)

    assert result["type"] == "form"
    assert result["step_id"] == "user"
    assert "errors" not in result or not result.get("errors")


@pytest.mark.asyncio
async def test_async_step_user_invalid_lock(flow, mock_hass):
    """Test user step with invalid lock entity."""
    flow.hass = mock_hass
    # Set up mock to return None (entity not found) so validation fails
    mock_hass.states.get.return_value = None

    result = await flow.async_step_user(
        {"name": "Test Door", "lock_entity": "invalid"}
    )

    assert result["type"] == "form"
    assert result["step_id"] == "user"
    assert "errors" in result
    assert "lock_entity" in result["errors"]


@pytest.mark.asyncio
async def test_async_step_user_valid(flow, mock_hass):
    """Test user step with valid input."""
    flow.hass = mock_hass
    # Set up mock to return a valid lock state
    lock_state = MagicMock()
    lock_state.state = "locked"
    mock_hass.states.get.return_value = lock_state

    result = await flow.async_step_user(
        {"name": "Test Door", "lock_entity": "lock.test"}
    )

    assert result["type"] == "form"
    assert result["step_id"] == "sensor"
    assert flow.data["name"] == "Test Door"
    assert flow.data["lock_entity"] == "lock.test"


@pytest.mark.asyncio
async def test_async_step_sensor_no_input(flow, mock_hass):
    """Test sensor step with no input (initial form)."""
    flow.hass = mock_hass
    flow.data = {"name": "Test Door", "lock_entity": "lock.test"}

    result = await flow.async_step_sensor(None)

    assert result["type"] == "form"
    assert result["step_id"] == "sensor"


@pytest.mark.asyncio
async def test_async_step_sensor_invalid(flow, mock_hass):
    """Test sensor step with invalid sensor."""
    flow.hass = mock_hass
    flow.data = {"name": "Test Door", "lock_entity": "lock.test"}
    # Set up mock to return None (entity not found) so validation fails
    mock_hass.states.get.return_value = None

    result = await flow.async_step_sensor({"sensor_entity": "invalid"})

    assert result["type"] == "form"
    assert result["step_id"] == "sensor"
    assert "errors" in result
    assert "sensor_entity" in result["errors"]


@pytest.mark.asyncio
async def test_async_step_sensor_valid(flow, mock_hass):
    """Test sensor step with valid input."""
    flow.hass = mock_hass
    flow.data = {"name": "Test Door", "lock_entity": "lock.test"}
    # Set up mock to return a valid sensor state
    sensor_state = MagicMock()
    sensor_state.state = "on"
    mock_hass.states.get.return_value = sensor_state

    result = await flow.async_step_sensor({"sensor_entity": "binary_sensor.test"})

    assert result["type"] == "form"
    assert result["step_id"] == "timing"
    assert flow.data["sensor_entity"] == "binary_sensor.test"


@pytest.mark.asyncio
async def test_async_step_timing_no_input(flow, mock_hass):
    """Test timing step with no input (initial form)."""
    flow.hass = mock_hass
    flow.data = {"name": "Test Door", "lock_entity": "lock.test"}

    result = await flow.async_step_timing(None)

    assert result["type"] == "form"
    assert result["step_id"] == "timing"


@pytest.mark.asyncio
async def test_async_step_timing_invalid_schedule(flow, mock_hass):
    """Test timing step with invalid schedule."""
    flow.hass = mock_hass
    flow.data = {"name": "Test Door", "lock_entity": "lock.test"}

    # Actually execute validation - invalid time format will fail
    result = await flow.async_step_timing(
        {
            "day_delay": 5,
            "night_delay": 2,
            "night_start": "invalid",
            "night_end": "06:00",
        }
    )

    assert result["type"] == "form"
    assert result["step_id"] == "timing"
    assert "errors" in result
    assert "night_start" in result["errors"]


@pytest.mark.asyncio
async def test_async_step_timing_valid(flow, mock_hass):
    """Test timing step with valid input."""
    flow.hass = mock_hass
    flow.data = {"name": "Test Door", "lock_entity": "lock.test"}

    # Actually execute validation - valid times will pass
    result = await flow.async_step_timing(
        {
            "day_delay": 5,
            "night_delay": 2,
            "night_start": "22:00",
            "night_end": "06:00",
        }
    )

    assert result["type"] == "form"
    assert result["step_id"] == "retry"
    assert flow.data["day_delay"] == 5
    assert flow.data["night_delay"] == 2


@pytest.mark.asyncio
async def test_async_step_retry_no_input(flow, mock_hass):
    """Test retry step with no input (initial form)."""
    flow.hass = mock_hass
    flow.data = {
        "name": "Test Door",
        "lock_entity": "lock.test",
        "day_delay": 5,
        "night_delay": 2,
        "night_start": "22:00",
        "night_end": "06:00",
    }

    result = await flow.async_step_retry(None)

    assert result["type"] == "form"
    assert result["step_id"] == "retry"


@pytest.mark.asyncio
async def test_async_step_retry_valid(flow, mock_hass):
    """Test retry step with valid input."""
    flow.hass = mock_hass
    flow.data = {
        "name": "Test Door",
        "lock_entity": "lock.test",
        "day_delay": 5,
        "night_delay": 2,
        "night_start": "22:00",
        "night_end": "06:00",
    }

    result = await flow.async_step_retry(
        {"retry_count": 3, "retry_delay": 5, "verification_delay": 5}
    )

    assert result["type"] == "form"
    assert result["step_id"] == "options"
    assert flow.data["retry_count"] == 3
    assert flow.data["retry_delay"] == 5


@pytest.mark.asyncio
async def test_async_step_options_no_input(flow, mock_hass):
    """Test options step with no input (initial form)."""
    flow.hass = mock_hass
    flow.data = {
        "name": "Test Door",
        "lock_entity": "lock.test",
        "retry_count": 3,
        "retry_delay": 5,
        "verification_delay": 5,
    }

    result = await flow.async_step_options(None)

    assert result["type"] == "form"
    assert result["step_id"] == "options"


@pytest.mark.asyncio
async def test_async_step_options_complete(flow, mock_hass):
    """Test options step completing flow."""
    flow.hass = mock_hass
    flow.data = {
        "name": "Test Door",
        "lock_entity": "lock.test",
        "retry_count": 3,
        "retry_delay": 5,
        "verification_delay": 5,
    }

    with (
        patch.object(
            flow, "async_set_unique_id", new_callable=AsyncMock
        ) as mock_unique,
        patch.object(
            flow, "_abort_if_unique_id_configured", new_callable=MagicMock
        ) as mock_abort,
    ):
        result = await flow.async_step_options({"enable_on_creation": True})

        assert result["type"] == "create_entry"
        assert result["title"] == "Test Door"
        assert result["data"]["name"] == "Test Door"
        mock_unique.assert_called_once()
        mock_abort.assert_called_once()


@pytest.mark.asyncio
async def test_async_get_options_flow(flow, mock_hass):
    """Test async_get_options_flow static method."""
    from homeassistant.config_entries import ConfigEntry

    mock_entry = MagicMock(spec=ConfigEntry)
    mock_entry.entry_id = "test_entry"

    handler = AutoLockConfigFlow.async_get_options_flow(mock_entry)

    assert isinstance(handler, AutoLockOptionsFlowHandler)
    assert handler.config_entry == mock_entry


@pytest.mark.asyncio
async def test_options_flow_init():
    """Test AutoLockOptionsFlowHandler initialization."""
    from homeassistant.config_entries import ConfigEntry

    mock_entry = MagicMock(spec=ConfigEntry)
    handler = AutoLockOptionsFlowHandler(mock_entry)

    assert handler.config_entry == mock_entry


@pytest.mark.asyncio
async def test_options_flow_step_init_no_input(mock_hass):
    """Test options flow init step with no input."""
    from homeassistant.config_entries import ConfigEntry

    mock_entry = MagicMock(spec=ConfigEntry)
    mock_entry.data = {
        "day_delay": 5,
        "night_delay": 2,
        "retry_count": 3,
        "retry_delay": 5,
    }

    handler = AutoLockOptionsFlowHandler(mock_entry)
    handler.hass = mock_hass

    result = await handler.async_step_init(None)

    assert result["type"] == "form"
    assert result["step_id"] == "init"


@pytest.mark.asyncio
async def test_options_flow_step_init_with_input(mock_hass):
    """Test options flow init step with input."""
    from homeassistant.config_entries import ConfigEntry

    mock_entry = MagicMock(spec=ConfigEntry)
    mock_entry.data = {
        "day_delay": 5,
        "night_delay": 2,
        "retry_count": 3,
        "retry_delay": 5,
    }
    mock_entry.entry_id = "test_entry"

    mock_hass.config_entries = MagicMock()
    mock_hass.config_entries.async_update_entry = AsyncMock()

    handler = AutoLockOptionsFlowHandler(mock_entry)
    handler.hass = mock_hass

    result = await handler.async_step_init(
        {
            "day_delay": 10,
            "night_delay": 3,
            "retry_count": 2,
            "retry_delay": 10,
        }
    )

    assert result["type"] == "create_entry"
    assert result["title"] == ""
    mock_hass.config_entries.async_update_entry.assert_called_once()
