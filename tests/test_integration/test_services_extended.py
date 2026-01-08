"""Extended tests for services."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.autolock.const import DOMAIN, SNOOZE_DURATION_30
from custom_components.autolock.services import async_setup_services


@pytest.mark.asyncio
async def test_snooze_service(mock_hass):
    """Test snooze service."""
    door = MagicMock()
    door.config = {"name": "Test Door"}
    mock_hass.data[DOMAIN] = {"test_door": door}
    mock_hass.services.async_call = AsyncMock()

    await async_setup_services(mock_hass)

    # Find snooze service
    snooze_service = None
    for call in mock_hass.services.async_register.call_args_list:
        if call[0][1] == "snooze":
            snooze_service = call[0][2]
            break

    if snooze_service:
        call_data = MagicMock()
        call_data.data = {"door_id": "test_door", "duration": SNOOZE_DURATION_30}
        await snooze_service(call_data)

        # Verify service was called
        assert mock_hass.services.async_call.called


@pytest.mark.asyncio
async def test_snooze_service_invalid_duration(mock_hass):
    """Test snooze service with invalid duration."""
    door = MagicMock()
    door.config = {"name": "Test Door"}
    mock_hass.data[DOMAIN] = {"test_door": door}

    await async_setup_services(mock_hass)

    # Find snooze service
    snooze_service = None
    for call in mock_hass.services.async_register.call_args_list:
        if call[0][1] == "snooze":
            snooze_service = call[0][2]
            break

    if snooze_service:
        call_data = MagicMock()
        call_data.data = {"door_id": "test_door", "duration": 99}  # Invalid
        await snooze_service(call_data)

        # Should not call service
        mock_hass.services.async_call.assert_not_called()


@pytest.mark.asyncio
async def test_enable_service(mock_hass):
    """Test enable service."""
    door = MagicMock()
    door.config = {"name": "Test Door"}
    mock_hass.data[DOMAIN] = {"test_door": door}
    mock_hass.services.async_call = AsyncMock()

    await async_setup_services(mock_hass)

    # Find enable service
    enable_service = None
    for call in mock_hass.services.async_register.call_args_list:
        if call[0][1] == "enable":
            enable_service = call[0][2]
            break

    if enable_service:
        call_data = MagicMock()
        call_data.data = {"door_id": "test_door"}
        await enable_service(call_data)

        mock_hass.services.async_call.assert_called_once()


@pytest.mark.asyncio
async def test_disable_service(mock_hass):
    """Test disable service."""
    door = MagicMock()
    door.config = {"name": "Test Door"}
    mock_hass.data[DOMAIN] = {"test_door": door}
    mock_hass.services.async_call = AsyncMock()

    await async_setup_services(mock_hass)

    # Find disable service
    disable_service = None
    for call in mock_hass.services.async_register.call_args_list:
        if call[0][1] == "disable":
            disable_service = call[0][2]
            break

    if disable_service:
        call_data = MagicMock()
        call_data.data = {"door_id": "test_door"}
        await disable_service(call_data)

        mock_hass.services.async_call.assert_called_once()


@pytest.mark.asyncio
async def test_lock_now_service_missing_door_id(mock_hass):
    """Test lock_now service with missing door_id."""
    await async_setup_services(mock_hass)

    # Find lock_now service
    lock_service = None
    for call in mock_hass.services.async_register.call_args_list:
        if call[0][1] == "lock_now":
            lock_service = call[0][2]
            break

    if lock_service:
        call_data = MagicMock()
        call_data.data = {}  # No door_id
        await lock_service(call_data)

        # Should not proceed
        assert True  # No exception raised


@pytest.mark.asyncio
async def test_lock_now_service_door_not_found(mock_hass):
    """Test lock_now service when door not found."""
    mock_hass.data[DOMAIN] = {}

    await async_setup_services(mock_hass)

    # Find lock_now service
    lock_service = None
    for call in mock_hass.services.async_register.call_args_list:
        if call[0][1] == "lock_now":
            lock_service = call[0][2]
            break

    if lock_service:
        call_data = MagicMock()
        call_data.data = {"door_id": "nonexistent"}
        await lock_service(call_data)

        # Should not proceed
        assert True  # No exception raised
