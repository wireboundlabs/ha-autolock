"""Tests for services."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.autolock.const import DOMAIN
from custom_components.autolock.services import async_setup_services


@pytest.mark.asyncio
async def test_async_setup_services(mock_hass):
    """Test service setup."""
    await async_setup_services(mock_hass)

    # Verify services were registered
    assert mock_hass.services.async_register.call_count == 4


@pytest.mark.asyncio
async def test_lock_now_service(mock_hass):
    """Test lock_now service."""
    from custom_components.autolock.services import _get_door_instance

    # Setup door in hass.data
    door = MagicMock()
    door.config = {"name": "Test Door", "lock_entity": "lock.test"}
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
            return_value=MagicMock(success=True, verified=True)
        )
        mock_validator.return_value = validator_instance

        # Call the service
        from custom_components.autolock.services import async_setup_services

        await async_setup_services(mock_hass)

        # Get the registered service
        service_call = None
        for call in mock_hass.services.async_register.call_args_list:
            if call[0][1] == "lock_now":
                service_call = call[0][2]
                break

        if service_call:
            call_data = MagicMock()
            call_data.data = {"door_id": "test_door"}
            await service_call(call_data)

            # Verify lock was called
            validator_instance.lock_with_verification.assert_called_once()
