"""Door manager for AutoLock integration.

Orchestrates all components for a single door instance.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from typing import Any

from homeassistant.core import Event, HomeAssistant, callback

from .const import (
    AUTOLOCK_AUTOMATION_TEMPLATE,
    AUTOLOCK_ENABLED_TEMPLATE,
    AUTOLOCK_SCRIPT_TEMPLATE,
    AUTOLOCK_SNOOZE_TEMPLATE,
    AUTOLOCK_TIMER_TEMPLATE,
    LOCK_STATE_UNLOCKED,
)
from .helpers import (
    EntityFactory,
    NotificationService,
    RetryStrategy,
    ScheduleCalculator,
)
from .helpers.schedule import ScheduleConfig
from .safety import LockResult, SafetyValidator
from .triggers import create_trigger_strategy

_LOGGER = logging.getLogger(__name__)


class AutolockDoor:
    """Manages auto-lock functionality for a single door."""

    def __init__(
        self,
        hass: HomeAssistant,
        door_id: str,
        config: dict[str, Any],
    ) -> None:
        """Initialize door manager.

        Args:
            hass: Home Assistant instance
            door_id: Unique door identifier
            config: Door configuration
        """
        self.hass = hass
        self.door_id = door_id
        self.config = config

        # Components
        self.schedule_calculator = ScheduleCalculator()
        self.retry_strategy = RetryStrategy(logger=_LOGGER)
        self.notification_service = NotificationService(hass)
        self.safety_validator = SafetyValidator(hass)
        self.entity_factory = EntityFactory()

        # Entity IDs
        self.enabled_entity = AUTOLOCK_ENABLED_TEMPLATE.format(door_id=door_id)
        self.snooze_entity = AUTOLOCK_SNOOZE_TEMPLATE.format(door_id=door_id)
        self.timer_entity = AUTOLOCK_TIMER_TEMPLATE.format(door_id=door_id)
        self.script_entity = AUTOLOCK_SCRIPT_TEMPLATE.format(door_id=door_id)
        self.automation_entity = AUTOLOCK_AUTOMATION_TEMPLATE.format(door_id=door_id)

        # Schedule config
        self.schedule_config = ScheduleConfig.from_strings(
            config["night_start"],
            config["night_end"],
        )

        # Event listeners
        self._listeners: list[Callable[[], None]] = []

    async def async_setup(self) -> None:
        """Set up door instance (create entities, register listeners)."""
        _LOGGER.info("Setting up door: %s", self.config["name"])

        # Create helper entities
        await self._create_entities()

        # Register event listeners
        self._register_listeners()

        _LOGGER.info("Door setup complete: %s", self.config["name"])

    async def _create_entities(self) -> None:
        """Create helper entities."""
        # Create enabled helper
        await self.entity_factory.create_input_boolean(
            self.hass,
            self.enabled_entity,
            f"{self.config['name']} AutoLock Enabled",
            initial_state=self.config.get("enable_on_creation", True),
        )

        # Create snooze helper
        await self.entity_factory.create_input_datetime(
            self.hass,
            self.snooze_entity,
            f"{self.config['name']} AutoLock Snooze",
            has_date=False,
            has_time=True,
        )

        # Create timer
        await self.entity_factory.create_timer(
            self.hass,
            self.timer_entity,
            f"{self.config['name']} AutoLock Delay",
        )

    def _register_listeners(self) -> None:
        """Register event listeners for state changes."""
        # Listen to trigger entity state changes
        trigger_strategy = create_trigger_strategy(
            self.hass,
            self.config["lock_entity"],
            self.config.get("sensor_entity"),
        )

        # Get trigger entities
        triggers = trigger_strategy.get_triggers()
        for trigger in triggers:
            entity_id = trigger.get("entity_id")
            if entity_id:
                self._listen_to_state_changes(entity_id)

        # Listen to timer finished events
        self._listen_to_timer_finished()

    @callback
    def _listen_to_state_changes(self, entity_id: str) -> None:
        """Listen to state changes for trigger entity."""

        @callback
        def state_changed_listener(event: Event) -> None:
            """Handle state change event."""
            if event.data.get("entity_id") != entity_id:
                return

            new_state = event.data.get("new_state")
            if not new_state:
                return

            # Check if this is a trigger event (door closed or lock unlocked)
            trigger_state = (
                "on" if "sensor" in entity_id.lower() else LOCK_STATE_UNLOCKED
            )
            if new_state.state == trigger_state:
                self.hass.async_create_task(self._handle_trigger())

        self._listeners.append(
            self.hass.bus.async_listen("state_changed", state_changed_listener)
        )

    @callback
    def _listen_to_timer_finished(self) -> None:
        """Listen to timer finished events."""

        @callback
        def timer_finished_listener(event: Event) -> None:
            """Handle timer finished event."""
            if event.data.get("entity_id") == self.timer_entity:
                self.hass.async_create_task(self._handle_timer_finished())

        self._listeners.append(
            self.hass.bus.async_listen("timer.finished", timer_finished_listener)
        )

    async def _handle_trigger(self) -> None:
        """Handle trigger event (door closed or lock unlocked)."""
        _LOGGER.debug("Trigger event for door: %s", self.config["name"])

        # Check if enabled
        enabled_state = self.hass.states.get(self.enabled_entity)
        if not enabled_state or enabled_state.state != "on":
            _LOGGER.debug("Door %s is disabled", self.config["name"])
            return

        # Check if snoozed
        snooze_state = self.hass.states.get(self.snooze_entity)
        if snooze_state and snooze_state.state not in ("unknown", "unavailable"):
            # Check if snooze time is in the future
            from datetime import datetime

            try:
                snooze_time = datetime.fromisoformat(snooze_state.state)
                if snooze_time > datetime.now(snooze_time.tzinfo):
                    _LOGGER.debug("Door %s is snoozed", self.config["name"])
                    return
            except (ValueError, AttributeError):
                pass

        # Cancel existing timer
        await self.hass.services.async_call(
            "timer",
            "cancel",
            {"entity_id": self.timer_entity},
        )

        # Calculate delay
        from datetime import datetime

        now = datetime.now()
        delay_minutes = self.schedule_calculator.get_delay(
            now,
            self.config["day_delay"],
            self.config["night_delay"],
            self.schedule_config,
        )

        # Start timer
        delay_minutes * 60
        await self.hass.services.async_call(
            "timer",
            "start",
            {
                "entity_id": self.timer_entity,
                "duration": f"00:{delay_minutes:02d}:00",
            },
        )

        _LOGGER.info(
            "Started %d minute delay timer for door: %s",
            delay_minutes,
            self.config["name"],
        )

    async def _handle_timer_finished(self) -> None:
        """Handle timer finished event."""
        _LOGGER.info("Timer finished for door: %s", self.config["name"])

        # Attempt to lock
        await self._lock_door()

    async def _lock_door(self) -> None:
        """Lock the door with retry logic."""
        lock_entity = self.config["lock_entity"]
        sensor_entity = self.config.get("sensor_entity")

        # Attempt lock with retry logic
        last_lock_result: LockResult | None = None
        retry_count = self.config.get("retry_count", 3)

        for attempt in range(retry_count + 1):
            lock_result = await self.safety_validator.lock_with_verification(
                lock_entity,
                verification_delay=self.config.get("verification_delay", 5.0),
                sensor_entity=sensor_entity,
            )

            if lock_result.success and lock_result.verified:
                _LOGGER.info(
                    "Lock successful for door %s (attempt %d)",
                    self.config["name"],
                    attempt + 1,
                )
                return

            last_lock_result = lock_result

            # If not last attempt, wait before retry
            if attempt < retry_count:
                retry_delay = self.config.get("retry_delay", 5.0)
                _LOGGER.warning(
                    "Lock failed for door %s (attempt %d/%d), retrying in %.1f seconds",
                    self.config["name"],
                    attempt + 1,
                    retry_count + 1,
                    retry_delay,
                )
                await asyncio.sleep(retry_delay)

        # All retries failed
        error_msg = (
            last_lock_result.error if last_lock_result and last_lock_result.error else "Lock failed"
        )
        message = (
            f"Failed to lock {lock_entity}: {error_msg}\n\n"
            "Likely cloud auth / integration issue. "
            "Check lock integration status."
        )
        await self.notification_service.send_notification(
            title=f"AutoLock Failed: {self.config['name']}",
            message=message,
            persistent_id=f"autolock_{self.door_id}_failure",
            severity="error",
        )

    async def async_unload(self) -> None:
        """Unload door instance (remove listeners)."""
        _LOGGER.info("Unloading door: %s", self.config["name"])

        # Remove listeners
        for remove_listener in self._listeners:
            remove_listener()
        self._listeners.clear()

        _LOGGER.info("Door unloaded: %s", self.config["name"])
