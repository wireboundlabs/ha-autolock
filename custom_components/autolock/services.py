"""Services for AutoLock integration."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv

from .const import (
    AUTOLOCK_ENABLED_TEMPLATE,
    AUTOLOCK_SNOOZE_TEMPLATE,
    DOMAIN,
    SNOOZE_DURATION_15,
    SNOOZE_DURATION_30,
    SNOOZE_DURATION_60,
)
from .safety import SafetyValidator

_LOGGER = logging.getLogger(__name__)

# Service schemas
SERVICE_LOCK_NOW_SCHEMA = cv.make_entity_service_schema({})
SERVICE_SNOOZE_SCHEMA = cv.make_entity_service_schema(
    {
        cv.Required("duration"): cv.positive_int,
    }
)
SERVICE_ENABLE_SCHEMA = cv.make_entity_service_schema({})
SERVICE_DISABLE_SCHEMA = cv.make_entity_service_schema({})


async def async_setup_services(hass: HomeAssistant) -> None:
    """Set up AutoLock services."""

    async def lock_now_service(call: ServiceCall) -> None:
        """Service to lock door immediately."""
        door_id = call.data.get("door_id")
        if not door_id:
            _LOGGER.error("door_id required for lock_now service")
            return

        # Get door instance from config entry
        door = _get_door_instance(hass, door_id)
        if not door:
            _LOGGER.error("Door %s not found", door_id)
            return

        lock_entity = door.config["lock_entity"]
        sensor_entity = door.config.get("sensor_entity")

        # Use safety validator to lock with verification
        safety_validator = SafetyValidator(hass)
        result = await safety_validator.lock_with_verification(
            lock_entity,
            verification_delay=door.config.get("verification_delay", 5.0),
            sensor_entity=sensor_entity,
        )

        if not result.success or not result.verified:
            error_msg = result.error or "Lock failed"
            await door.notification_service.send_notification(
                title=f"Manual Lock Failed: {door.config['name']}",
                message=f"Failed to lock {lock_entity}: {error_msg}",
                persistent_id=f"autolock_{door_id}_manual_failure",
                severity="error",
            )
            _LOGGER.error("Manual lock failed for door %s: %s", door_id, error_msg)
        else:
            _LOGGER.info("Manual lock successful for door: %s", door.config["name"])

    async def snooze_service(call: ServiceCall) -> None:
        """Service to snooze door."""
        door_id = call.data.get("door_id")
        duration = call.data.get("duration", 30)

        if not door_id:
            _LOGGER.error("door_id required for snooze service")
            return

        # Validate duration
        if duration not in [SNOOZE_DURATION_15, SNOOZE_DURATION_30, SNOOZE_DURATION_60]:
            _LOGGER.error("Invalid snooze duration: %d (must be 15, 30, or 60)", duration)
            return

        # Get door instance
        door = _get_door_instance(hass, door_id)
        if not door:
            _LOGGER.error("Door %s not found", door_id)
            return

        # Calculate snooze until time
        snooze_until = datetime.now() + timedelta(minutes=duration)
        snooze_entity = AUTOLOCK_SNOOZE_TEMPLATE.format(door_id=door_id)

        # Set snooze time
        await hass.services.async_call(
            "input_datetime",
            "set_datetime",
            {
                "entity_id": snooze_entity,
                "datetime": snooze_until.strftime("%Y-%m-%d %H:%M:%S"),
            },
        )

        _LOGGER.info(
            "Snoozed door %s for %d minutes",
            door.config["name"],
            duration,
        )

    async def enable_service(call: ServiceCall) -> None:
        """Service to enable door."""
        door_id = call.data.get("door_id")
        if not door_id:
            _LOGGER.error("door_id required for enable service")
            return

        door = _get_door_instance(hass, door_id)
        if not door:
            _LOGGER.error("Door %s not found", door_id)
            return

        enabled_entity = AUTOLOCK_ENABLED_TEMPLATE.format(door_id=door_id)
        await hass.services.async_call(
            "input_boolean",
            "turn_on",
            {"entity_id": enabled_entity},
        )

        _LOGGER.info("Enabled door: %s", door.config["name"])

    async def disable_service(call: ServiceCall) -> None:
        """Service to disable door."""
        door_id = call.data.get("door_id")
        if not door_id:
            _LOGGER.error("door_id required for disable service")
            return

        door = _get_door_instance(hass, door_id)
        if not door:
            _LOGGER.error("Door %s not found", door_id)
            return

        enabled_entity = AUTOLOCK_ENABLED_TEMPLATE.format(door_id=door_id)
        await hass.services.async_call(
            "input_boolean",
            "turn_off",
            {"entity_id": enabled_entity},
        )

        _LOGGER.info("Disabled door: %s", door.config["name"])

    # Register services
    hass.services.async_register(
        DOMAIN,
        "lock_now",
        lock_now_service,
        schema=SERVICE_LOCK_NOW_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        "snooze",
        snooze_service,
        schema=SERVICE_SNOOZE_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        "enable",
        enable_service,
        schema=SERVICE_ENABLE_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        "disable",
        disable_service,
        schema=SERVICE_DISABLE_SCHEMA,
    )

    _LOGGER.info("AutoLock services registered")


def _get_door_instance(hass: HomeAssistant, door_id: str) -> Any:
    """Get door instance from config entry.

    Args:
        hass: Home Assistant instance
        door_id: Door identifier

    Returns:
        AutolockDoor instance or None
    """
    # Get from domain data
    domain_data = hass.data.get(DOMAIN, {})
    return domain_data.get(door_id)

