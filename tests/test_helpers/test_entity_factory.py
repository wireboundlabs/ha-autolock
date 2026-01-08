"""Tests for entity factory."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from custom_components.autolock.helpers.entity_factory import EntityFactory


def test_generate_entity_id():
    """Test generate_entity_id."""
    entity_id = EntityFactory.generate_entity_id("autolock", "door1", "input_boolean")
    assert entity_id == "input_boolean.autolock_door1"


def test_create_script_yaml():
    """Test create_script_yaml."""
    sequence = [{"service": "test.service", "data": {}}]
    config = EntityFactory.create_script_yaml(
        "script.test", "Test Script", sequence, alias="Test"
    )

    assert config["alias"] == "Test"
    assert config["sequence"] == sequence
    assert config["mode"] == "single"


def test_create_automation_yaml():
    """Test create_automation_yaml."""
    triggers = [{"platform": "state", "entity_id": "test.entity"}]
    actions = [{"service": "test.service"}]
    config = EntityFactory.create_automation_yaml(
        "automation.test", "Test Automation", triggers, actions=actions
    )

    assert config["alias"] == "Test Automation"
    assert config["trigger"] == triggers
    assert config["action"] == actions
    assert config["mode"] == "single"
