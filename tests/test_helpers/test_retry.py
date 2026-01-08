"""Tests for retry strategy."""
from __future__ import annotations

import asyncio

import pytest

from custom_components.autolock.helpers.retry import RetryResult, RetryStrategy


async def successful_callable():
    """Successful callable."""
    return "success"


async def failing_callable():
    """Failing callable."""
    raise ValueError("Test error")


@pytest.mark.asyncio
async def test_retry_success():
    """Test retry with successful call."""
    strategy = RetryStrategy()
    result = await strategy.execute_with_retry(
        successful_callable,
        max_retries=3,
        delay=0.1,
    )

    assert result.success is True
    assert result.attempts == 1
    assert result.error is None


@pytest.mark.asyncio
async def test_retry_failure():
    """Test retry with failing call."""
    strategy = RetryStrategy()
    result = await strategy.execute_with_retry(
        failing_callable,
        max_retries=2,
        delay=0.1,
    )

    assert result.success is False
    assert result.attempts == 3  # Initial + 2 retries
    assert result.error is not None
    assert "Test error" in (result.last_error or "")


@pytest.mark.asyncio
async def test_retry_no_retries():
    """Test retry with max_retries=0."""
    strategy = RetryStrategy()
    result = await strategy.execute_with_retry(
        failing_callable,
        max_retries=0,
        delay=0.1,
    )

    assert result.success is False
    assert result.attempts == 1  # Only initial attempt

