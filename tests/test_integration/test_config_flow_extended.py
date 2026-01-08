"""Extended tests for config flow."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from custom_components.autolock.config_flow import AutoLockConfigFlow


@pytest.fixture
def flow():
    """Create config flow instance."""
    return AutoLockConfigFlow()


@pytest.mark.asyncio
async def test_async_step_retry(flow, mock_hass):
    """Test retry step."""
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


@pytest.mark.asyncio
async def test_async_step_options_complete(flow, mock_hass):
    """Test options step completing flow."""
    flow.hass = mock_hass
    flow.data = {
        "name": "Test Door",
        "lock_entity": "lock.test",
        "day_delay": 5,
        "night_delay": 2,
        "night_start": "22:00",
        "night_end": "06:00",
        "retry_count": 3,
        "retry_delay": 5,
        "verification_delay": 5,
    }

    with (
        patch.object(flow, "async_set_unique_id"),
        patch.object(flow, "_abort_if_unique_id_configured"),
    ):
        result = await flow.async_step_options({"enable_on_creation": True})

        assert result["type"] == "create_entry"
        assert result["title"] == "Test Door"


@pytest.mark.asyncio
async def test_async_step_sensor_no_sensor(flow, mock_hass):
    """Test sensor step with no sensor."""
    flow.hass = mock_hass
    flow.data = {"name": "Test Door", "lock_entity": "lock.test"}

    result = await flow.async_step_sensor({"sensor_entity": ""})

    assert result["type"] == "form"
    assert result["step_id"] == "timing"
