from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import build_entity_id
from .coordinator import SmartThingsVehicleCoordinator


@dataclass(frozen=True, kw_only=True)
class SmartThingsVehicleSwitchDescription(SwitchEntityDescription):
    value_fn: Callable[[SmartThingsVehicleCoordinator], bool | None]
    turn_on_fn: Callable[[SmartThingsVehicleCoordinator], Awaitable[None]]
    turn_off_fn: Callable[[SmartThingsVehicleCoordinator], Awaitable[None]]


SWITCHES: tuple[SmartThingsVehicleSwitchDescription, ...] = (
    SmartThingsVehicleSwitchDescription(
        key="hvac",
        translation_key="hvac",
        value_fn=lambda coordinator: coordinator.is_hvac_on,
        turn_on_fn=lambda coordinator: coordinator.async_turn_hvac_on(),
        turn_off_fn=lambda coordinator: coordinator.async_turn_hvac_off(),
    ),
    SmartThingsVehicleSwitchDescription(
        key="hvac_defog",
        translation_key="hvac_defog",
        entity_category=EntityCategory.CONFIG,
        value_fn=lambda coordinator: coordinator.hvac_settings.defog == "on",
        turn_on_fn=lambda coordinator: coordinator.async_set_hvac_defog_on(),
        turn_off_fn=lambda coordinator: coordinator.async_set_hvac_defog_off(),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: SmartThingsVehicleCoordinator = entry.runtime_data
    async_add_entities(
        SmartThingsVehicleSwitch(coordinator, description) for description in SWITCHES
    )


class SmartThingsVehicleSwitch(CoordinatorEntity[SmartThingsVehicleCoordinator], SwitchEntity):
    entity_description: SmartThingsVehicleSwitchDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: SmartThingsVehicleCoordinator,
        description: SmartThingsVehicleSwitchDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.client.device_id}_{description.key}"
        self.entity_id = build_entity_id("switch", description.key)
        self._attr_device_info = coordinator.device_info

    @property
    def is_on(self) -> bool | None:
        return self.entity_description.value_fn(self.coordinator)

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.entity_description.turn_on_fn(self.coordinator)
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.entity_description.turn_off_fn(self.coordinator)
        self.async_write_ha_state()
