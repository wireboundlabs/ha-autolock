"""Generic entity validation utilities for Home Assistant integrations.

This module provides reusable entity validation functions that can be used
by any integration needing to validate entities (domain-agnostic).
"""
from __future__ import annotations

import logging

from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)


def validate_entity_exists(hass: HomeAssistant, entity_id: str) -> bool:
    """Validate that an entity exists.

    Args:
        hass: Home Assistant instance
        entity_id: Entity ID to validate

    Returns:
        True if entity exists, False otherwise
    """
    if not entity_id:
        return False

    # Check if entity exists in state machine
    state = hass.states.get(entity_id)
    if state is None:
        _LOGGER.debug("Entity %s does not exist", entity_id)
        return False

    return True


def validate_entity_domain(
    hass: HomeAssistant,
    entity_id: str,
    domain: str,
) -> bool:
    """Validate that an entity belongs to a specific domain.

    Args:
        hass: Home Assistant instance
        entity_id: Entity ID to validate
        domain: Expected domain (e.g., "lock", "binary_sensor")

    Returns:
        True if entity belongs to domain, False otherwise
    """
    if not validate_entity_exists(hass, entity_id):
        return False

    # Extract domain from entity_id (format: domain.entity_name)
    entity_domain = entity_id.split(".", 1)[0] if "." in entity_id else None

    if entity_domain != domain:
        _LOGGER.debug(
            "Entity %s does not belong to domain %s (found: %s)",
            entity_id,
            domain,
            entity_domain,
        )
        return False

    return True


def validate_entity_state(
    hass: HomeAssistant,
    entity_id: str,
    valid_states: list[str],
) -> bool:
    """Validate that an entity is in one of the valid states.

    Args:
        hass: Home Assistant instance
        entity_id: Entity ID to validate
        valid_states: List of valid state values

    Returns:
        True if entity is in a valid state, False otherwise
    """
    if not validate_entity_exists(hass, entity_id):
        return False

    state = hass.states.get(entity_id)
    if state is None:
        return False

    entity_state = state.state
    if entity_state not in valid_states:
        _LOGGER.debug(
            "Entity %s is not in valid states %s (current: %s)",
            entity_id,
            valid_states,
            entity_state,
        )
        return False

    return True


def validate_entity_available(hass: HomeAssistant, entity_id: str) -> bool:
    """Validate that an entity is available (not unavailable/unknown).

    Args:
        hass: Home Assistant instance
        entity_id: Entity ID to validate

    Returns:
        True if entity is available, False otherwise
    """
    if not validate_entity_exists(hass, entity_id):
        return False

    state = hass.states.get(entity_id)
    if state is None:
        return False

    entity_state = state.state
    unavailable_states = {"unavailable", "unknown", "None"}

    if entity_state in unavailable_states:
        _LOGGER.debug(
            "Entity %s is not available (state: %s)",
            entity_id,
            entity_state,
        )
        return False

    return True


def get_entity_domain(hass: HomeAssistant, entity_id: str) -> str | None:
    """Get the domain of an entity.

    Args:
        hass: Home Assistant instance
        entity_id: Entity ID

    Returns:
        Domain name if found, None otherwise
    """
    if not entity_id or "." not in entity_id:
        return None

    return entity_id.split(".", 1)[0]

