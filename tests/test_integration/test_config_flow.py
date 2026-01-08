"""Tests for config flow."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from custom_components.autolock.config_flow import AutoLockConfigFlow


@pytest.fixture
def flow():
    """Create config flow instance."""
    return AutoLockConfigFlow()


@pytest.mark.asyncio
async def test_async_step_user_invalid_lock(flow, mock_hass):
    """Test user step with invalid lock entity."""
    flow.hass = mock_hass

    with patch(
        "custom_components.autolock.config_flow.validate_lock_entity",
        return_value=False,
    ):
        result = await flow.async_step_user(
            {"name": "Test Door", "lock_entity": "invalid"}
        )

        assert result["type"] == "form"
        assert result["step_id"] == "user"
        assert "errors" in result


@pytest.mark.asyncio
async def test_async_step_user_valid(flow, mock_hass):
    """Test user step with valid input."""
    flow.hass = mock_hass

    with patch(
        "custom_components.autolock.config_flow.validate_lock_entity",
        return_value=True,
    ):
        result = await flow.async_step_user(
            {"name": "Test Door", "lock_entity": "lock.test"}
        )

        assert result["type"] == "form"
        assert result["step_id"] == "sensor"


@pytest.mark.asyncio
async def test_async_step_sensor_invalid(flow, mock_hass):
    """Test sensor step with invalid sensor."""
    flow.hass = mock_hass
    flow.data = {"name": "Test Door", "lock_entity": "lock.test"}

    with patch(
        "custom_components.autolock.config_flow.validate_sensor_entity",
        return_value=False,
    ):
        result = await flow.async_step_sensor({"sensor_entity": "invalid"})

        assert result["type"] == "form"
        assert result["step_id"] == "sensor"
        assert "errors" in result


@pytest.mark.asyncio
async def test_async_step_sensor_valid(flow, mock_hass):
    """Test sensor step with valid input."""
    flow.hass = mock_hass
    flow.data = {"name": "Test Door", "lock_entity": "lock.test"}

    with patch(
        "custom_components.autolock.config_flow.validate_sensor_entity",
        return_value=True,
    ):
        result = await flow.async_step_sensor({"sensor_entity": "binary_sensor.test"})

        assert result["type"] == "form"
        assert result["step_id"] == "timing"


@pytest.mark.asyncio
async def test_async_step_timing_invalid_schedule(flow, mock_hass):
    """Test timing step with invalid schedule."""
    flow.hass = mock_hass
    flow.data = {"name": "Test Door", "lock_entity": "lock.test"}

    with patch(
        "custom_components.autolock.config_flow.validate_schedule",
        return_value=False,
    ):
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


@pytest.mark.asyncio
async def test_async_step_timing_valid(flow, mock_hass):
    """Test timing step with valid input."""
    flow.hass = mock_hass
    flow.data = {"name": "Test Door", "lock_entity": "lock.test"}

    with patch(
        "custom_components.autolock.config_flow.validate_schedule",
        return_value=True,
    ):
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
