from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field, replace
from time import monotonic
from typing import Any
from urllib.parse import quote

API_BASE_URL = "https://api.smartthings.com/v1"


class SmartThingsApiError(RuntimeError):
    """Raised when SmartThings vehicle API data or commands are invalid."""


class SmartThingsUnauthorizedError(SmartThingsApiError):
    """Raised when SmartThings rejects the current OAuth access token."""


@dataclass(frozen=True, slots=True)
class SmartThingsTokenInfo:
    access_token: str
    expires_at: float | None = None


@dataclass(frozen=True, slots=True)
class VehicleStatus:
    range_km: float | int | None = None
    odometer_km: float | int | None = None
    engine_state: str | None = None
    hvac_state: str | None = None
    hvac_speed: int | None = None
    defog_state: str | None = None
    cabin_temperature: float | int | None = None
    cabin_temperature_unit: str | None = None
    lock_state: str | None = None
    front_left_door: str | None = None
    front_right_door: str | None = None
    rear_left_door: str | None = None
    rear_right_door: str | None = None
    front_left_window: str | None = None
    front_right_window: str | None = None
    rear_left_window: str | None = None
    rear_right_window: str | None = None
    fuel_warning: str | None = None
    smart_key_battery: str | None = None
    tire_pressure_warning: str | None = None
    tire_pressure_front_left: str | None = None
    tire_pressure_front_right: str | None = None
    tire_pressure_rear_left: str | None = None
    tire_pressure_rear_right: str | None = None
    lamp_wire_warning: str | None = None
    washer_fluid_warning: str | None = None
    brake_fluid_warning: str | None = None
    engine_oil_warning: str | None = None
    ev_battery_level: float | int | None = None
    charging_state: str | None = None
    charging_plug: str | None = None
    charging_detail: str | None = None
    auxiliary_battery_warning: str | None = None
    electric_vehicle_battery_warning: str | None = None
    health: str | None = None
    available_capabilities: frozenset[str] = field(
        default_factory=frozenset,
        compare=False,
        repr=False,
    )
    available_attributes: frozenset[str] = field(
        default_factory=frozenset,
        compare=False,
        repr=False,
    )

    def as_dict(self) -> dict[str, Any]:
        return {
            field_name: getattr(self, field_name)
            for field_name in self.__dataclass_fields__
            if field_name not in {"available_capabilities", "available_attributes"}
            and getattr(self, field_name) is not None
        }

    def supports_attribute(self, capability: str, attribute: str) -> bool:
        """Return whether SmartThings reported an attribute for this vehicle."""

        return f"{capability}.{attribute}" in self.available_attributes


@dataclass(frozen=True, slots=True)
class VehicleCommandResult:
    accepted: bool
    command_id: str | None
    raw: dict[str, Any]


@dataclass(frozen=True, slots=True)
class VehicleCommandStatus:
    state: str
    last_command: str | None = None
    target: str | None = None
    command_id: str | None = None
    started_at: float | None = None
    completed_at: float | None = None
    last_error: str | None = None

    @classmethod
    def idle(cls) -> VehicleCommandStatus:
        return cls(state="idle")

    def mark_pending(
        self,
        *,
        command: str,
        target: str | None,
        started_at: float,
    ) -> VehicleCommandStatus:
        return VehicleCommandStatus(
            state="pending",
            last_command=command,
            target=target,
            started_at=started_at,
        )

    def mark_accepted(self, command_id: str | None) -> VehicleCommandStatus:
        return replace(self, state="accepted", command_id=command_id)

    def mark_converged(self, *, completed_at: float) -> VehicleCommandStatus:
        return replace(self, state="converged", completed_at=completed_at)

    def mark_timeout(self, last_error: str, *, completed_at: float) -> VehicleCommandStatus:
        return replace(
            self,
            state="timeout",
            completed_at=completed_at,
            last_error=last_error,
        )

    def mark_failed(self, last_error: str, *, completed_at: float) -> VehicleCommandStatus:
        return replace(
            self,
            state="failed",
            completed_at=completed_at,
            last_error=last_error,
        )

    def as_attributes(self) -> dict[str, Any]:
        return {
            "last_command": self.last_command,
            "target": self.target,
            "command_id": self.command_id,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "last_error": self.last_error,
        }


@dataclass(frozen=True, slots=True)
class VehicleStatusConvergenceResult:
    converged: bool
    last_error: Exception | None = None


@dataclass(frozen=True, slots=True)
class VehicleDevice:
    device_id: str
    label: str
    manufacturer: str | None = None

    def as_dict(self) -> dict[str, str | None]:
        return {
            "device_id": self.device_id,
            "label": self.label,
            "manufacturer": self.manufacturer,
        }


def _main_component(payload: dict[str, Any]) -> dict[str, Any]:
    components = payload.get("components")
    if not isinstance(components, dict):
        return {}
    main = components.get("main")
    return main if isinstance(main, dict) else {}


def _nested_value(payload: dict[str, Any], capability: str, attribute: str) -> Any:
    main = _main_component(payload)
    capability_status = main.get(capability)
    if not isinstance(capability_status, dict):
        return None
    attribute_status = capability_status.get(attribute)
    if not isinstance(attribute_status, dict):
        return None
    return attribute_status.get("value")


def _nested_unit(payload: dict[str, Any], capability: str, attribute: str) -> str | None:
    main = _main_component(payload)
    capability_status = main.get(capability)
    if not isinstance(capability_status, dict):
        return None
    attribute_status = capability_status.get(attribute)
    if not isinstance(attribute_status, dict):
        return None
    unit = attribute_status.get("unit")
    return unit if isinstance(unit, str) else None


def _available_status_attributes(main: dict[str, Any]) -> frozenset[str]:
    attributes: set[str] = set()
    for capability, capability_status in main.items():
        if not isinstance(capability, str) or not isinstance(capability_status, dict):
            continue
        attributes.update(
            f"{capability}.{attribute}"
            for attribute in capability_status
            if isinstance(attribute, str)
        )
    return frozenset(attributes)


def _aggregate_warning(*values: Any) -> str | None:
    """Combine Hyundai per-position warnings into its public API warning state."""

    reported = [value for value in values if isinstance(value, str)]
    if not reported:
        return None
    if "warning" in reported:
        return "warning"
    if all(value == "normal" for value in reported):
        return "normal"
    return None


def _coerce_expires_at(value: Any) -> float | None:
    if isinstance(value, int | float):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    return None


def extract_token_info(data: dict[str, Any]) -> SmartThingsTokenInfo:
    """Extract a SmartThings OAuth access token and expiry from HA config-entry-like data."""

    direct = data.get("access_token") or data.get("accessToken")
    if isinstance(direct, str) and direct:
        return SmartThingsTokenInfo(
            access_token=direct,
            expires_at=_coerce_expires_at(data.get("expires_at") or data.get("expiresAt")),
        )

    for value in data.values():
        if isinstance(value, dict):
            token = value.get("access_token") or value.get("accessToken")
            if isinstance(token, str) and token:
                expires_at = value.get("expires_at") or value.get("expiresAt")
                return SmartThingsTokenInfo(
                    access_token=token,
                    expires_at=_coerce_expires_at(expires_at),
                )

    raise SmartThingsApiError("SmartThings access token was not found")


def extract_access_token(data: dict[str, Any]) -> str:
    """Extract a SmartThings OAuth access token from HA config-entry-like data."""

    return extract_token_info(data).access_token


def _device_has_vehicle_capability(device: dict[str, Any]) -> bool:
    components = device.get("components")
    if not isinstance(components, list):
        return False

    for component in components:
        capabilities = component.get("capabilities") if isinstance(component, dict) else None
        if not isinstance(capabilities, list):
            continue
        for capability in capabilities:
            if isinstance(capability, dict):
                capability_id = capability.get("id")
            else:
                capability_id = capability
            if isinstance(capability_id, str) and capability_id.startswith("vehicle"):
                return True
    return False


def discover_vehicle_devices(payload: dict[str, Any]) -> list[dict[str, str | None]]:
    """Return SmartThings devices that look like Hyundai/Kia/Genesis vehicle devices."""

    items = payload.get("items")
    if not isinstance(items, list):
        return []

    vehicles: list[VehicleDevice] = []
    for device in items:
        if not isinstance(device, dict) or not _device_has_vehicle_capability(device):
            continue
        device_id = device.get("deviceId") or device.get("device_id")
        if not isinstance(device_id, str) or not device_id:
            continue
        label = device.get("label") or device.get("name") or device_id
        manufacturer = device.get("manufacturerName") or device.get("manufacturer")
        vehicles.append(
            VehicleDevice(
                device_id=device_id,
                label=str(label),
                manufacturer=str(manufacturer) if manufacturer is not None else None,
            )
        )

    return [vehicle.as_dict() for vehicle in vehicles]


def parse_vehicle_status(payload: dict[str, Any]) -> VehicleStatus:
    """Map SmartThings `/status` JSON into a stable vehicle status dataclass."""

    main = _main_component(payload)
    tire_pressure_front_left = _nested_value(
        payload,
        "vehicleWarning",
        "tirePressureFrontLeft",
    )
    tire_pressure_front_right = _nested_value(
        payload,
        "vehicleWarning",
        "tirePressureFrontRight",
    )
    tire_pressure_rear_left = _nested_value(
        payload,
        "vehicleWarning",
        "tirePressureRearLeft",
    )
    tire_pressure_rear_right = _nested_value(
        payload,
        "vehicleWarning",
        "tirePressureRearRight",
    )
    return VehicleStatus(
        range_km=_nested_value(payload, "vehicleRange", "estimatedRemainingRange"),
        odometer_km=_nested_value(payload, "vehicleOdometer", "odometerReading"),
        engine_state=_nested_value(payload, "vehicleEngine", "engineState"),
        hvac_state=_nested_value(payload, "vehicleHvac", "hvacState"),
        hvac_speed=_nested_value(payload, "vehicleHvac", "hvacSpeed"),
        defog_state=_nested_value(payload, "vehicleHvac", "defogState"),
        cabin_temperature=_nested_value(payload, "vehicleHvac", "temperature"),
        cabin_temperature_unit=_nested_unit(payload, "vehicleHvac", "temperature"),
        lock_state=_nested_value(payload, "vehicleDoorState", "lockState"),
        front_left_door=_nested_value(payload, "vehicleDoorState", "frontLeftDoor"),
        front_right_door=_nested_value(payload, "vehicleDoorState", "frontRightDoor"),
        rear_left_door=_nested_value(payload, "vehicleDoorState", "rearLeftDoor"),
        rear_right_door=_nested_value(payload, "vehicleDoorState", "rearRightDoor"),
        front_left_window=_nested_value(payload, "vehicleWindowState", "frontLeftWindow"),
        front_right_window=_nested_value(payload, "vehicleWindowState", "frontRightWindow"),
        rear_left_window=_nested_value(payload, "vehicleWindowState", "rearLeftWindow"),
        rear_right_window=_nested_value(payload, "vehicleWindowState", "rearRightWindow"),
        fuel_warning=_nested_value(payload, "vehicleWarning", "fuel"),
        smart_key_battery=_nested_value(payload, "vehicleWarning", "smartKeyBattery"),
        tire_pressure_warning=_aggregate_warning(
            tire_pressure_front_left,
            tire_pressure_front_right,
            tire_pressure_rear_left,
            tire_pressure_rear_right,
        ),
        tire_pressure_front_left=tire_pressure_front_left,
        tire_pressure_front_right=tire_pressure_front_right,
        tire_pressure_rear_left=tire_pressure_rear_left,
        tire_pressure_rear_right=tire_pressure_rear_right,
        lamp_wire_warning=_nested_value(payload, "vehicleWarning", "lampWire"),
        washer_fluid_warning=_nested_value(payload, "vehicleWarning", "washerFluid"),
        brake_fluid_warning=_nested_value(payload, "vehicleWarning", "brakeFluid"),
        engine_oil_warning=_nested_value(payload, "vehicleWarning", "engineOil"),
        ev_battery_level=_nested_value(payload, "vehicleBattery", "batteryLevel"),
        charging_state=_nested_value(payload, "vehicleBattery", "chargingState"),
        charging_plug=_nested_value(payload, "vehicleBattery", "chargingPlug"),
        charging_detail=_nested_value(payload, "vehicleBattery", "chargingDetail"),
        auxiliary_battery_warning=_nested_value(
            payload,
            "vehicleWarning",
            "auxiliaryBattery",
        ),
        electric_vehicle_battery_warning=_nested_value(
            payload,
            "vehicleWarning",
            "electricVehicleBattery",
        ),
        health=_nested_value(payload, "healthCheck", "DeviceWatch-DeviceStatus"),
        available_capabilities=frozenset(main),
        available_attributes=_available_status_attributes(main),
    )


def parse_command_result(payload: dict[str, Any]) -> VehicleCommandResult:
    results = payload.get("results")
    if not isinstance(results, list) or not results:
        raise SmartThingsApiError("SmartThings command response had no results")

    first = results[0] or {}
    status = first.get("status")
    command_id = first.get("id")
    if status != "ACCEPTED":
        raise SmartThingsApiError(f"SmartThings command was not accepted: {status!r}")

    return VehicleCommandResult(accepted=True, command_id=command_id, raw=payload)


async def async_wait_for_vehicle_status(
    get_status: Callable[[], Awaitable[VehicleStatus]],
    predicate: Callable[[VehicleStatus], bool],
    update_status: Callable[[VehicleStatus], None],
    *,
    timeout_seconds: int,
    poll_seconds: int,
) -> VehicleStatusConvergenceResult:
    """Poll vehicle status until a SmartThings command reaches its target state."""

    deadline = monotonic() + timeout_seconds
    last_error: SmartThingsApiError | None = None

    while True:
        try:
            status = await get_status()
        except SmartThingsApiError as err:
            last_error = err
        else:
            update_status(status)
            if predicate(status):
                return VehicleStatusConvergenceResult(converged=True)

        remaining = deadline - monotonic()
        if remaining <= 0:
            return VehicleStatusConvergenceResult(
                converged=False,
                last_error=last_error,
            )
        await asyncio.sleep(min(poll_seconds, remaining))


class SmartThingsVehicleClient:
    """Tiny async client for the SmartThings vehicle REST endpoints."""

    def __init__(self, session: Any, access_token: str, device_id: str) -> None:
        self._session = session
        self._access_token = access_token
        self.device_id = device_id

    @property
    def access_token(self) -> str:
        return self._access_token

    def set_access_token(self, access_token: str) -> None:
        self._access_token = access_token

    @property
    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._access_token}",
            "Accept": "application/json",
        }

    async def async_list_devices(self) -> list[dict[str, str | None]]:
        payload = await self._request("GET", "/devices")
        return discover_vehicle_devices(payload)

    async def async_get_device(self) -> dict[str, Any]:
        return await self._request("GET", f"/devices/{self.device_id}")

    async def async_get_raw_status(self) -> dict[str, Any]:
        return await self._request("GET", f"/devices/{self.device_id}/status")

    async def async_get_status(self) -> VehicleStatus:
        payload = await self.async_get_raw_status()
        return parse_vehicle_status(payload)

    async def async_get_capability_definition(
        self,
        capability_id: str,
        version: int = 1,
    ) -> dict[str, Any]:
        encoded_capability_id = quote(capability_id, safe="")
        return await self._request(
            "GET",
            f"/capabilities/{encoded_capability_id}/{version}",
        )

    async def async_refresh(self) -> VehicleCommandResult:
        return await self.async_send_command("refresh", "refresh")

    async def async_ping(self) -> VehicleCommandResult:
        return await self.async_send_command("healthCheck", "ping")

    async def async_lock(self) -> VehicleCommandResult:
        return await self.async_send_command("vehicleDoorState", "lock")

    async def async_unlock(self) -> VehicleCommandResult:
        return await self.async_send_command("vehicleDoorState", "unlock")

    async def async_start_engine(self) -> VehicleCommandResult:
        return await self.async_send_command("vehicleEngine", "startEngine")

    async def async_stop_engine(self) -> VehicleCommandResult:
        return await self.async_send_command("vehicleEngine", "stopEngine")

    async def async_turn_hvac_on(
        self,
        *,
        temperature: float | int = 22,
        unit: str = "C",
        ignition_duration: int = 10,
        defog: str = "off",
    ) -> VehicleCommandResult:
        return await self.async_send_command(
            "vehicleHvacRemoteSwitch",
            "on",
            arguments=[
                {
                    "temperature": {"value": temperature, "unit": unit},
                    "ignitionDuration": ignition_duration,
                    "defog": defog,
                }
            ],
        )

    async def async_turn_hvac_off(self) -> VehicleCommandResult:
        return await self.async_send_command("vehicleHvacRemoteSwitch", "off")

    async def async_send_command(
        self,
        capability: str,
        command: str,
        *,
        arguments: list[Any] | None = None,
    ) -> VehicleCommandResult:
        payload = {
            "commands": [
                {
                    "component": "main",
                    "capability": capability,
                    "command": command,
                    "arguments": arguments or [],
                }
            ]
        }
        result = await self._request("POST", f"/devices/{self.device_id}/commands", json=payload)
        return parse_command_result(result)

    async def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        headers = kwargs.pop("headers", {})
        headers = {**self._headers, **headers}
        if method == "POST":
            headers.setdefault("Content-Type", "application/json")

        async with self._session.request(
            method,
            f"{API_BASE_URL}{path}",
            headers=headers,
            **kwargs,
        ) as response:
            if response.status == 401:
                text = await response.text()
                raise SmartThingsUnauthorizedError(
                    f"SmartThings HTTP {response.status}: {text[:500]}"
                )
            if response.status >= 400:
                text = await response.text()
                raise SmartThingsApiError(f"SmartThings HTTP {response.status}: {text[:500]}")
            return await response.json()
