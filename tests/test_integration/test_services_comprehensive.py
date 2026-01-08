"""Comprehensive tests for services."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.autolock.const import (
    DOMAIN,
    SNOOZE_DURATION_15,
    SNOOZE_DURATION_30,
    SNOOZE_DURATION_60,
)
from custom_components.autolock.services import async_setup_services


@pytest.mark.asyncio
async def test_lock_now_service_success(mock_hass):
    """Test lock_now service with success."""
    door = MagicMock()
    door.config = {
        "name": "Test Door",
        "lock_entity": "lock.test",
        "verification_delay": 5.0,
    }
    door.config.get = lambda key, default=None: door.config.get(key, default)
    door.notification_service = MagicMock()
    door.notification_service.send_notification = AsyncMock()

    mock_hass.data[DOMAIN] = {"test_door": door}

    with (
        patch(
            "custom_components.autolock.services._get_door_instance",
            return_value=door,
        ),
        patch("custom_components.autolock.services.SafetyValidator") as mock_validator,
    ):
        validator_instance = MagicMock()
        validator_instance.lock_with_verification = AsyncMock(
            return_value=MagicMock(success=True, verified=True, error=None)
        )
        mock_validator.return_value = validator_instance

        await async_setup_services(mock_hass)

        # Find lock_now service
        lock_service = None
        for call in mock_hass.services.async_register.call_args_list:
            if call[0][1] == "lock_now":
                lock_service = call[0][2]
                break

        assert lock_service is not None

        call_data = MagicMock()
        call_data.data = {"door_id": "test_door"}
        await lock_service(call_data)

        validator_instance.lock_with_verification.assert_called_once()
        door.notification_service.send_notification.assert_not_called()


@pytest.mark.asyncio
async def test_lock_now_service_failure(mock_hass):
    """Test lock_now service with failure."""
    door = MagicMock()
    door.config = {
        "name": "Test Door",
        "lock_entity": "lock.test",
        "verification_delay": 5.0,
    }
    door.config.get = lambda key, default=None: door.config.get(key, default)
    door.notification_service = MagicMock()
    door.notification_service.send_notification = AsyncMock()

    mock_hass.data[DOMAIN] = {"test_door": door}

    with (
        patch(
            "custom_components.autolock.services._get_door_instance",
            return_value=door,
        ),
        patch("custom_components.autolock.services.SafetyValidator") as mock_validator,
    ):
        validator_instance = MagicMock()
        validator_instance.lock_with_verification = AsyncMock(
            return_value=MagicMock(success=False, verified=False, error="Test error")
        )
        mock_validator.return_value = validator_instance

        await async_setup_services(mock_hass)

        # Find lock_now service
        lock_service = None
        for call in mock_hass.services.async_register.call_args_list:
            if call[0][1] == "lock_now":
                lock_service = call[0][2]
                break

        call_data = MagicMock()
        call_data.data = {"door_id": "test_door"}
        await lock_service(call_data)

        door.notification_service.send_notification.assert_called_once()


@pytest.mark.asyncio
async def test_snooze_service_all_durations(mock_hass):
    """Test snooze service with all valid durations."""
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

    for duration in [SNOOZE_DURATION_15, SNOOZE_DURATION_30, SNOOZE_DURATION_60]:
        call_data = MagicMock()
        call_data.data = {"door_id": "test_door", "duration": duration}
        await snooze_service(call_data)

        assert mock_hass.services.async_call.called


@pytest.mark.asyncio
async def test_snooze_service_missing_door_id(mock_hass):
    """Test snooze service with missing door_id."""
    await async_setup_services(mock_hass)

    # Find snooze service
    snooze_service = None
    for call in mock_hass.services.async_register.call_args_list:
        if call[0][1] == "snooze":
            snooze_service = call[0][2]
            break

    call_data = MagicMock()
    call_data.data = {"duration": 30}  # No door_id
    await snooze_service(call_data)

    # Should not crash
    assert True


@pytest.mark.asyncio
async def test_enable_service_missing_door_id(mock_hass):
    """Test enable service with missing door_id."""
    await async_setup_services(mock_hass)

    # Find enable service
    enable_service = None
    for call in mock_hass.services.async_register.call_args_list:
        if call[0][1] == "enable":
            enable_service = call[0][2]
            break

    call_data = MagicMock()
    call_data.data = {}  # No door_id
    await enable_service(call_data)

    # Should not crash
    assert True


@pytest.mark.asyncio
async def test_disable_service_missing_door_id(mock_hass):
    """Test disable service with missing door_id."""
    await async_setup_services(mock_hass)

    # Find disable service
    disable_service = None
    for call in mock_hass.services.async_register.call_args_list:
        if call[0][1] == "disable":
            disable_service = call[0][2]
            break

    call_data = MagicMock()
    call_data.data = {}  # No door_id
    await disable_service(call_data)

    # Should not crash
    assert True


@pytest.mark.asyncio
async def test_snooze_service_door_not_found(mock_hass):
    """Test snooze service when door not found."""
    mock_hass.data[DOMAIN] = {}

    await async_setup_services(mock_hass)

    # Find snooze service
    snooze_service = None
    for call in mock_hass.services.async_register.call_args_list:
        if call[0][1] == "snooze":
            snooze_service = call[0][2]
            break

    call_data = MagicMock()
    call_data.data = {"door_id": "nonexistent", "duration": 30}
    await snooze_service(call_data)

    # Should not crash
    assert True


@pytest.mark.asyncio
async def test_enable_service_door_not_found(mock_hass):
    """Test enable service when door not found."""
    mock_hass.data[DOMAIN] = {}

    await async_setup_services(mock_hass)

    # Find enable service
    enable_service = None
    for call in mock_hass.services.async_register.call_args_list:
        if call[0][1] == "enable":
            enable_service = call[0][2]
            break

    call_data = MagicMock()
    call_data.data = {"door_id": "nonexistent"}
    await enable_service(call_data)

    # Should not crash
    assert True


@pytest.mark.asyncio
async def test_disable_service_door_not_found(mock_hass):
    """Test disable service when door not found."""
    mock_hass.data[DOMAIN] = {}

    await async_setup_services(mock_hass)

    # Find disable service
    disable_service = None
    for call in mock_hass.services.async_register.call_args_list:
        if call[0][1] == "disable":
            disable_service = call[0][2]
            break

    call_data = MagicMock()
    call_data.data = {"door_id": "nonexistent"}
    await disable_service(call_data)

    # Should not crash
    assert True
