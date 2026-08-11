from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import build_entity_id
from .coordinator import SmartThingsVehicleCoordinator
from .hvac import (
    HVAC_DEFOG_OPTIONS,
    HVAC_IGNITION_DURATION_MAX,
    HVAC_IGNITION_DURATION_MIN,
    HvacSettings,
)

_DURATION_OPTIONS = tuple(
    f"{minutes}분"
    for minutes in range(HVAC_IGNITION_DURATION_MIN, HVAC_IGNITION_DURATION_MAX + 1)
)


def _duration_to_option(settings: HvacSettings) -> str:
    return f"{settings.ignition_duration}분"


def _option_to_duration(option: str) -> int:
    return int(option.removesuffix("분"))


@dataclass(frozen=True, kw_only=True)
class SmartThingsVehicleSelectDescription(SelectEntityDescription):
    value_fn: Callable[[HvacSettings], str]
    set_fn: Callable[[SmartThingsVehicleCoordinator, str], None]


SELECTS: tuple[SmartThingsVehicleSelectDescription, ...] = (
    SmartThingsVehicleSelectDescription(
        key="hvac_defog",
        translation_key="hvac_defog",
        entity_category=EntityCategory.CONFIG,
        options=list(HVAC_DEFOG_OPTIONS),
        value_fn=lambda settings: settings.defog,
        set_fn=lambda coordinator, option: coordinator.set_hvac_defog(option),
    ),
    SmartThingsVehicleSelectDescription(
        key="hvac_ignition_duration_select",
        translation_key="hvac_ignition_duration",
        entity_category=EntityCategory.CONFIG,
        options=list(_DURATION_OPTIONS),
        value_fn=_duration_to_option,
        set_fn=lambda coordinator, option: coordinator.set_hvac_ignition_duration(
            _option_to_duration(option)
        ),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: SmartThingsVehicleCoordinator = entry.runtime_data
    async_add_entities(
        SmartThingsVehicleSelect(coordinator, description) for description in SELECTS
    )


class SmartThingsVehicleSelect(CoordinatorEntity[SmartThingsVehicleCoordinator], SelectEntity):
    entity_description: SmartThingsVehicleSelectDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: SmartThingsVehicleCoordinator,
        description: SmartThingsVehicleSelectDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.client.device_id}_{description.key}"
        if description.key == "hvac_ignition_duration_select":
            self.entity_id = build_entity_id("select", "hvac_ignition_duration")
        else:
            self.entity_id = build_entity_id("select", description.key)
        self._attr_device_info = coordinator.device_info

    @property
    def current_option(self) -> str:
        return self.entity_description.value_fn(self.coordinator.hvac_settings)

    async def async_select_option(self, option: str) -> None:
        self.entity_description.set_fn(self.coordinator, option)
        self.async_write_ha_state()
