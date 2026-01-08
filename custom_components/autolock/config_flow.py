"""Config flow for AutoLock integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN
from .validation import (
    SCHEMA_BASE,
    SCHEMA_OPTIONS,
    SCHEMA_RETRY,
    SCHEMA_SENSOR,
    SCHEMA_TIMING,
    validate_lock_entity,
    validate_schedule,
    validate_sensor_entity,
)

_LOGGER = logging.getLogger(__name__)


class AutoLockConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for AutoLock."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize config flow."""
        self.data: dict[str, Any] = {}

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Validate lock entity
            if not validate_lock_entity(self.hass, user_input["lock_entity"]):
                errors["lock_entity"] = "invalid_lock_entity"
            else:
                self.data.update(user_input)
                return await self.async_step_sensor()

        return self.async_show_form(
            step_id="user",
            data_schema=SCHEMA_BASE,
            errors=errors,
        )

    async def async_step_sensor(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Handle sensor step (optional)."""
        if user_input is not None:
            sensor_entity = user_input.get("sensor_entity")
            if sensor_entity and not validate_sensor_entity(self.hass, sensor_entity):
                return self.async_show_form(
                    step_id="sensor",
                    data_schema=SCHEMA_SENSOR,
                    errors={"sensor_entity": "invalid_sensor_entity"},
                )
            self.data.update(user_input)
            return await self.async_step_timing()

        return self.async_show_form(
            step_id="sensor",
            data_schema=SCHEMA_SENSOR,
        )

    async def async_step_timing(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Handle timing step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Validate schedule
            if not validate_schedule(
                user_input["night_start"],
                user_input["night_end"],
            ):
                errors["night_start"] = "invalid_schedule"
            else:
                self.data.update(user_input)
                return await self.async_step_retry()

        return self.async_show_form(
            step_id="timing",
            data_schema=SCHEMA_TIMING,
            errors=errors,
        )

    async def async_step_retry(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Handle retry settings step."""
        if user_input is not None:
            self.data.update(user_input)
            return await self.async_step_options()

        return self.async_show_form(
            step_id="retry",
            data_schema=SCHEMA_RETRY,
        )

    async def async_step_options(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Handle options step."""
        if user_input is not None:
            self.data.update(user_input)

            # Generate unique ID
            unique_id = f"{self.data['lock_entity']}"
            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()

            # Create config entry
            return self.async_create_entry(
                title=self.data["name"],
                data=self.data,
            )

        return self.async_show_form(
            step_id="options",
            data_schema=SCHEMA_OPTIONS,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> AutoLockOptionsFlowHandler:
        """Get options flow handler."""
        return AutoLockOptionsFlowHandler(config_entry)


class AutoLockOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for AutoLock."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Handle options flow."""
        if user_input is not None:
            # Update config entry
            self.hass.config_entries.async_update_entry(
                self.config_entry,
                data={**self.config_entry.data, **user_input},
            )
            return self.async_create_entry(title="", data={})

        # Show current values
        current_data = self.config_entry.data
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        "day_delay",
                        default=current_data.get("day_delay", 5),
                    ): vol.All(
                        vol.Coerce(int),
                        vol.Range(min=1, max=240),
                    ),
                    vol.Required(
                        "night_delay",
                        default=current_data.get("night_delay", 2),
                    ): vol.All(
                        vol.Coerce(int),
                        vol.Range(min=1, max=30),
                    ),
                    vol.Required(
                        "retry_count",
                        default=current_data.get("retry_count", 3),
                    ): vol.All(
                        vol.Coerce(int),
                        vol.Range(min=0, max=5),
                    ),
                    vol.Required(
                        "retry_delay",
                        default=current_data.get("retry_delay", 5),
                    ): vol.All(
                        vol.Coerce(int),
                        vol.Range(min=3, max=60),
                    ),
                }
            ),
        )

