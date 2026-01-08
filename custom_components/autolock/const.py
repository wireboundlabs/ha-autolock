"""Constants for the AutoLock integration."""

from __future__ import annotations

from typing import Final

# Domain
DOMAIN: Final = "autolock"

# Entity ID templates
AUTOLOCK_ENABLED_TEMPLATE: Final = "input_boolean.autolock_{door_id}_enabled"
AUTOLOCK_SNOOZE_TEMPLATE: Final = "input_datetime.autolock_{door_id}_snooze_until"
AUTOLOCK_TIMER_TEMPLATE: Final = "timer.autolock_{door_id}_delay"
AUTOLOCK_SCRIPT_TEMPLATE: Final = "script.autolock_{door_id}_lock"
AUTOLOCK_AUTOMATION_TEMPLATE: Final = "automation.autolock_{door_id}"

# Default values
DEFAULT_DAY_DELAY: Final = 5  # minutes
DEFAULT_NIGHT_DELAY: Final = 2  # minutes
DEFAULT_RETRY_COUNT: Final = 3
DEFAULT_RETRY_DELAY: Final = 5  # seconds
DEFAULT_VERIFICATION_DELAY: Final = 5  # seconds
DEFAULT_ENABLE_ON_CREATION: Final = True

# Validation ranges
MIN_DAY_DELAY: Final = 1
MAX_DAY_DELAY: Final = 240
MIN_NIGHT_DELAY: Final = 1
MAX_NIGHT_DELAY: Final = 30
MIN_RETRY_COUNT: Final = 0
MAX_RETRY_COUNT: Final = 5
MIN_RETRY_DELAY: Final = 3
MAX_RETRY_DELAY: Final = 60
MIN_VERIFICATION_DELAY: Final = 2
MAX_VERIFICATION_DELAY: Final = 10

# Lock states
LOCK_STATE_LOCKED: Final = "locked"
LOCK_STATE_UNLOCKED: Final = "unlocked"
LOCK_STATE_JAMMED: Final = "jammed"
LOCK_STATE_UNKNOWN: Final = "unknown"

# Snooze durations (minutes)
SNOOZE_DURATION_15: Final = 15
SNOOZE_DURATION_30: Final = 30
SNOOZE_DURATION_60: Final = 60

# Notification
NOTIFICATION_ID_TEMPLATE: Final = "autolock_{door_id}_failure"
