from pathlib import Path

from custom_components.smartthings_vehicle.const import (
    build_entity_id,
    removed_entity_unique_ids,
)

ROOT = Path(__file__).resolve().parents[1]


def test_vehicle_entity_ids_are_generic_and_do_not_include_vehicle_name():
    assert build_entity_id("sensor", "range_km") == "sensor.smartthings_vehicle_range_km"
    assert build_entity_id("sensor", "lock_state") == "sensor.smartthings_vehicle_lock_state"
    assert build_entity_id("sensor", "ev_battery_level") == (
        "sensor.smartthings_vehicle_ev_battery_level"
    )
    assert build_entity_id("sensor", "charging_state") == (
        "sensor.smartthings_vehicle_charging_state"
    )
    assert build_entity_id("sensor", "charging_detail") == (
        "sensor.smartthings_vehicle_charging_detail"
    )
    assert build_entity_id("lock", "door_lock") == "lock.smartthings_vehicle_door_lock"
    assert build_entity_id("switch", "hvac") == "switch.smartthings_vehicle_hvac"

    for vehicle_name in ("쏘나타", "아이오닉", "ev6", "genesis"):
        assert vehicle_name not in build_entity_id("sensor", "range_km").lower()


def test_removed_entity_unique_ids_match_previous_sensor_unique_ids():
    assert removed_entity_unique_ids("device-1") == {
        "device-1_vehicle_make",
        "device-1_vehicle_model",
        "device-1_vehicle_year",
        "device-1_vehicle_trim",
        "device-1_vehicle_color",
        "device-1_vehicle_plate",
        "device-1_vehicle_image",
        "device-1_charging_remaining_time",
    }


def test_entities_set_generic_entity_id_before_home_assistant_registers_them():
    sensor_source = (ROOT / "custom_components/smartthings_vehicle/sensor.py").read_text(
        encoding="utf-8"
    )
    button_source = (ROOT / "custom_components/smartthings_vehicle/button.py").read_text(
        encoding="utf-8"
    )
    lock_source = (ROOT / "custom_components/smartthings_vehicle/lock.py").read_text(
        encoding="utf-8"
    )
    switch_source = (ROOT / "custom_components/smartthings_vehicle/switch.py").read_text(
        encoding="utf-8"
    )

    assert 'self.entity_id = build_entity_id("sensor", description.key)' in sensor_source
    assert 'self.entity_id = build_entity_id("button", description.key)' in button_source
    assert 'self.entity_id = build_entity_id("lock", description.key)' in lock_source
    assert 'self.entity_id = build_entity_id("switch", description.key)' in switch_source
    assert "_attr_entity_id" not in sensor_source
    assert "_attr_entity_id" not in button_source
    assert "_attr_entity_id" not in lock_source
    assert "_attr_entity_id" not in switch_source
