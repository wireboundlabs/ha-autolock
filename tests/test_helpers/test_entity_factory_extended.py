"""Extended tests for entity factory."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.autolock.helpers.entity_factory import EntityFactory


@pytest.mark.asyncio
async def test_create_input_boolean(mock_hass):
    """Test create_input_boolean."""
    mock_hass.states.get.return_value = None
    mock_hass.services.async_call = AsyncMock()

    result = await EntityFactory.create_input_boolean(
        mock_hass, "input_boolean.test", "Test", initial_state=True
    )

    assert result is True
    mock_hass.services.async_call.assert_called_once()


@pytest.mark.asyncio
async def test_create_input_boolean_already_exists(mock_hass):
    """Test create_input_boolean when already exists."""
    existing_state = MagicMock()
    mock_hass.states.get.return_value = existing_state

    result = await EntityFactory.create_input_boolean(
        mock_hass, "input_boolean.test", "Test"
    )

    assert result is True
    # Should not call create service
    mock_hass.services.async_call.assert_not_called()


@pytest.mark.asyncio
async def test_create_input_datetime(mock_hass):
    """Test create_input_datetime."""
    mock_hass.states.get.return_value = None
    mock_hass.services.async_call = AsyncMock()

    result = await EntityFactory.create_input_datetime(
        mock_hass, "input_datetime.test", "Test", has_date=False, has_time=True
    )

    assert result is True
    mock_hass.services.async_call.assert_called_once()


@pytest.mark.asyncio
async def test_create_timer(mock_hass):
    """Test create_timer."""
    mock_hass.states.get.return_value = None
    mock_hass.services.async_call = AsyncMock()

    result = await EntityFactory.create_timer(
        mock_hass, "timer.test", "Test", duration="00:05:00"
    )

    assert result is True
    mock_hass.services.async_call.assert_called_once()
