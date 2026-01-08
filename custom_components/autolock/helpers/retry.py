"""Generic retry strategy for async operations.

This module provides reusable retry logic that can be used by any integration
needing retry functionality (API calls, device commands, etc.).
"""
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Awaitable, Callable, TypeVar

_LOGGER = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass
class RetryResult:
    """Result of a retry operation."""

    success: bool
    attempts: int
    error: Exception | None = None
    last_error: str | None = None

    def __str__(self) -> str:
        """String representation of retry result."""
        if self.success:
            return f"Success after {self.attempts} attempt(s)"
        return f"Failed after {self.attempts} attempt(s): {self.last_error}"


class RetryStrategy:
    """Generic retry strategy for async operations.

    Provides configurable retry logic with exponential backoff and jitter.
    """

    def __init__(
        self,
        logger: logging.Logger | None = None,
    ) -> None:
        """Initialize retry strategy.

        Args:
            logger: Optional logger for retry attempts
        """
        self.logger = logger or _LOGGER

    async def execute_with_retry(
        self,
        callable_func: Callable[[], Awaitable[T]],
        max_retries: int = 3,
        delay: float = 5.0,
        exponential_backoff: bool = True,
        max_delay: float = 60.0,
        jitter: bool = True,
    ) -> RetryResult:
        """Execute async callable with retry logic.

        Args:
            callable_func: Async callable to execute
            max_retries: Maximum number of retry attempts (0 = no retries)
            delay: Initial delay between retries in seconds
            exponential_backoff: Whether to use exponential backoff
            max_delay: Maximum delay between retries in seconds
            jitter: Whether to add random jitter to prevent thundering herd

        Returns:
            RetryResult with success status, attempts, and error details
        """
        attempt = 0
        current_delay = delay
        last_error: Exception | None = None
        last_error_str: str | None = None

        while attempt <= max_retries:
            try:
                result = await callable_func()
                if attempt > 0:
                    self.logger.info(
                        "Operation succeeded after %d retry attempt(s)",
                        attempt,
                    )
                return RetryResult(
                    success=True,
                    attempts=attempt + 1,
                    error=None,
                    last_error=None,
                )
            except Exception as err:
                last_error = err
                last_error_str = str(err)
                attempt += 1

                if attempt > max_retries:
                    self.logger.error(
                        "Operation failed after %d attempt(s): %s",
                        attempt,
                        last_error_str,
                    )
                    break

                # Calculate delay for next retry
                if exponential_backoff:
                    current_delay = min(current_delay * 2, max_delay)
                else:
                    current_delay = delay

                # Add jitter to prevent thundering herd
                if jitter:
                    import random

                    jitter_amount = current_delay * 0.1  # 10% jitter
                    actual_delay = current_delay + random.uniform(
                        -jitter_amount, jitter_amount
                    )
                    actual_delay = max(0.1, actual_delay)  # Minimum 0.1 seconds
                else:
                    actual_delay = current_delay

                self.logger.warning(
                    "Operation failed (attempt %d/%d), retrying in %.1f seconds: %s",
                    attempt,
                    max_retries,
                    actual_delay,
                    last_error_str,
                )

                await asyncio.sleep(actual_delay)

        return RetryResult(
            success=False,
            attempts=attempt,
            error=last_error,
            last_error=last_error_str,
        )

