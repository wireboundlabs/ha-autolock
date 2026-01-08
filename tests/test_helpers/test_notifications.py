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
