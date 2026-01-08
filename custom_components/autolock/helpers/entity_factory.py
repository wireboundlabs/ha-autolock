"""Generic factory for creating Home Assistant entities.

This module provides reusable entity creation functionality that can be used
by any integration needing to create helpers, scripts, automations, etc.
"""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)


class EntityFactory:
    """Generic factory for creating HA entities.

    Provides methods to create various HA entities (helpers, scripts, automations).
    """

    @staticmethod
    def generate_entity_id(prefix: str, unique_id: str, domain: str) -> str:
        """Generate entity ID from components.

        Args:
            prefix: Prefix for the entity (e.g., "autolock")
            unique_id: Unique identifier
            domain: Entity domain (e.g., "input_boolean", "timer")

        Returns:
            Entity ID in format: domain.prefix_unique_id
        """
        return f"{domain}.{prefix}_{unique_id}"

    @staticmethod
    async def create_input_boolean(
        hass: HomeAssistant,
        entity_id: str,
        name: str,
        initial_state: bool = False,
        icon: str | None = None,
    ) -> bool:
        """Create input_boolean helper.

        Args:
            hass: Home Assistant instance
            entity_id: Entity ID for the helper
            name: Friendly name
            initial_state: Initial state (default: False)
            icon: Optional icon

        Returns:
            True if created successfully
        """
        try:
            # Check if already exists
            if hass.states.get(entity_id) is not None:
                _LOGGER.debug("Input boolean %s already exists", entity_id)
                return True

            # Create via input_boolean service
            service_data: dict[str, Any] = {
                "entity_id": entity_id,
                "name": name,
                "initial": initial_state,
            }
            if icon:
                service_data["icon"] = icon

            await hass.services.async_call(
                "input_boolean",
                "create",
                service_data,
            )
            _LOGGER.debug("Created input_boolean: %s", entity_id)
            return True
        except Exception as err:
            _LOGGER.error(
                "Failed to create input_boolean %s: %s",
                entity_id,
                err,
                exc_info=True,
            )
            return False

    @staticmethod
    async def create_input_datetime(
        hass: HomeAssistant,
        entity_id: str,
        name: str,
        has_date: bool = False,
        has_time: bool = True,
    ) -> bool:
        """Create input_datetime helper.

        Args:
            hass: Home Assistant instance
            entity_id: Entity ID for the helper
            name: Friendly name
            has_date: Whether to include date
            has_time: Whether to include time

        Returns:
            True if created successfully
        """
        try:
            # Check if already exists
            if hass.states.get(entity_id) is not None:
                _LOGGER.debug("Input datetime %s already exists", entity_id)
                return True

            # Create via input_datetime service
            await hass.services.async_call(
                "input_datetime",
                "create",
                {
                    "entity_id": entity_id,
                    "name": name,
                    "has_date": has_date,
                    "has_time": has_time,
                },
            )
            _LOGGER.debug("Created input_datetime: %s", entity_id)
            return True
        except Exception as err:
            _LOGGER.error(
                "Failed to create input_datetime %s: %s",
                entity_id,
                err,
                exc_info=True,
            )
            return False

    @staticmethod
    async def create_timer(
        hass: HomeAssistant,
        entity_id: str,
        name: str,
        duration: str | None = None,
    ) -> bool:
        """Create timer entity.

        Args:
            hass: Home Assistant instance
            entity_id: Entity ID for the timer
            name: Friendly name
            duration: Optional initial duration (HH:MM:SS format)

        Returns:
            True if created successfully
        """
        try:
            # Check if already exists
            if hass.states.get(entity_id) is not None:
                _LOGGER.debug("Timer %s already exists", entity_id)
                return True

            # Create via timer service
            service_data: dict[str, Any] = {
                "entity_id": entity_id,
                "name": name,
            }
            if duration:
                service_data["duration"] = duration

            await hass.services.async_call(
                "timer",
                "create",
                service_data,
            )
            _LOGGER.debug("Created timer: %s", entity_id)
            return True
        except Exception as err:
            _LOGGER.error(
                "Failed to create timer %s: %s",
                entity_id,
                err,
                exc_info=True,
            )
            return False

    @staticmethod
    def create_script_yaml(
        entity_id: str,
        name: str,
        sequence: list[dict[str, Any]],
        alias: str | None = None,
        mode: str = "single",
    ) -> dict[str, Any]:
        """Generate script YAML configuration.

        Args:
            entity_id: Entity ID for the script
            name: Friendly name
            sequence: List of actions for the script
            alias: Optional alias
            mode: Script mode (single, restart, queued, parallel)

        Returns:
            Script YAML configuration dict
        """
        script_config: dict[str, Any] = {
            "alias": alias or name,
            "sequence": sequence,
            "mode": mode,
        }
        return script_config

    @staticmethod
    def create_automation_yaml(
        entity_id: str,
        name: str,
        triggers: list[dict[str, Any]],
        conditions: list[dict[str, Any]] | None = None,
        actions: list[dict[str, Any]] | None = None,
        mode: str = "single",
    ) -> dict[str, Any]:
        """Generate automation YAML configuration.

        Args:
            entity_id: Entity ID for the automation
            name: Friendly name
            triggers: List of triggers
            conditions: Optional list of conditions
            actions: Optional list of actions
            mode: Automation mode (single, restart, queued, parallel)

        Returns:
            Automation YAML configuration dict
        """
        automation_config: dict[str, Any] = {
            "alias": name,
            "trigger": triggers,
            "mode": mode,
        }

        if conditions:
            automation_config["condition"] = conditions

        if actions:
            automation_config["action"] = actions

        return automation_config
