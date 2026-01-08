"""Extended tests for notification service."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from custom_components.autolock.helpers.notifications import NotificationService


@pytest.mark.asyncio
async def test_send_notification_persistent_only(mock_hass):
    """Test send_notification with persistent only."""
    mock_hass.services.async_call = AsyncMock(return_value=None)

    service = NotificationService(mock_hass)
    result = await service.send_notification(
        "Title", "Message", persistent_id="test_id"
    )

    assert result is True
    mock_hass.services.async_call.assert_called()


@pytest.mark.asyncio
async def test_send_notification_both(mock_hass):
    """Test send_notification with both persistent and push."""
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


@pytest.mark.asyncio
async def test_send_persistent_notification_failure(mock_hass):
    """Test send_persistent_notification with failure."""
    mock_hass.services.async_call = AsyncMock(side_effect=Exception("Error"))

    service = NotificationService(mock_hass)
    result = await service.send_persistent_notification("test_id", "Title", "Message")

    assert result is False


@pytest.mark.asyncio
async def test_send_push_notification_no_service(mock_hass):
    """Test send_push_notification when no service available."""
    mock_hass.services.async_services.return_value = {}

    service = NotificationService(mock_hass)
    result = await service.send_push_notification("Title", "Message")

    assert result is False


@pytest.mark.asyncio
async def test_find_notify_service_with_target(mock_hass):
    """Test find_notify_service with specific target."""
    mock_hass.services.async_services.return_value = {
        "notify": {"mobile_app_iphone": {}}
    }

    service = NotificationService(mock_hass)
    result = service.find_notify_service("mobile_app_iphone")

    assert result == "mobile_app_iphone"


@pytest.mark.asyncio
async def test_find_notify_service_target_not_found(mock_hass):
    """Test find_notify_service when target not found."""
    mock_hass.services.async_services.return_value = {"notify": {"other": {}}}

    service = NotificationService(mock_hass)
    result = service.find_notify_service("mobile_app_iphone")

    # Should return first available
    assert result == "other"


@pytest.mark.asyncio
async def test_send_push_notification_with_data(mock_hass):
    """Test send_push_notification with data parameter."""
    mock_hass.services.async_services.return_value = {"notify": {"mobile_app": {}}}
    mock_hass.services.async_call = AsyncMock(return_value=None)

    service = NotificationService(mock_hass)
    result = await service.send_push_notification(
        "Title", "Message", data={"key": "value"}
    )

    assert result is True
    call_args = mock_hass.services.async_call.call_args
    # Data is merged directly into service_data, not nested under 'data'
    service_data = call_args[0][2]
    assert service_data.get("key") == "value"
    assert service_data.get("title") == "Title"
    assert service_data.get("message") == "Message"


@pytest.mark.asyncio
async def test_send_push_notification_exception(mock_hass):
    """Test send_push_notification with exception."""
    mock_hass.services.async_services.return_value = {"notify": {"mobile_app": {}}}
    mock_hass.services.async_call = AsyncMock(side_effect=Exception("Service error"))

    service = NotificationService(mock_hass)
    result = await service.send_push_notification("Title", "Message")

    assert result is False
