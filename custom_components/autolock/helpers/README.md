# Reusable Helpers

This directory contains **integration-agnostic** helper modules that can be reused across different Home Assistant integrations.

## Design Philosophy

These helpers are designed to be:
- **Integration-agnostic**: No dependencies on autolock-specific code
- **Easily copyable**: Can be copied to other integrations as-is
- **Extractable**: Can be moved to a shared core integration library
- **Well-documented**: Includes docstrings and usage examples

## Available Helpers

### ScheduleCalculator (`schedule.py`)

Generic day/night schedule logic for any integration needing time-based schedules.

**Usage:**
```python
from custom_components.autolock.helpers import ScheduleCalculator
from custom_components.autolock.helpers.schedule import ScheduleConfig

calculator = ScheduleCalculator()
schedule = ScheduleConfig.from_strings("22:00", "06:00")

# Get delay based on current time
delay = calculator.get_delay(now, day_delay=5, night_delay=2, schedule=schedule)
```

**Features:**
- Handles midnight crossing (e.g., 22:00-06:00)
- Pure functions (no side effects)
- No HA dependencies

### RetryStrategy (`retry.py`)

Generic retry logic for async operations with exponential backoff.

**Usage:**
```python
from custom_components.autolock.helpers import RetryStrategy

strategy = RetryStrategy()

async def my_operation():
    # Your async operation
    pass

result = await strategy.execute_with_retry(
    my_operation,
    max_retries=3,
    delay=5.0,
    exponential_backoff=True,
)
```

**Features:**
- Configurable retry count and delay
- Exponential backoff with jitter
- Structured result with attempt count and errors

### NotificationService (`notifications.py`)

Generic notification service abstraction for persistent and push notifications.

**Usage:**
```python
from custom_components.autolock.helpers import NotificationService

notifier = NotificationService(hass)

await notifier.send_notification(
    title="Alert",
    message="Something happened",
    persistent_id="my_notification",
    push_target="mobile_app_iphone",
)
```

**Features:**
- Persistent notifications
- Push notifications (if available)
- Graceful fallback handling

### Entity Validation (`entity_validation.py`)

Generic entity validation utilities (domain-agnostic).

**Usage:**
```python
from custom_components.autolock.helpers.entity_validation import (
    validate_entity_exists,
    validate_entity_domain,
    validate_entity_state,
)

if validate_entity_domain(hass, "lock.front_door", "lock"):
    # Entity is a valid lock
    pass
```

**Features:**
- Entity existence checks
- Domain validation
- State validation
- Availability checks

### EntityFactory (`entity_factory.py`)

Generic factory for creating HA entities (helpers, scripts, automations).

**Usage:**
```python
from custom_components.autolock.helpers import EntityFactory

factory = EntityFactory()

await factory.create_input_boolean(
    hass,
    "input_boolean.my_helper",
    "My Helper",
    initial_state=True,
)
```

**Features:**
- Create input_boolean helpers
- Create input_datetime helpers
- Create timers
- Generate YAML for scripts and automations

## Copying Helpers to Other Integrations

1. Copy the entire `helpers/` directory to your integration
2. Update imports: `from .helpers import ...`
3. No other changes needed - helpers are self-contained

## Moving to Shared Core Integration

1. Create `custom_components/ha_helpers/` (or similar)
2. Move `helpers/` contents there
3. Update imports: `from custom_components.ha_helpers import ...`
4. Other integrations can depend on shared core

## Requirements

- Python 3.12+
- Home Assistant 2026.1+
- No additional dependencies (uses only HA core APIs)

