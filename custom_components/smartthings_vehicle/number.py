from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.number import NumberEntity, NumberEntityDescription, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import build_entity_id
from .coordinator import SmartThingsVehicleCoordinator
from .hvac import (
    HVAC_IGNITION_DURATION_MAX,
    HVAC_IGNITION_DURATION_MIN,
    HVAC_IGNITION_DURATION_STEP,
    HVAC_TEMPERATURE_MAX,
    HVAC_TEMPERATURE_MIN,
    HVAC_TEMPERATURE_STEP,
    HvacSettings,
)


@dataclass(frozen=True, kw_only=True)
class SmartThingsVehicleNumberDescription(NumberEntityDescription):
    value_fn: Callable[[HvacSettings], float | int]
    set_fn: Callable[[SmartThingsVehicleCoordinator, float], None]


NUMBERS: tuple[SmartThingsVehicleNumberDescription, ...] = (
    SmartThingsVehicleNumberDescription(
        key="hvac_temperature",
        translation_key="hvac_temperature",
        entity_category=EntityCategory.CONFIG,
        native_min_value=HVAC_TEMPERATURE_MIN,
        native_max_value=HVAC_TEMPERATURE_MAX,
        native_step=HVAC_TEMPERATURE_STEP,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        mode=NumberMode.SLIDER,
        value_fn=lambda settings: settings.temperature,
        set_fn=lambda coordinator, value: coordinator.set_hvac_temperature(value),
    ),
    SmartThingsVehicleNumberDescription(
        key="hvac_ignition_duration",
        translation_key="hvac_ignition_duration",
        entity_category=EntityCategory.CONFIG,
        native_min_value=HVAC_IGNITION_DURATION_MIN,
        native_max_value=HVAC_IGNITION_DURATION_MAX,
        native_step=HVAC_IGNITION_DURATION_STEP,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        mode=NumberMode.SLIDER,
        value_fn=lambda settings: settings.ignition_duration,
        set_fn=lambda coordinator, value: coordinator.set_hvac_ignition_duration(value),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: SmartThingsVehicleCoordinator = entry.runtime_data
    async_add_entities(
        SmartThingsVehicleNumber(coordinator, description) for description in NUMBERS
    )


class SmartThingsVehicleNumber(CoordinatorEntity[SmartThingsVehicleCoordinator], NumberEntity):
    entity_description: SmartThingsVehicleNumberDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: SmartThingsVehicleCoordinator,
        description: SmartThingsVehicleNumberDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.client.device_id}_{description.key}"
        self.entity_id = build_entity_id("number", description.key)
        self._attr_device_info = coordinator.device_info

    @property
    def native_value(self) -> Any:
        return self.entity_description.value_fn(self.coordinator.hvac_settings)

    async def async_set_native_value(self, value: float) -> None:
        self.entity_description.set_fn(self.coordinator, value)
        self.async_write_ha_state()
