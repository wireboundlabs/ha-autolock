"""Pytest configuration and fixtures."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component


@pytest.fixture
def hass() -> HomeAssistant:
    """Create Home Assistant instance."""
    from homeassistant.core import HomeAssistant

    return HomeAssistant()


@pytest.fixture
async def mock_hass():
    """Create mock Home Assistant instance."""
    hass = MagicMock(spec=HomeAssistant)
    hass.states = MagicMock()
    hass.states.get = MagicMock(return_value=None)
    hass.services = MagicMock()
    hass.services.async_call = AsyncMock()
    hass.bus = MagicMock()
    hass.bus.async_listen = MagicMock(return_value=lambda: None)
    hass.data = {}
    return hass


@pytest.fixture
def mock_config_entry():
    """Create mock config entry."""
    from homeassistant.config_entries import ConfigEntry

    entry = MagicMock(spec=ConfigEntry)
    entry.unique_id = "test_door_1"
    entry.entry_id = "test_entry_1"
    entry.title = "Test Door"
    entry.data = {
        "name": "Test Door",
        "lock_entity": "lock.test_lock",
        "sensor_entity": "binary_sensor.test_sensor",
        "day_delay": 5,
        "night_delay": 2,
        "night_start": "22:00",
        "night_end": "06:00",
        "retry_count": 3,
        "retry_delay": 5,
        "verification_delay": 5,
        "enable_on_creation": True,
    }
    return entry

