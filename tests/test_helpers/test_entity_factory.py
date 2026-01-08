"""Tests for entity factory."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.autolock.helpers.entity_factory import EntityFactory


class TestGenerateEntityId:
    """Tests for generate_entity_id."""

    def test_generate_entity_id(self):
        """Test generate_entity_id."""
        entity_id = EntityFactory.generate_entity_id(
            "autolock", "door1", "input_boolean"
        )
        assert entity_id == "input_boolean.autolock_door1"


class TestCreateScriptYaml:
    """Tests for create_script_yaml."""

    def test_create_script_yaml(self):
        """Test create_script_yaml."""
        sequence = [{"service": "test.service", "data": {}}]
        config = EntityFactory.create_script_yaml(
            "script.test", "Test Script", sequence, alias="Test"
        )

        assert config["alias"] == "Test"
        assert config["sequence"] == sequence
        assert config["mode"] == "single"


class TestCreateAutomationYaml:
    """Tests for create_automation_yaml."""

    def test_basic(self):
        """Test basic automation yaml."""
        triggers = [{"platform": "state", "entity_id": "test.entity"}]
        actions = [{"service": "test.service"}]
        config = EntityFactory.create_automation_yaml(
            "automation.test", "Test Automation", triggers, actions=actions
        )

        assert config["alias"] == "Test Automation"
        assert config["trigger"] == triggers
        assert config["action"] == actions
        assert config["mode"] == "single"

    def test_with_conditions(self):
        """Test with conditions and actions."""
        triggers = [{"platform": "state", "entity_id": "sensor.test"}]
        conditions = [{"condition": "state", "entity_id": "sensor.test", "state": "on"}]
        actions = [{"service": "light.turn_on", "entity_id": "light.test"}]

        result = EntityFactory.create_automation_yaml(
            "automation.test",
            "Test Automation",
            triggers,
            conditions=conditions,
            actions=actions,
        )

        assert result["alias"] == "Test Automation"
        assert result["trigger"] == triggers
        assert result["condition"] == conditions
        assert result["action"] == actions
        assert result["mode"] == "single"


class TestCreateInputBoolean:
    """Tests for create_input_boolean."""

    @pytest.mark.asyncio
    async def test_success(self, mock_hass):
        """Test successful creation."""
        mock_hass.states.get.return_value = None
        mock_hass.services.async_call = AsyncMock()

        result = await EntityFactory.create_input_boolean(
            mock_hass, "input_boolean.test", "Test", initial_state=True
        )

        assert result is True
        mock_hass.services.async_call.assert_called_once()

    @pytest.mark.asyncio
    async def test_with_icon(self, mock_hass):
        """Test with icon."""
        mock_hass.states.get.return_value = None
        mock_hass.services.async_call = AsyncMock()

        result = await EntityFactory.create_input_boolean(
            mock_hass, "input_boolean.test", "Test", icon="mdi:lock"
        )

        assert result is True
        call_args = mock_hass.services.async_call.call_args
        assert call_args[0][2].get("icon") == "mdi:lock"

    @pytest.mark.asyncio
    async def test_already_exists(self, mock_hass):
        """Test when already exists."""
        existing_state = MagicMock()
        mock_hass.states.get.return_value = existing_state

        result = await EntityFactory.create_input_boolean(
            mock_hass, "input_boolean.test", "Test"
        )

        assert result is True
        mock_hass.services.async_call.assert_not_called()

    @pytest.mark.asyncio
    async def test_exception(self, mock_hass):
        """Test with exception."""
        mock_hass.states.get.return_value = None
        mock_hass.services.async_call = AsyncMock(
            side_effect=Exception("Service error")
        )

        result = await EntityFactory.create_input_boolean(
            mock_hass, "input_boolean.test", "Test"
        )

        assert result is False


class TestCreateInputDatetime:
    """Tests for create_input_datetime."""

    @pytest.mark.asyncio
    async def test_success(self, mock_hass):
        """Test successful creation."""
        mock_hass.states.get.return_value = None
        mock_hass.services.async_call = AsyncMock()

        result = await EntityFactory.create_input_datetime(
            mock_hass, "input_datetime.test", "Test", has_date=False, has_time=True
        )

        assert result is True
        mock_hass.services.async_call.assert_called_once()

    @pytest.mark.asyncio
    async def test_already_exists(self, mock_hass):
        """Test when already exists."""
        existing_state = MagicMock()
        mock_hass.states.get.return_value = existing_state

        result = await EntityFactory.create_input_datetime(
            mock_hass, "input_datetime.test", "Test"
        )

        assert result is True
        mock_hass.services.async_call.assert_not_called()

    @pytest.mark.asyncio
    async def test_exception(self, mock_hass):
        """Test with exception."""
        mock_hass.states.get.return_value = None
        mock_hass.services.async_call = AsyncMock(
            side_effect=Exception("Service error")
        )

        result = await EntityFactory.create_input_datetime(
            mock_hass, "input_datetime.test", "Test"
        )

        assert result is False


class TestCreateTimer:
    """Tests for create_timer."""

    @pytest.mark.asyncio
    async def test_success(self, mock_hass):
        """Test successful creation."""
        mock_hass.states.get.return_value = None
        mock_hass.services.async_call = AsyncMock()

        result = await EntityFactory.create_timer(
            mock_hass, "timer.test", "Test", duration="00:05:00"
        )

        assert result is True
        mock_hass.services.async_call.assert_called_once()

    @pytest.mark.asyncio
    async def test_already_exists(self, mock_hass):
        """Test when already exists."""
        existing_state = MagicMock()
        mock_hass.states.get.return_value = existing_state

        result = await EntityFactory.create_timer(mock_hass, "timer.test", "Test")

        assert result is True
        mock_hass.services.async_call.assert_not_called()

    @pytest.mark.asyncio
    async def test_exception(self, mock_hass):
        """Test with exception."""
        mock_hass.states.get.return_value = None
        mock_hass.services.async_call = AsyncMock(
            side_effect=Exception("Service error")
        )

        result = await EntityFactory.create_timer(mock_hass, "timer.test", "Test")

        assert result is False
