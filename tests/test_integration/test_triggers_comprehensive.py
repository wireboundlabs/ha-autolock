"""Comprehensive tests for trigger strategies."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from custom_components.autolock.triggers import (
    LockTriggerStrategy,
    SensorTriggerStrategy,
    TriggerStrategy,
    create_trigger_strategy,
)


def test_trigger_strategy_abstract():
    """Test TriggerStrategy is abstract."""
    with pytest.raises(TypeError):
        TriggerStrategy()  # Should not be instantiable


def test_sensor_trigger_strategy_get_triggers():
    """Test SensorTriggerStrategy.get_triggers returns correct format."""
    strategy = SensorTriggerStrategy("binary_sensor.test")
    triggers = strategy.get_triggers()

    assert len(triggers) == 1
    assert triggers[0]["platform"] == "state"
    assert triggers[0]["entity_id"] == "binary_sensor.test"
    assert triggers[0]["to"] == "on"


def test_lock_trigger_strategy_get_triggers():
    """Test LockTriggerStrategy.get_triggers returns correct format."""
    strategy = LockTriggerStrategy("lock.test")
    triggers = strategy.get_triggers()

    assert len(triggers) == 1
    assert triggers[0]["platform"] == "state"
    assert triggers[0]["entity_id"] == "lock.test"
    assert triggers[0]["to"] == "unlocked"


def test_create_trigger_strategy_with_sensor():
    """Test create_trigger_strategy returns SensorTriggerStrategy when sensor provided."""
    hass = MagicMock()
    strategy = create_trigger_strategy(hass, "lock.test", "binary_sensor.test")

    assert isinstance(strategy, SensorTriggerStrategy)
    assert strategy.sensor_entity == "binary_sensor.test"


def test_create_trigger_strategy_without_sensor():
    """Test create_trigger_strategy returns LockTriggerStrategy when no sensor."""
    hass = MagicMock()
    strategy = create_trigger_strategy(hass, "lock.test", None)

    assert isinstance(strategy, LockTriggerStrategy)
    assert strategy.lock_entity == "lock.test"


def test_create_trigger_strategy_with_empty_sensor():
    """Test create_trigger_strategy with empty sensor string."""
    hass = MagicMock()
    strategy = create_trigger_strategy(hass, "lock.test", "")

    # Empty string should be treated as None
    assert isinstance(strategy, LockTriggerStrategy)


def test_sensor_trigger_strategy_init():
    """Test SensorTriggerStrategy initialization."""
    strategy = SensorTriggerStrategy("binary_sensor.test")
    assert strategy.sensor_entity == "binary_sensor.test"


def test_lock_trigger_strategy_init():
    """Test LockTriggerStrategy initialization."""
    strategy = LockTriggerStrategy("lock.test")
    assert strategy.lock_entity == "lock.test"
