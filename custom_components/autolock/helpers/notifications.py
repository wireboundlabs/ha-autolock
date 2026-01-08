"""Generic notification service for Home Assistant integrations.

This module provides reusable notification functionality that can be used by
any integration needing notifications (alarms, sensors, automations, etc.).
"""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)


class NotificationService:
    """Generic notification service for Home Assistant.

    Abstracts HA notification services and provides fallback handling.
    """

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize notification service.

        Args:
            hass: Home Assistant instance
        """
        self.hass = hass

    async def send_persistent_notification(
        self,
        notification_id: str,
        title: str,
        message: str,
        severity: str = "error",
    ) -> bool:
        """Send persistent notification.

        Args:
            notification_id: Unique notification ID
            title: Notification title
            message: Notification message
            severity: Notification severity (info, warning, error)

        Returns:
            True if notification was sent successfully
        """
        try:
            await self.hass.services.async_call(
                "persistent_notification",
                "create",
                {
                    "notification_id": notification_id,
                    "title": title,
                    "message": message,
                },
            )
            _LOGGER.debug(
                "Sent persistent notification: %s - %s",
                title,
                message,
            )
            return True
        except Exception as err:
            _LOGGER.error(
                "Failed to send persistent notification: %s",
                err,
                exc_info=True,
            )
            return False

    async def send_push_notification(
        self,
        title: str,
        message: str,
        target: str | None = None,
        data: dict[str, Any] | None = None,
    ) -> bool:
        """Send push notification (if available).

        Args:
            title: Notification title
            message: Notification message
            target: Optional target notify service
            data: Optional additional data

        Returns:
            True if notification was sent successfully, False otherwise
        """
        # Find available notify service
        notify_service = self.find_notify_service(target)

        if not notify_service:
            _LOGGER.debug("No notify service available for push notification")
            return False

        try:
            service_data: dict[str, Any] = {
                "title": title,
                "message": message,
            }
            if data:
                service_data.update(data)

            await self.hass.services.async_call(
                "notify",
                notify_service,
                service_data,
            )
            _LOGGER.debug(
                "Sent push notification via %s: %s - %s",
                notify_service,
                title,
                message,
            )
            return True
        except Exception as err:
            _LOGGER.warning(
                "Failed to send push notification via %s: %s",
                notify_service,
                err,
            )
            return False

    async def send_notification(
        self,
        title: str,
        message: str,
        persistent_id: str | None = None,
        push_target: str | None = None,
        severity: str = "error",
        data: dict[str, Any] | None = None,
    ) -> bool:
        """Send notification (persistent and/or push).

        Args:
            title: Notification title
            message: Notification message
            persistent_id: Optional persistent notification ID
            push_target: Optional push notification target
            severity: Notification severity (info, warning, error)
            data: Optional additional data for push notification

        Returns:
            True if at least one notification was sent successfully
        """
        results = []

        # Send persistent notification if ID provided
        if persistent_id:
            results.append(
                await self.send_persistent_notification(
                    persistent_id,
                    title,
                    message,
                    severity,
                )
            )

        # Send push notification
        results.append(
            await self.send_push_notification(
                title,
                message,
                push_target,
                data,
            )
        )

        # Return True if at least one succeeded (graceful degradation)
        return any(results)

    def find_notify_service(self, target: str | None = None) -> str | None:
        """Find available notify service.

        Args:
            target: Optional target service name (e.g., "mobile_app_iphone")

        Returns:
            Service name if found, None otherwise
        """
        if target and f"notify.{target}" in self.hass.services.async_services().get(
            "notify", {}
        ):
            return target

        # Find first available notify service
        notify_services = self.hass.services.async_services().get("notify", {})
        if notify_services:
            # Return first available service
            return list(notify_services.keys())[0]

        return None

