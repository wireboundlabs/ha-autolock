# Home Assistant AutoLock Integration

[![CI](https://github.com/wirebound-labs/ha-autolock/workflows/CI/badge.svg)](https://github.com/wirebound-labs/ha-autolock/actions)
[![Coverage](https://codecov.io/gh/wirebound-labs/ha-autolock/branch/main/graph/badge.svg)](https://codecov.io/gh/wirebound-labs/ha-autolock)
[![hacs](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![ha-core](https://img.shields.io/badge/Home%20Assistant-2025.1.4%2B-blue.svg)](https://www.home-assistant.io/)
[![python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)

Automatically lock doors after they close with configurable day/night delays, retry logic, and safety checks.

## Features

- **Multi-door support**: Configure separate auto-lock settings for each door
- **Day/night schedules**: Different delay times for day and night
- **Safety checks**: Only locks if door is closed and lock is unlocked
- **Retry logic**: Configurable retries with exponential backoff
- **Lock verification**: Verifies lock actually locked after service call
- **Failure notifications**: Persistent and push notifications on lock failures
- **Enable/disable per door**: Control each door independently
- **Snooze functionality**: Temporarily disable auto-lock (15/30/60 minutes)
- **Manual lock service**: Lock now service with verification

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Go to Integrations
3. Click the three dots menu → Custom repositories
4. Add repository: `https://github.com/wirebound-labs/ha-autolock`
5. Select category: Integration
6. Click Install
7. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/autolock` directory to your `custom_components` folder
2. Restart Home Assistant
3. Add integration via Settings → Devices & Services → Add Integration

## Configuration

### Via UI (Config Flow)

1. Go to Settings → Devices & Services → Add Integration
2. Search for "AutoLock"
3. Follow the setup wizard:
   - **Step 1**: Enter door name and select lock entity
   - **Step 2**: (Optional) Select door sensor entity
   - **Step 3**: Configure timing (day/night delays and schedule)
   - **Step 4**: Configure retry settings
   - **Step 5**: Review and confirm

### Configuration Options

- **Door Name**: Friendly name for the door
- **Lock Entity**: Lock entity to control
- **Sensor Entity** (Optional): Binary sensor that detects door closed
- **Day Delay**: Minutes to wait before locking during day (1-240)
- **Night Delay**: Minutes to wait before locking during night (1-30)
- **Night Schedule**: Start and end times for night schedule (supports midnight crossing)
- **Retry Count**: Number of retry attempts if lock fails (0-5)
- **Retry Delay**: Seconds between retries (3-60)
- **Verification Delay**: Seconds to wait after lock call before verifying (2-10)

## Usage

### Services

- `autolock.lock_now`: Lock door immediately with verification
  ```yaml
  service: autolock.lock_now
  data:
    door_id: front_door
  ```

- `autolock.snooze`: Snooze auto-lock for specified duration
  ```yaml
  service: autolock.snooze
  data:
    door_id: front_door
    duration: 30  # 15, 30, or 60 minutes
  ```

- `autolock.enable`: Enable auto-lock for a door
  ```yaml
  service: autolock.enable
  data:
    door_id: front_door
  ```

- `autolock.disable`: Disable auto-lock for a door
  ```yaml
  service: autolock.disable
  data:
    door_id: front_door
  ```

### Helpers

Each door creates the following helpers:
- `input_boolean.autolock_{door_id}_enabled`: Enable/disable switch
- `input_datetime.autolock_{door_id}_snooze_until`: Snooze state
- `timer.autolock_{door_id}_delay`: Countdown timer

## How It Works

1. **Trigger**: Door closes (sensor) or lock becomes unlocked (fallback)
2. **Safety Check**: Verifies door is closed (if sensor) and lock is unlocked
3. **Timer Start**: Starts countdown timer based on day/night schedule
4. **Timer Restart**: Any close/unlock event while timer is running restarts it
5. **Lock Attempt**: When timer finishes, attempts to lock
6. **Verification**: Waits and verifies lock actually locked
7. **Retry**: If lock fails, retries up to configured count
8. **Notification**: Sends notification if all retries fail

## Troubleshooting

### Lock Fails to Lock

- Check lock integration status
- Verify lock entity is available
- Check for cloud authentication issues
- Review Home Assistant logs for errors

### Timer Doesn't Start

- Verify door sensor is working (if configured)
- Check that door is enabled (`input_boolean.autolock_*_enabled`)
- Ensure door is not snoozed

### Notifications Not Received

- Check persistent notifications in Home Assistant UI
- Verify notify service is configured for push notifications
- Check Home Assistant logs for notification errors

## Requirements

- Home Assistant 2025.1.4 or later
- Python 3.12 or later
- Lock entity (lock domain)
- Optional: Binary sensor for door state

## Development

### Setup

```bash
pip install -r requirements_dev.txt
pre-commit install
```

### Running Tests

```bash
pytest
pytest --cov=custom_components/autolock --cov-report=html
```

### Linting

```bash
ruff check .
ruff format .
mypy custom_components/autolock
```

## License

MIT License

## Support

- [Issue Tracker](https://github.com/wirebound-labs/ha-autolock/issues)
- [Documentation](https://github.com/wirebound-labs/ha-autolock)

## Contributing

Contributions are welcome! Please open an issue or pull request.

