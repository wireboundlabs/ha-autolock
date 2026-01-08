"""Safety validator for AutoLock integration.

Handles pre-lock safety checks and post-lock verification.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass

from homeassistant.core import HomeAssistant

from .const import LOCK_STATE_LOCKED

_LOGGER = logging.getLogger(__name__)


@dataclass
class LockResult:
    """Result of a lock operation."""

    success: bool
    verified: bool
    error: str | None = None


class SafetyValidator:
    """Safety validator for lock operations.

    Handles pre-lock validation and post-lock verification.
    """

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize safety validator.

        Args:
            hass: Home Assistant instance
        """
        self.hass = hass

    def can_lock(
        self,
        lock_entity: str,
        sensor_entity: str | None = None,
    ) -> tuple[bool, str | None]:
        """Check if lock operation is safe to perform.

        Args:
            lock_entity: Lock entity ID
            sensor_entity: Optional door sensor entity ID

        Returns:
            Tuple of (can_lock: bool, reason: str | None)
        """
        # Check lock state
        lock_state = self.hass.states.get(lock_entity)
        if lock_state is None:
            return False, f"Lock entity {lock_entity} not found"

        if lock_state.state == LOCK_STATE_LOCKED:
            return False, "Lock is already locked"

        # Check door sensor if provided
        if sensor_entity:
            sensor_state = self.hass.states.get(sensor_entity)
            if sensor_state is None:
                return False, f"Sensor entity {sensor_entity} not found"

            # Door closed = sensor state "on"
            if sensor_state.state != "on":
                return False, "Door is open"

        return True, None

    async def verify_lock_state(
        self,
        lock_entity: str,
        expected_state: str,
        timeout: float = 10.0,
    ) -> tuple[bool, str | None]:
        """Verify lock reached expected state after operation.

        Args:
            lock_entity: Lock entity ID
            expected_state: Expected state (e.g., "locked")
            timeout: Maximum time to wait in seconds

        Returns:
            Tuple of (verified: bool, reason: str | None)
        """
        start_time = asyncio.get_event_loop().time()
        poll_interval = 0.5  # Poll every 0.5 seconds

        while True:
            lock_state = self.hass.states.get(lock_entity)
            if lock_state is None:
                return False, f"Lock entity {lock_entity} not found"

            if lock_state.state == expected_state:
                return True, None

            # Check timeout
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed >= timeout:
                current_state = lock_state.state
                return (
                    False,
                    f"Lock did not reach state {expected_state} within "
                    f"{timeout}s (current: {current_state})",
                )

            await asyncio.sleep(poll_interval)

    async def lock_with_verification(
        self,
        lock_entity: str,
        verification_delay: float = 5.0,
        sensor_entity: str | None = None,
    ) -> LockResult:
        """Call lock service and verify success.

        Args:
            lock_entity: Lock entity ID
            verification_delay: Time to wait before verifying (seconds)
            sensor_entity: Optional door sensor entity ID

        Returns:
            LockResult with success, verified, and error details
        """
        # Pre-lock safety check
        can_lock, reason = self.can_lock(lock_entity, sensor_entity)
        if not can_lock:
            return LockResult(
                success=False,
                verified=False,
                error=reason or "Pre-lock safety check failed",
            )

        # Call lock service
        try:
            await self.hass.services.async_call(
                "lock",
                "lock",
                {"entity_id": lock_entity},
            )
            _LOGGER.debug("Lock service called for %s", lock_entity)
        except Exception as err:
            error_msg = f"Lock service call failed: {err}"
            _LOGGER.error(error_msg, exc_info=True)
            return LockResult(
                success=False,
                verified=False,
                error=error_msg,
            )

        # Wait for verification delay
        await asyncio.sleep(verification_delay)

        # Verify lock state
        verified, verify_reason = await self.verify_lock_state(
            lock_entity,
            LOCK_STATE_LOCKED,
            timeout=5.0,  # Additional timeout after delay
        )

        if not verified:
            error_msg = f"Lock verification failed: {verify_reason}"
            _LOGGER.warning(error_msg)
            return LockResult(
                success=False,
                verified=False,
                error=error_msg,
            )

        _LOGGER.debug("Lock verified successfully for %s", lock_entity)
        return LockResult(
            success=True,
            verified=True,
            error=None,
        )
