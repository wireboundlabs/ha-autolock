"""Tests for retry strategy."""

from __future__ import annotations

import pytest

from custom_components.autolock.helpers.retry import RetryStrategy


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
    # Test __str__ for failure case
    assert "Failed" in str(result)
    assert "Test error" in str(result)


@pytest.mark.asyncio
async def test_retry_with_exponential_backoff():
    """Test retry with exponential backoff."""
    strategy = RetryStrategy()
    call_count = 0

    async def failing_then_success():
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise ValueError("Retry")
        return "success"

    result = await strategy.execute_with_retry(
        failing_then_success,
        max_retries=2,
        delay=0.01,
        exponential_backoff=True,
    )

    assert result.success is True
    assert result.attempts == 2


@pytest.mark.asyncio
async def test_retry_with_jitter():
    """Test retry with jitter."""
    strategy = RetryStrategy()

    result = await strategy.execute_with_retry(
        failing_callable,
        max_retries=1,
        delay=0.01,
        jitter=True,
    )

    assert result.success is False
    assert result.attempts == 2
