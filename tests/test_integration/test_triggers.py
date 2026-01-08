"""Tests for trigger strategies."""

from __future__ import annotations

from unittest.mock import MagicMock

from custom_components.autolock.triggers import (
    LockTriggerStrategy,
    SensorTriggerStrategy,
    create_trigger_strategy,
)


def test_sensor_trigger_strategy():
    """Test SensorTriggerStrategy."""
    strategy = SensorTriggerStrategy("binary_sensor.test")
    triggers = strategy.get_triggers()

    assert len(triggers) == 1
    assert triggers[0]["platform"] == "state"
    assert triggers[0]["entity_id"] == "binary_sensor.test"
    assert triggers[0]["to"] == "on"


def test_lock_trigger_strategy():
    """Test LockTriggerStrategy."""
    strategy = LockTriggerStrategy("lock.test")
    triggers = strategy.get_triggers()

    assert len(triggers) == 1
    assert triggers[0]["platform"] == "state"
    assert triggers[0]["entity_id"] == "lock.test"
    assert triggers[0]["to"] == "unlocked"


def test_create_trigger_strategy_with_sensor():
    """Test create_trigger_strategy with sensor."""
    hass = MagicMock()
    strategy = create_trigger_strategy(hass, "lock.test", "binary_sensor.test")

    assert isinstance(strategy, SensorTriggerStrategy)


def test_create_trigger_strategy_without_sensor():
    """Test create_trigger_strategy without sensor."""
    hass = MagicMock()
    strategy = create_trigger_strategy(hass, "lock.test", None)

    assert isinstance(strategy, LockTriggerStrategy)
