from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant

from .coordinator import SmartThingsVehicleCoordinator
from .diagnostics_data import build_vehicle_diagnostics, extract_device_capability_ids
from .vehicle import SmartThingsApiError


async def _async_build_entry_diagnostics(entry: Any) -> dict[str, Any]:
    coordinator: SmartThingsVehicleCoordinator = entry.runtime_data
    device_payload, status_payload = await coordinator.async_get_diagnostics_payloads()

    definitions: dict[str, dict[str, Any]] = {}
    unavailable: list[str] = []
    for capability_id in extract_device_capability_ids(device_payload):
        try:
            definitions[capability_id] = (
                await coordinator.async_get_capability_definition(capability_id)
            )
        except SmartThingsApiError:
            unavailable.append(capability_id)

    return build_vehicle_diagnostics(
        device_payload,
        status_payload,
        definitions,
        unavailable,
    )


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    entry: Any,
) -> dict[str, Any]:
    """Return sanitized diagnostics for the configured SmartThings vehicle."""

    return await _async_build_entry_diagnostics(entry)


async def async_get_device_diagnostics(
    hass: HomeAssistant,
    entry: Any,
    device: Any,
) -> dict[str, Any]:
    """Return sanitized diagnostics for the configured SmartThings vehicle."""

    return await _async_build_entry_diagnostics(entry)
