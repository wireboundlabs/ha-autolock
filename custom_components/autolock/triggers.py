"""Trigger strategies for AutoLock integration.

Provides different trigger types (sensor-based vs lock-based).
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from homeassistant.core import HomeAssistant


class TriggerStrategy(ABC):
    """Abstract base class for trigger strategies."""

    @abstractmethod
    def get_triggers(self) -> list[dict[str, Any]]:
        """Get automation trigger configuration.

        Returns:
            List of trigger dictionaries for HA automation
        """
        raise NotImplementedError


class SensorTriggerStrategy(TriggerStrategy):
    """Trigger strategy using binary_sensor state changes."""

    def __init__(self, sensor_entity: str) -> None:
        """Initialize sensor trigger strategy.

        Args:
            sensor_entity: Binary sensor entity ID
        """
        self.sensor_entity = sensor_entity

    def get_triggers(self) -> list[dict[str, Any]]:
        """Get sensor-based triggers.

        Returns:
            List with single trigger for sensor state change to "on" (door closed)
        """
        return [
            {
                "platform": "state",
                "entity_id": self.sensor_entity,
                "to": "on",  # Door closed
            }
        ]


class LockTriggerStrategy(TriggerStrategy):
    """Trigger strategy using lock state changes (fallback)."""

    def __init__(self, lock_entity: str) -> None:
        """Initialize lock trigger strategy.

        Args:
            lock_entity: Lock entity ID
        """
        self.lock_entity = lock_entity

    def get_triggers(self) -> list[dict[str, Any]]:
        """Get lock-based triggers.

        Returns:
            List with single trigger for lock state change to "unlocked"
        """
        return [
            {
                "platform": "state",
                "entity_id": self.lock_entity,
                "to": "unlocked",
            }
        ]


def create_trigger_strategy(
    hass: HomeAssistant,
    lock_entity: str,
    sensor_entity: str | None = None,
) -> TriggerStrategy:
    """Create appropriate trigger strategy.

    Args:
        hass: Home Assistant instance
        lock_entity: Lock entity ID
        sensor_entity: Optional sensor entity ID

    Returns:
        TriggerStrategy instance (SensorTriggerStrategy if sensor provided,
        otherwise LockTriggerStrategy)
    """
    if sensor_entity:
        return SensorTriggerStrategy(sensor_entity)
    return LockTriggerStrategy(lock_entity)

