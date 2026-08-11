from __future__ import annotations

import logging
from typing import Any

from .const import CONF_DEVICE_ID, PLATFORMS, removed_entity_unique_ids

_LOGGER = logging.getLogger(__name__)


def _remove_matching_entities(
    registry: Any,
    registry_entries: list[Any],
    obsolete_unique_ids: frozenset[str],
) -> int:
    """Remove matching entity-registry entries and return the removal count."""

    removed = 0
    for registry_entry in registry_entries:
        if registry_entry.unique_id not in obsolete_unique_ids:
            continue
        registry.async_remove(registry_entry.entity_id)
        removed += 1
    return removed


def _remove_obsolete_entities(hass: Any, entry: Any) -> None:
    """Remove entities retired by the integration from Home Assistant's registry."""

    from homeassistant.helpers import entity_registry as er

    device_id = entry.data.get(CONF_DEVICE_ID)
    if not isinstance(device_id, str) or not device_id:
        return

    obsolete_unique_ids = removed_entity_unique_ids(device_id)
    registry = er.async_get(hass)
    removed = _remove_matching_entities(
        registry,
        er.async_entries_for_config_entry(registry, entry.entry_id),
        obsolete_unique_ids,
    )

    if removed:
        _LOGGER.info("Removed %s obsolete SmartThings vehicle entities", removed)


async def async_setup_entry(hass: Any, entry: Any) -> bool:
    from .coordinator import SmartThingsVehicleCoordinator

    _remove_obsolete_entities(hass, entry)
    coordinator = SmartThingsVehicleCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: Any, entry: Any) -> bool:
    coordinator = getattr(entry, "runtime_data", None)
    if coordinator is not None and hasattr(coordinator, "async_shutdown"):
        coordinator.async_shutdown()
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
