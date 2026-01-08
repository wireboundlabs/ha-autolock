"""The AutoLock integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .door import AutolockDoor
from .services import async_setup_services

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the AutoLock integration."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up AutoLock from a config entry."""
    _LOGGER.info("Setting up AutoLock entry: %s", entry.title)

    # Create door instance
    door_id = entry.unique_id or entry.entry_id
    door = AutolockDoor(hass, door_id, entry.data)

    # Set up door
    await door.async_setup()

    # Store door instance
    hass.data[DOMAIN][door_id] = door

    # Set up services (only once)
    if DOMAIN not in hass.data.get("_autolock_services_setup", set()):
        await async_setup_services(hass)
        hass.data.setdefault("_autolock_services_setup", set()).add(DOMAIN)

    _LOGGER.info("AutoLock entry setup complete: %s", entry.title)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.info("Unloading AutoLock entry: %s", entry.title)

    door_id = entry.unique_id or entry.entry_id
    door = hass.data[DOMAIN].get(door_id)

    if door:
        await door.async_unload()
        del hass.data[DOMAIN][door_id]

    _LOGGER.info("AutoLock entry unloaded: %s", entry.title)
    return True

