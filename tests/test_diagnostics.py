import json
from pathlib import Path

from custom_components.smartthings_vehicle.diagnostics_data import (
    REDACTED,
    build_vehicle_diagnostics,
    extract_device_capability_ids,
)

ROOT = Path(__file__).resolve().parents[1]


def test_vehicle_diagnostics_preserve_seat_structure_and_redact_identifiers():
    device_payload = {
        "deviceId": "device-secret",
        "locationId": "location-secret",
        "label": "내 아이오닉 5",
        "components": [
            {
                "id": "main",
                "capabilities": [
                    {"id": "vehicleHvac", "version": 1},
                    {"id": "custom.vehicleSeat", "version": 1},
                    "execute",
                ],
            }
        ],
    }
    status_payload = {
        "components": {
            "main": {
                "custom.vehicleSeat": {
                    "driverSeat": {"value": "heat3"},
                    "passengerSeat": {"value": "vent2"},
                },
                "execute": {
                    "data": {
                        "value": {
                            "heatVentSeat": {
                                "rearLeftSeat": {"heatVentLevel": 3},
                            },
                            "vin": "VIN-SECRET",
                        }
                    }
                },
                "vehicleInformation": {
                    "vehicleId": {"value": "VEHICLE-SECRET"},
                },
                "vehicleRange": {
                    "estimatedRemainingRange": {"value": 386, "unit": "km"}
                },
            }
        }
    }
    definitions = {
        "custom.vehicleSeat": {
            "id": "custom.vehicleSeat",
            "name": "Vehicle Seat",
            "status": "live",
            "attributes": {"driverSeat": {"schema": {"type": "object"}}},
            "commands": {"setDriverSeat": {"arguments": []}},
            "ownerId": "owner-secret",
        }
    }

    diagnostics = build_vehicle_diagnostics(
        device_payload,
        status_payload,
        definitions,
        ["vehicleHvac"],
    )
    serialized = json.dumps(diagnostics)

    assert "device-secret" not in serialized
    assert "location-secret" not in serialized
    assert "내 아이오닉 5" not in serialized
    assert "VIN-SECRET" not in serialized
    assert "VEHICLE-SECRET" not in serialized
    assert "owner-secret" not in serialized
    assert diagnostics["status"]["components"]["main"]["custom.vehicleSeat"] == {
        "driverSeat": {"value": "heat3"},
        "passengerSeat": {"value": "vent2"},
    }
    assert diagnostics["status"]["components"]["main"]["execute"]["data"][
        "value"
    ] == {
        "heatVentSeat": {"rearLeftSeat": {"heatVentLevel": 3}},
        "vin": REDACTED,
    }
    assert diagnostics["status"]["components"]["main"]["vehicleRange"] == {
        "estimatedRemainingRange": {"value": "<integer>", "unit": "km"}
    }
    assert diagnostics["capability_definitions"]["custom.vehicleSeat"]["commands"] == {
        "setDriverSeat": {"arguments": []}
    }
    assert diagnostics["unavailable_capability_definitions"] == ["vehicleHvac"]


def test_extract_device_capability_ids_is_sorted_and_unique():
    payload = {
        "components": [
            {
                "id": "main",
                "capabilities": ["vehicleHvac", {"id": "custom.vehicleSeat"}],
            },
            {"id": "rear", "capabilities": [{"id": "custom.vehicleSeat"}]},
        ]
    }

    assert extract_device_capability_ids(payload) == (
        "custom.vehicleSeat",
        "vehicleHvac",
    )


def test_home_assistant_diagnostics_entry_points_exist():
    source = (
        ROOT / "custom_components/smartthings_vehicle/diagnostics.py"
    ).read_text(encoding="utf-8")

    assert "async_get_config_entry_diagnostics" in source
    assert "async_get_device_diagnostics" in source
