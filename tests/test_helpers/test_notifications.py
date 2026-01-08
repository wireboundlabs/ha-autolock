"""Tests for notification service."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.autolock.helpers.notifications import NotificationService


@pytest.mark.asyncio
async def test_send_persistent_notification():
    """Test send_persistent_notification."""
    hass = MagicMock()
    hass.services.async_call = AsyncMock(return_value=None)

    service = NotificationService(hass)
    result = await service.send_persistent_notification(
        "test_id", "Test Title", "Test Message"
    )

    assert result is True
    hass.services.async_call.assert_called_once()


@pytest.mark.asyncio
async def test_send_push_notification():
    """Test send_push_notification."""
    hass = MagicMock()
    hass.services.async_services.return_value = {"notify": {"mobile_app": {}}}
    hass.services.async_call = AsyncMock(return_value=None)

    service = NotificationService(hass)
    result = await service.send_push_notification("Title", "Message")

    assert result is True
    hass.services.async_call.assert_called_once()


@pytest.mark.asyncio
async def test_find_notify_service():
    """Test find_notify_service."""
    hass = MagicMock()
    hass.services.async_services.return_value = {"notify": {"mobile_app": {}}}

    service = NotificationService(hass)
    result = service.find_notify_service()

    assert result == "mobile_app"


@pytest.mark.asyncio
async def test_find_notify_service_no_services():
    """Test find_notify_service when no services available."""
    hass = MagicMock()
    hass.services.async_services.return_value = {}

    service = NotificationService(hass)
    result = service.find_notify_service()

    assert result is None


@pytest.mark.asyncio
async def test_find_notify_service_with_target():
    """Test find_notify_service with specific target."""
    hass = MagicMock()
    hass.services.async_services.return_value = {
        "notify": {"notify.mobile_app_iphone": {}, "notify.mobile_app_android": {}}
    }

    service = NotificationService(hass)
    result = service.find_notify_service("mobile_app_iphone")

    assert result == "mobile_app_iphone"


@pytest.mark.asyncio
async def test_find_notify_service_with_invalid_target():
    """Test find_notify_service with invalid target falls back to first service."""
    hass = MagicMock()
    hass.services.async_services.return_value = {"notify": {"mobile_app_android": {}}}

    service = NotificationService(hass)
    result = service.find_notify_service("mobile_app_iphone")

    # Should fall back to first available service
    assert result == "mobile_app_android"


class TestSendNotification:
    """Tests for send_notification method."""

    @pytest.mark.asyncio
    async def test_persistent_only(self, mock_hass):
        """Test with persistent only."""
        mock_hass.services.async_call = AsyncMock(return_value=None)

        service = NotificationService(mock_hass)
        result = await service.send_notification(
            "Title", "Message", persistent_id="test_id"
        )

        assert result is True
        mock_hass.services.async_call.assert_called()

    @pytest.mark.asyncio
    async def test_both_persistent_and_push(self, mock_hass):
        """Test with both persistent and push."""
        mock_hass.services.async_services.return_value = {"notify": {"mobile_app": {}}}
        mock_hass.services.async_call = AsyncMock(return_value=None)

        service = NotificationService(mock_hass)
        result = await service.send_notification(
            "Title",
            "Message",
            persistent_id="test_id",
            push_target="mobile_app",
        )

        assert result is True
        assert mock_hass.services.async_call.call_count >= 1


class TestSendPersistentNotification:
    """Tests for send_persistent_notification method."""

    @pytest.mark.asyncio
    async def test_failure(self, mock_hass):
        """Test with failure."""
        mock_hass.services.async_call = AsyncMock(side_effect=Exception("Error"))

        service = NotificationService(mock_hass)
        result = await service.send_persistent_notification(
            "test_id", "Title", "Message"
        )

        assert result is False


class TestSendPushNotification:
    """Tests for send_push_notification method."""

    @pytest.mark.asyncio
    async def test_no_service(self, mock_hass):
        """Test when no service available."""
        mock_hass.services.async_services.return_value = {}

        service = NotificationService(mock_hass)
        result = await service.send_push_notification("Title", "Message")

        assert result is False

    @pytest.mark.asyncio
    async def test_with_data(self, mock_hass):
        """Test with data parameter."""
        mock_hass.services.async_services.return_value = {"notify": {"mobile_app": {}}}
        mock_hass.services.async_call = AsyncMock(return_value=None)

        service = NotificationService(mock_hass)
        result = await service.send_push_notification(
            "Title", "Message", data={"key": "value"}
        )

        assert result is True
        call_args = mock_hass.services.async_call.call_args
        service_data = call_args[0][2]
        assert service_data.get("key") == "value"
        assert service_data.get("title") == "Title"
        assert service_data.get("message") == "Message"

    @pytest.mark.asyncio
    async def test_exception(self, mock_hass):
        """Test with exception."""
        mock_hass.services.async_services.return_value = {"notify": {"mobile_app": {}}}
        mock_hass.services.async_call = AsyncMock(
            side_effect=Exception("Service error")
        )

        service = NotificationService(mock_hass)
        result = await service.send_push_notification("Title", "Message")

        assert result is False


class TestFindNotifyService:
    """Additional tests for find_notify_service."""

    @pytest.mark.asyncio
    async def test_target_not_found(self, mock_hass):
        """Test when target not found."""
        mock_hass.services.async_services.return_value = {"notify": {"other": {}}}

        service = NotificationService(mock_hass)
        result = service.find_notify_service("mobile_app_iphone")

        # Should return first available
        assert result == "other"

    @pytest.mark.asyncio
    async def test_find_notify_service_with_target_found(self, mock_hass):
        """Test find_notify_service when target is found with notify prefix."""
        mock_hass.services.async_services.return_value = {
            "notify": {"notify.mobile_app_iphone": {}, "notify.mobile_app_android": {}}
        }

        service = NotificationService(mock_hass)
        result = service.find_notify_service("mobile_app_iphone")

        # Should return target (without notify prefix) when found
        assert result == "mobile_app_iphone"
