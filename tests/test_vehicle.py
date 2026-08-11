import pytest

from custom_components.smartthings_vehicle.vehicle import (
    SmartThingsApiError,
    VehicleCommandResult,
    VehicleCommandStatus,
    VehicleStatus,
    extract_access_token,
    parse_command_result,
    parse_vehicle_status,
)


def test_extract_access_token_supports_home_assistant_smartthings_oauth_shapes():
    assert extract_access_token({"access_token": "direct-token"}) == "direct-token"
    assert extract_access_token({"token": {"access_token": "nested-token"}}) == "nested-token"
    assert extract_access_token({"auth": {"accessToken": "camel-token"}}) == "camel-token"


def test_extract_access_token_rejects_missing_token():
    with pytest.raises(SmartThingsApiError):
        extract_access_token({"not_token": "nope"})


def test_parse_vehicle_status_maps_smartthings_status_payload():
    payload = {
        "components": {
            "main": {
                "vehicleRange": {"estimatedRemainingRange": {"value": 412, "unit": "km"}},
                "vehicleOdometer": {"odometerReading": {"value": 12345.6, "unit": "km"}},
                "vehicleInformation": {
                    "vehicleMake": {"value": "Hyundai"},
                    "vehicleModel": {"value": "IONIQ 5"},
                    "vehicleYear": {"value": 2025},
                    "vehicleTrim": {"value": "Prestige"},
                    "vehicleColor": {"value": "Digital Teal"},
                    "vehiclePlate": {"value": "12가3456"},
                    "vehicleImage": {"value": "https://example.com/ioniq5.png"},
                },
                "vehicleEngine": {"engineState": {"value": "off"}},
                "vehicleHvac": {
                    "hvacState": {"value": "off"},
                    "hvacSpeed": {"value": 3},
                    "defogState": {"value": "off"},
                    "temperature": {"value": 22, "unit": "C"},
                },
                "vehicleDoorState": {
                    "lockState": {"value": "locked"},
                    "frontLeftDoor": {"value": "locked"},
                    "frontRightDoor": {"value": "locked"},
                    "rearLeftDoor": {"value": "locked"},
                    "rearRightDoor": {"value": "locked"},
                },
                "vehicleWindowState": {
                    "frontLeftWindow": {"value": "closed"},
                    "frontRightWindow": {"value": "closed"},
                    "rearLeftWindow": {"value": "closed"},
                    "rearRightWindow": {"value": "closed"},
                },
                "vehicleWarning": {
                    "fuel": {"value": "normal"},
                    "smartKeyBattery": {"value": "normal"},
                    "tirePressureFrontLeft": {"value": "normal"},
                    "tirePressureFrontRight": {"value": "normal"},
                    "tirePressureRearLeft": {"value": "warning"},
                    "tirePressureRearRight": {"value": "normal"},
                    "lampWire": {"value": "normal"},
                    "washerFluid": {"value": "warning"},
                    "brakeFluid": {"value": "normal"},
                    "engineOil": {"value": "normal"},
                },
                "healthCheck": {"DeviceWatch-DeviceStatus": {"value": "online"}},
            }
        }
    }

    status = parse_vehicle_status(payload)

    assert status == VehicleStatus(
        range_km=412,
        odometer_km=12345.6,
        engine_state="off",
        hvac_state="off",
        hvac_speed=3,
        defog_state="off",
        cabin_temperature=22,
        cabin_temperature_unit="C",
        lock_state="locked",
        front_left_door="locked",
        front_right_door="locked",
        rear_left_door="locked",
        rear_right_door="locked",
        front_left_window="closed",
        front_right_window="closed",
        rear_left_window="closed",
        rear_right_window="closed",
        fuel_warning="normal",
        smart_key_battery="normal",
        tire_pressure_warning="warning",
        tire_pressure_front_left="normal",
        tire_pressure_front_right="normal",
        tire_pressure_rear_left="warning",
        tire_pressure_rear_right="normal",
        lamp_wire_warning="normal",
        washer_fluid_warning="warning",
        brake_fluid_warning="normal",
        engine_oil_warning="normal",
        health="online",
    )
    assert not {
        "vehicle_make",
        "vehicle_model",
        "vehicle_year",
        "vehicle_trim",
        "vehicle_color",
        "vehicle_plate",
        "vehicle_image",
        "charging_remaining_time",
    } & set(VehicleStatus.__dataclass_fields__)


def test_parse_vehicle_status_tolerates_missing_capabilities():
    status = parse_vehicle_status({"components": {"main": {}}})

    assert status.lock_state is None
    assert status.engine_state is None
    assert status.range_km is None
    assert status.ev_battery_level is None
    assert status.supports_attribute("vehicleBattery", "batteryLevel") is False


def test_parse_2025_ioniq5_electric_vehicle_status():
    payload = {
        "components": {
            "main": {
                "vehicleRange": {
                    "estimatedRemainingRange": {"value": 386, "unit": "km"}
                },
                "vehicleBattery": {
                    "batteryLevel": {"value": 72, "unit": "%"},
                    "chargingState": {"value": "charging"},
                    "chargingPlug": {"value": "connected"},
                    "chargingDetail": {"value": "fastCharging"},
                },
                "vehicleWarning": {
                    "auxiliaryBattery": {"value": "normal"},
                    "electricVehicleBattery": {"value": "normal"},
                    "tirePressureFrontLeft": {"value": "normal"},
                    "tirePressureFrontRight": {"value": "normal"},
                    "tirePressureRearLeft": {"value": "normal"},
                    "tirePressureRearRight": {"value": "normal"},
                    "lampWire": {"value": "normal"},
                    "washerFluid": {"value": "normal"},
                    "brakeFluid": {"value": "normal"},
                    "engineOil": {"value": "normal"},
                },
            }
        }
    }

    status = parse_vehicle_status(payload)

    assert status.range_km == 386
    assert status.ev_battery_level == 72
    assert status.charging_state == "charging"
    assert status.charging_plug == "connected"
    assert status.charging_detail == "fastCharging"
    assert status.auxiliary_battery_warning == "normal"
    assert status.electric_vehicle_battery_warning == "normal"
    assert status.tire_pressure_warning == "normal"
    assert status.lamp_wire_warning == "normal"
    assert status.washer_fluid_warning == "normal"
    assert status.brake_fluid_warning == "normal"
    assert status.engine_oil_warning == "normal"
    assert "vehicleBattery" in status.available_capabilities
    assert status.supports_attribute("vehicleBattery", "batteryLevel") is True
    assert status.supports_attribute("vehicleBattery", "chargingDetail") is True
    assert status.supports_attribute("vehicleFuelLevel", "fuelLevel") is False


def test_tire_pressure_warning_is_unknown_without_reported_wheel_states():
    status = parse_vehicle_status(
        {
            "components": {
                "main": {
                    "vehicleWarning": {
                        "tirePressureFrontLeft": {"value": None},
                        "tirePressureFrontRight": {"value": None},
                    }
                }
            }
        }
    )

    assert status.tire_pressure_warning is None


def test_parse_command_result_requires_accepted_status():
    payload = {"results": [{"id": "abc", "status": "ACCEPTED"}]}

    assert parse_command_result(payload) == VehicleCommandResult(
        accepted=True,
        command_id="abc",
        raw=payload,
    )


def test_parse_command_result_rejects_failed_status():
    with pytest.raises(SmartThingsApiError):
        parse_command_result({"results": [{"id": "abc", "status": "FAILED"}]})


def test_vehicle_command_status_tracks_pending_response_and_terminal_states():
    status = VehicleCommandStatus.idle().mark_pending(
        command="lock",
        target="lock_state=locked",
        started_at=100.0,
    )

    assert status.state == "pending"
    assert status.as_attributes() == {
        "last_command": "lock",
        "target": "lock_state=locked",
        "command_id": None,
        "started_at": 100.0,
        "completed_at": None,
        "last_error": None,
    }

    accepted = status.mark_accepted("cmd-1")
    assert accepted.state == "accepted"
    assert accepted.command_id == "cmd-1"
    assert accepted.completed_at is None

    converged = accepted.mark_converged(completed_at=104.0)
    assert converged.state == "converged"
    assert converged.completed_at == 104.0

    timed_out = accepted.mark_timeout("status did not converge", completed_at=124.0)
    assert timed_out.state == "timeout"
    assert timed_out.last_error == "status did not converge"

    failed = status.mark_failed("SmartThings HTTP 500", completed_at=101.0)
    assert failed.state == "failed"
    assert failed.last_error == "SmartThings HTTP 500"
