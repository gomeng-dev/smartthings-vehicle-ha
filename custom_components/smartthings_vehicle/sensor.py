from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfLength, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import build_entity_id
from .coordinator import SmartThingsVehicleCoordinator


@dataclass(frozen=True, kw_only=True)
class SmartThingsVehicleSensorDescription(SensorEntityDescription):
    value_fn: Callable[[SmartThingsVehicleCoordinator], Any]
    attr_fn: Callable[[SmartThingsVehicleCoordinator], dict[str, Any] | None] | None = None
    required_capability: str | None = None
    required_attribute: str | None = None


def _status_value(attribute: str) -> Callable[[SmartThingsVehicleCoordinator], Any]:
    def value(coordinator: SmartThingsVehicleCoordinator) -> Any:
        if coordinator.data is None:
            return None
        return getattr(coordinator.data, attribute)

    return value


def _is_sensor_supported(
    coordinator: SmartThingsVehicleCoordinator,
    description: SmartThingsVehicleSensorDescription,
) -> bool:
    if description.required_capability is None or description.required_attribute is None:
        return True
    if coordinator.data is None:
        return False
    return coordinator.data.supports_attribute(
        description.required_capability,
        description.required_attribute,
    )


SENSORS: tuple[SmartThingsVehicleSensorDescription, ...] = (
    SmartThingsVehicleSensorDescription(
        key="range_km",
        translation_key="range_km",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        device_class=SensorDeviceClass.DISTANCE,
        value_fn=_status_value("range_km"),
        required_capability="vehicleRange",
        required_attribute="estimatedRemainingRange",
    ),
    SmartThingsVehicleSensorDescription(
        key="odometer_km",
        translation_key="odometer_km",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        device_class=SensorDeviceClass.DISTANCE,
        value_fn=_status_value("odometer_km"),
        required_capability="vehicleOdometer",
        required_attribute="odometerReading",
    ),
    SmartThingsVehicleSensorDescription(
        key="engine_state",
        translation_key="engine_state",
        value_fn=_status_value("engine_state"),
        required_capability="vehicleEngine",
        required_attribute="engineState",
    ),
    SmartThingsVehicleSensorDescription(
        key="hvac_state",
        translation_key="hvac_state",
        value_fn=_status_value("hvac_state"),
        required_capability="vehicleHvac",
        required_attribute="hvacState",
    ),
    SmartThingsVehicleSensorDescription(
        key="hvac_speed",
        translation_key="hvac_speed",
        value_fn=_status_value("hvac_speed"),
        required_capability="vehicleHvac",
        required_attribute="hvacSpeed",
    ),
    SmartThingsVehicleSensorDescription(
        key="defog_state",
        translation_key="defog_state",
        value_fn=_status_value("defog_state"),
        required_capability="vehicleHvac",
        required_attribute="defogState",
    ),
    SmartThingsVehicleSensorDescription(
        key="cabin_temperature",
        translation_key="cabin_temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        value_fn=_status_value("cabin_temperature"),
        required_capability="vehicleHvac",
        required_attribute="temperature",
    ),
    SmartThingsVehicleSensorDescription(
        key="lock_state",
        translation_key="lock_state",
        value_fn=_status_value("lock_state"),
        required_capability="vehicleDoorState",
        required_attribute="lockState",
    ),
    SmartThingsVehicleSensorDescription(
        key="front_left_door",
        translation_key="front_left_door",
        value_fn=_status_value("front_left_door"),
        required_capability="vehicleDoorState",
        required_attribute="frontLeftDoor",
    ),
    SmartThingsVehicleSensorDescription(
        key="front_right_door",
        translation_key="front_right_door",
        value_fn=_status_value("front_right_door"),
        required_capability="vehicleDoorState",
        required_attribute="frontRightDoor",
    ),
    SmartThingsVehicleSensorDescription(
        key="rear_left_door",
        translation_key="rear_left_door",
        value_fn=_status_value("rear_left_door"),
        required_capability="vehicleDoorState",
        required_attribute="rearLeftDoor",
    ),
    SmartThingsVehicleSensorDescription(
        key="rear_right_door",
        translation_key="rear_right_door",
        value_fn=_status_value("rear_right_door"),
        required_capability="vehicleDoorState",
        required_attribute="rearRightDoor",
    ),
    SmartThingsVehicleSensorDescription(
        key="front_left_window",
        translation_key="front_left_window",
        value_fn=_status_value("front_left_window"),
        required_capability="vehicleWindowState",
        required_attribute="frontLeftWindow",
    ),
    SmartThingsVehicleSensorDescription(
        key="front_right_window",
        translation_key="front_right_window",
        value_fn=_status_value("front_right_window"),
        required_capability="vehicleWindowState",
        required_attribute="frontRightWindow",
    ),
    SmartThingsVehicleSensorDescription(
        key="rear_left_window",
        translation_key="rear_left_window",
        value_fn=_status_value("rear_left_window"),
        required_capability="vehicleWindowState",
        required_attribute="rearLeftWindow",
    ),
    SmartThingsVehicleSensorDescription(
        key="rear_right_window",
        translation_key="rear_right_window",
        value_fn=_status_value("rear_right_window"),
        required_capability="vehicleWindowState",
        required_attribute="rearRightWindow",
    ),
    SmartThingsVehicleSensorDescription(
        key="fuel_warning",
        translation_key="fuel_warning",
        value_fn=_status_value("fuel_warning"),
        required_capability="vehicleWarning",
        required_attribute="fuel",
    ),
    SmartThingsVehicleSensorDescription(
        key="smart_key_battery",
        translation_key="smart_key_battery",
        value_fn=_status_value("smart_key_battery"),
        required_capability="vehicleWarning",
        required_attribute="smartKeyBattery",
    ),
    SmartThingsVehicleSensorDescription(
        key="tire_pressure_warning",
        translation_key="tire_pressure_warning",
        value_fn=_status_value("tire_pressure_warning"),
        required_capability="vehicleWarning",
        required_attribute="tirePressureFrontLeft",
    ),
    SmartThingsVehicleSensorDescription(
        key="tire_pressure_front_left",
        translation_key="tire_pressure_front_left",
        value_fn=_status_value("tire_pressure_front_left"),
        required_capability="vehicleWarning",
        required_attribute="tirePressureFrontLeft",
    ),
    SmartThingsVehicleSensorDescription(
        key="tire_pressure_front_right",
        translation_key="tire_pressure_front_right",
        value_fn=_status_value("tire_pressure_front_right"),
        required_capability="vehicleWarning",
        required_attribute="tirePressureFrontRight",
    ),
    SmartThingsVehicleSensorDescription(
        key="tire_pressure_rear_left",
        translation_key="tire_pressure_rear_left",
        value_fn=_status_value("tire_pressure_rear_left"),
        required_capability="vehicleWarning",
        required_attribute="tirePressureRearLeft",
    ),
    SmartThingsVehicleSensorDescription(
        key="tire_pressure_rear_right",
        translation_key="tire_pressure_rear_right",
        value_fn=_status_value("tire_pressure_rear_right"),
        required_capability="vehicleWarning",
        required_attribute="tirePressureRearRight",
    ),
    SmartThingsVehicleSensorDescription(
        key="lamp_wire_warning",
        translation_key="lamp_wire_warning",
        value_fn=_status_value("lamp_wire_warning"),
        required_capability="vehicleWarning",
        required_attribute="lampWire",
    ),
    SmartThingsVehicleSensorDescription(
        key="washer_fluid_warning",
        translation_key="washer_fluid_warning",
        value_fn=_status_value("washer_fluid_warning"),
        required_capability="vehicleWarning",
        required_attribute="washerFluid",
    ),
    SmartThingsVehicleSensorDescription(
        key="brake_fluid_warning",
        translation_key="brake_fluid_warning",
        value_fn=_status_value("brake_fluid_warning"),
        required_capability="vehicleWarning",
        required_attribute="brakeFluid",
    ),
    SmartThingsVehicleSensorDescription(
        key="engine_oil_warning",
        translation_key="engine_oil_warning",
        value_fn=_status_value("engine_oil_warning"),
        required_capability="vehicleWarning",
        required_attribute="engineOil",
    ),
    SmartThingsVehicleSensorDescription(
        key="ev_battery_level",
        translation_key="ev_battery_level",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        value_fn=_status_value("ev_battery_level"),
        required_capability="vehicleBattery",
        required_attribute="batteryLevel",
    ),
    SmartThingsVehicleSensorDescription(
        key="charging_state",
        translation_key="charging_state",
        value_fn=_status_value("charging_state"),
        required_capability="vehicleBattery",
        required_attribute="chargingState",
    ),
    SmartThingsVehicleSensorDescription(
        key="charging_detail",
        translation_key="charging_detail",
        value_fn=_status_value("charging_detail"),
        required_capability="vehicleBattery",
        required_attribute="chargingDetail",
    ),
    SmartThingsVehicleSensorDescription(
        key="charging_plug",
        translation_key="charging_plug",
        value_fn=_status_value("charging_plug"),
        required_capability="vehicleBattery",
        required_attribute="chargingPlug",
    ),
    SmartThingsVehicleSensorDescription(
        key="auxiliary_battery_warning",
        translation_key="auxiliary_battery_warning",
        value_fn=_status_value("auxiliary_battery_warning"),
        required_capability="vehicleWarning",
        required_attribute="auxiliaryBattery",
    ),
    SmartThingsVehicleSensorDescription(
        key="electric_vehicle_battery_warning",
        translation_key="electric_vehicle_battery_warning",
        value_fn=_status_value("electric_vehicle_battery_warning"),
        required_capability="vehicleWarning",
        required_attribute="electricVehicleBattery",
    ),
    SmartThingsVehicleSensorDescription(
        key="health",
        translation_key="health",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_status_value("health"),
        required_capability="healthCheck",
        required_attribute="DeviceWatch-DeviceStatus",
    ),
    SmartThingsVehicleSensorDescription(
        key="command_state",
        translation_key="command_state",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda coordinator: coordinator.command_status.state,
        attr_fn=lambda coordinator: coordinator.command_status.as_attributes(),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: SmartThingsVehicleCoordinator = entry.runtime_data
    async_add_entities(
        SmartThingsVehicleSensor(coordinator, description)
        for description in SENSORS
        if _is_sensor_supported(coordinator, description)
    )


class SmartThingsVehicleSensor(CoordinatorEntity[SmartThingsVehicleCoordinator], SensorEntity):
    entity_description: SmartThingsVehicleSensorDescription
    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        coordinator: SmartThingsVehicleCoordinator,
        description: SmartThingsVehicleSensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.client.device_id}_{description.key}"
        self.entity_id = build_entity_id("sensor", description.key)
        self._attr_device_info = coordinator.device_info

    @property
    def native_value(self) -> Any:
        return self.entity_description.value_fn(self.coordinator)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        if self.entity_description.attr_fn is None:
            return None
        return self.entity_description.attr_fn(self.coordinator)
