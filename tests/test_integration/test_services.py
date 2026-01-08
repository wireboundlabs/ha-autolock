"""Tests for AutoLock services."""

from __future__ import annotations

from contextlib import suppress
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.autolock.const import (
    DOMAIN,
    SNOOZE_DURATION_15,
    SNOOZE_DURATION_30,
    SNOOZE_DURATION_60,
)
from custom_components.autolock.services import (
    _get_door_instance,
    async_setup_services,
)


async def _get_service_handler(mock_hass, service_name: str):
    """Helper to get registered service handler."""
    await async_setup_services(mock_hass)
    for call in mock_hass.services.async_register.call_args_list:
        if call[0][1] == service_name:
            return call[0][2]
    return None


@pytest.mark.asyncio
async def test_async_setup_services(mock_hass):
    """Test service setup registers all services."""
    await async_setup_services(mock_hass)
    assert mock_hass.services.async_register.call_count == 4


class TestGetDoorInstance:
    """Tests for _get_door_instance helper."""

    def test_door_found(self, mock_hass):
        """Test when door is found."""
        door = MagicMock()
        mock_hass.data[DOMAIN] = {"test_door": door}
        assert _get_door_instance(mock_hass, "test_door") == door

    def test_door_not_found(self, mock_hass):
        """Test when door is not found."""
        mock_hass.data[DOMAIN] = {}
        assert _get_door_instance(mock_hass, "nonexistent") is None

    def test_no_domain_data(self, mock_hass):
        """Test when domain data doesn't exist."""
        mock_hass.data = {}
        assert _get_door_instance(mock_hass, "test_door") is None


class TestLockNowService:
    """Tests for lock_now service."""

    @pytest.fixture
    def door(self):
        """Create mock door."""
        door = MagicMock()
        door.config = {
            "name": "Test Door",
            "lock_entity": "lock.test",
            "verification_delay": 5.0,
        }
        door.notification_service = MagicMock()
        door.notification_service.send_notification = AsyncMock()
        return door

    @pytest.mark.asyncio
    async def test_success(self, mock_hass, door):
        """Test successful lock."""
        mock_hass.data[DOMAIN] = {"test_door": door}

        with (
            patch(
                "custom_components.autolock.services._get_door_instance",
                return_value=door,
            ),
            patch(
                "custom_components.autolock.services.SafetyValidator"
            ) as mock_validator,
        ):
            validator_instance = MagicMock()
            validator_instance.lock_with_verification = AsyncMock(
                return_value=MagicMock(success=True, verified=True, error=None)
            )
            mock_validator.return_value = validator_instance

            service = await _get_service_handler(mock_hass, "lock_now")
            assert service is not None

            call_data = MagicMock()
            call_data.data = {"door_id": "test_door"}
            await service(call_data)

            validator_instance.lock_with_verification.assert_called_once()
            door.notification_service.send_notification.assert_not_called()

    @pytest.mark.asyncio
    async def test_failure(self, mock_hass, door):
        """Test failed lock."""
        mock_hass.data[DOMAIN] = {"test_door": door}

        with (
            patch(
                "custom_components.autolock.services._get_door_instance",
                return_value=door,
            ),
            patch(
                "custom_components.autolock.services.SafetyValidator"
            ) as mock_validator,
        ):
            validator_instance = MagicMock()
            validator_instance.lock_with_verification = AsyncMock(
                return_value=MagicMock(
                    success=False, verified=False, error="Test error"
                )
            )
            mock_validator.return_value = validator_instance

            service = await _get_service_handler(mock_hass, "lock_now")
            call_data = MagicMock()
            call_data.data = {"door_id": "test_door"}
            await service(call_data)

            door.notification_service.send_notification.assert_called_once()

    @pytest.mark.asyncio
    async def test_verification_failed(self, mock_hass, door):
        """Test when verification fails."""
        mock_hass.data[DOMAIN] = {"test_door": door}

        with (
            patch(
                "custom_components.autolock.services._get_door_instance",
                return_value=door,
            ),
            patch(
                "custom_components.autolock.services.SafetyValidator"
            ) as mock_validator,
        ):
            validator_instance = MagicMock()
            validator_instance.lock_with_verification = AsyncMock(
                return_value=MagicMock(
                    success=True, verified=False, error="Verification failed"
                )
            )
            mock_validator.return_value = validator_instance

            service = await _get_service_handler(mock_hass, "lock_now")
            call_data = MagicMock()
            call_data.data = {"door_id": "test_door"}
            await service(call_data)

            door.notification_service.send_notification.assert_called_once()

    @pytest.mark.asyncio
    async def test_with_sensor_entity(self, mock_hass, door):
        """Test with sensor entity."""
        door.config["sensor_entity"] = "binary_sensor.test"
        mock_hass.data[DOMAIN] = {"test_door": door}

        with (
            patch(
                "custom_components.autolock.services._get_door_instance",
                return_value=door,
            ),
            patch(
                "custom_components.autolock.services.SafetyValidator"
            ) as mock_validator,
        ):
            validator_instance = MagicMock()
            validator_instance.lock_with_verification = AsyncMock(
                return_value=MagicMock(success=True, verified=True, error=None)
            )
            mock_validator.return_value = validator_instance

            service = await _get_service_handler(mock_hass, "lock_now")
            call_data = MagicMock()
            call_data.data = {"door_id": "test_door"}
            await service(call_data)

            call_args = validator_instance.lock_with_verification.call_args
            assert call_args[1]["sensor_entity"] == "binary_sensor.test"

    @pytest.mark.asyncio
    async def test_missing_door_id(self, mock_hass):
        """Test with missing door_id."""
        service = await _get_service_handler(mock_hass, "lock_now")
        call_data = MagicMock()
        call_data.data = {}
        await service(call_data)
        # Should not raise exception

    @pytest.mark.asyncio
    async def test_door_not_found(self, mock_hass):
        """Test when door is not found."""
        mock_hass.data[DOMAIN] = {}
        service = await _get_service_handler(mock_hass, "lock_now")
        call_data = MagicMock()
        call_data.data = {"door_id": "nonexistent"}
        await service(call_data)
        # Should not raise exception

    @pytest.mark.asyncio
    async def test_exception_handling(self, mock_hass, door):
        """Test exception handling.

        When lock_with_verification raises an exception, it propagates
        and the service doesn't send a notification (exception handling
        would need to be added to the service if desired).
        """
        mock_hass.data[DOMAIN] = {"test_door": door}

        with (
            patch(
                "custom_components.autolock.services._get_door_instance",
                return_value=door,
            ),
            patch(
                "custom_components.autolock.services.SafetyValidator"
            ) as mock_validator,
        ):
            validator_instance = MagicMock()
            validator_instance.lock_with_verification = AsyncMock(
                side_effect=Exception("Unexpected error")
            )
            mock_validator.return_value = validator_instance

            service = await _get_service_handler(mock_hass, "lock_now")
            call_data = MagicMock()
            call_data.data = {"door_id": "test_door"}
            # Exception propagates - service doesn't catch it
            with suppress(Exception):
                await service(call_data)
            # Notification is not sent when exception occurs
            door.notification_service.send_notification.assert_not_called()


class TestSnoozeService:
    """Tests for snooze service."""

    @pytest.fixture
    def door(self):
        """Create mock door."""
        door = MagicMock()
        door.config = {"name": "Test Door"}
        return door

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "duration",
        [SNOOZE_DURATION_15, SNOOZE_DURATION_30, SNOOZE_DURATION_60],
    )
    async def test_valid_durations(self, mock_hass, door, duration):
        """Test with valid snooze durations."""
        door_id = "test_door"
        mock_hass.data[DOMAIN] = {door_id: door}
        mock_hass.services.async_call = AsyncMock()

        service = await _get_service_handler(mock_hass, "snooze")
        call_data = MagicMock()
        call_data.data = {"door_id": door_id, "duration": duration}
        await service(call_data)

        assert mock_hass.services.async_call.called
        call_args = mock_hass.services.async_call.call_args
        assert call_args[0][0] == "input_datetime"
        assert call_args[0][1] == "set_datetime"

    @pytest.mark.asyncio
    async def test_default_duration(self, mock_hass, door):
        """Test with default duration."""
        door_id = "test_door"
        mock_hass.data[DOMAIN] = {door_id: door}
        mock_hass.services.async_call = AsyncMock()

        service = await _get_service_handler(mock_hass, "snooze")
        call_data = MagicMock()
        call_data.data = {"door_id": door_id}  # No duration
        await service(call_data)

        assert mock_hass.services.async_call.called

    @pytest.mark.asyncio
    async def test_invalid_duration(self, mock_hass, door):
        """Test with invalid duration."""
        door_id = "test_door"
        mock_hass.data[DOMAIN] = {door_id: door}

        service = await _get_service_handler(mock_hass, "snooze")
        call_data = MagicMock()
        call_data.data = {"door_id": door_id, "duration": 99}
        await service(call_data)
        # Should log error but not crash

    @pytest.mark.asyncio
    async def test_missing_door_id(self, mock_hass):
        """Test with missing door_id."""
        service = await _get_service_handler(mock_hass, "snooze")
        call_data = MagicMock()
        call_data.data = {}
        await service(call_data)

    @pytest.mark.asyncio
    async def test_door_not_found(self, mock_hass):
        """Test when door is not found."""
        mock_hass.data[DOMAIN] = {}
        service = await _get_service_handler(mock_hass, "snooze")
        call_data = MagicMock()
        call_data.data = {"door_id": "nonexistent", "duration": 30}
        await service(call_data)


class TestEnableService:
    """Tests for enable service."""

    @pytest.fixture
    def door(self):
        """Create mock door."""
        door = MagicMock()
        door.config = {"name": "Test Door"}
        return door

    @pytest.mark.asyncio
    async def test_success(self, mock_hass, door):
        """Test successful enable."""
        door_id = "test_door"
        mock_hass.data[DOMAIN] = {door_id: door}
        mock_hass.services.async_call = AsyncMock()

        service = await _get_service_handler(mock_hass, "enable")
        call_data = MagicMock()
        call_data.data = {"door_id": door_id}
        await service(call_data)

        assert mock_hass.services.async_call.called
        call_args = mock_hass.services.async_call.call_args
        assert call_args[0][0] == "input_boolean"
        assert call_args[0][1] == "turn_on"

    @pytest.mark.asyncio
    async def test_missing_door_id(self, mock_hass):
        """Test with missing door_id."""
        service = await _get_service_handler(mock_hass, "enable")
        call_data = MagicMock()
        call_data.data = {}
        await service(call_data)

    @pytest.mark.asyncio
    async def test_door_not_found(self, mock_hass):
        """Test when door is not found."""
        mock_hass.data[DOMAIN] = {}
        service = await _get_service_handler(mock_hass, "enable")
        call_data = MagicMock()
        call_data.data = {"door_id": "nonexistent"}
        await service(call_data)


class TestDisableService:
    """Tests for disable service."""

    @pytest.fixture
    def door(self):
        """Create mock door."""
        door = MagicMock()
        door.config = {"name": "Test Door"}
        return door

    @pytest.mark.asyncio
    async def test_success(self, mock_hass, door):
        """Test successful disable."""
        door_id = "test_door"
        mock_hass.data[DOMAIN] = {door_id: door}
        mock_hass.services.async_call = AsyncMock()

        service = await _get_service_handler(mock_hass, "disable")
        call_data = MagicMock()
        call_data.data = {"door_id": door_id}
        await service(call_data)

        assert mock_hass.services.async_call.called
        call_args = mock_hass.services.async_call.call_args
        assert call_args[0][0] == "input_boolean"
        assert call_args[0][1] == "turn_off"

    @pytest.mark.asyncio
    async def test_missing_door_id(self, mock_hass):
        """Test with missing door_id."""
        service = await _get_service_handler(mock_hass, "disable")
        call_data = MagicMock()
        call_data.data = {}
        await service(call_data)

    @pytest.mark.asyncio
    async def test_door_not_found(self, mock_hass):
        """Test when door is not found."""
        mock_hass.data[DOMAIN] = {}
        service = await _get_service_handler(mock_hass, "disable")
        call_data = MagicMock()
        call_data.data = {"door_id": "nonexistent"}
        await service(call_data)
