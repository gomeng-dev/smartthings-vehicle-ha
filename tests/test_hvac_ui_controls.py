from pathlib import Path

import pytest

from custom_components.smartthings_vehicle.const import PLATFORMS, build_entity_id
from custom_components.smartthings_vehicle.hvac import HvacSettings

ROOT = Path(__file__).resolve().parents[1]


def test_hvac_settings_default_and_command_payload_kwargs_are_user_adjustable():
    settings = HvacSettings()

    assert settings.temperature == 22
    assert settings.ignition_duration == 10
    assert settings.defog == "off"
    assert settings.as_command_kwargs() == {
        "temperature": 22,
        "unit": "C",
        "ignition_duration": 10,
        "defog": "off",
    }

    adjusted = settings.with_temperature(24).with_ignition_duration(20).with_defog("on")

    assert adjusted.as_command_kwargs() == {
        "temperature": 24,
        "unit": "C",
        "ignition_duration": 20,
        "defog": "on",
    }


@pytest.mark.parametrize(
    ("change", "value"),
    [
        ("with_temperature", 16),
        ("with_temperature", 28),
        ("with_ignition_duration", 0),
        ("with_ignition_duration", 31),
        ("with_defog", "invalid"),
    ],
)
def test_hvac_settings_reject_unsupported_ui_values(change, value):
    with pytest.raises(ValueError):
        getattr(HvacSettings(), change)(value)


def test_home_assistant_platforms_include_hvac_number_select_and_toggle_entities():
    assert PLATFORMS == [
        "sensor",
        "button",
        "lock",
        "switch",
        "number",
        "select",
        "climate",
    ]

    assert build_entity_id("number", "hvac_temperature") == (
        "number.smartthings_vehicle_hvac_temperature"
    )
    assert build_entity_id("number", "hvac_ignition_duration") == (
        "number.smartthings_vehicle_hvac_ignition_duration"
    )
    assert build_entity_id("select", "hvac_defog") == "select.smartthings_vehicle_hvac_defog"
    assert build_entity_id("select", "hvac_ignition_duration") == (
        "select.smartthings_vehicle_hvac_ignition_duration"
    )
    assert build_entity_id("switch", "hvac_defog") == "switch.smartthings_vehicle_hvac_defog"
    assert build_entity_id("climate", "hvac") == "climate.smartthings_vehicle_hvac"
    assert build_entity_id("lock", "door_lock") == "lock.smartthings_vehicle_door_lock"
    assert build_entity_id("switch", "hvac") == "switch.smartthings_vehicle_hvac"

    button_source = (ROOT / "custom_components/smartthings_vehicle/button.py").read_text(
        encoding="utf-8"
    )
    lock_source = (ROOT / "custom_components/smartthings_vehicle/lock.py").read_text(
        encoding="utf-8"
    )
    switch_source = (ROOT / "custom_components/smartthings_vehicle/switch.py").read_text(
        encoding="utf-8"
    )
    sensor_source = (ROOT / "custom_components/smartthings_vehicle/sensor.py").read_text(
        encoding="utf-8"
    )
    number_source = (ROOT / "custom_components/smartthings_vehicle/number.py").read_text(
        encoding="utf-8"
    )
    select_source = (ROOT / "custom_components/smartthings_vehicle/select.py").read_text(
        encoding="utf-8"
    )
    climate_source = (ROOT / "custom_components/smartthings_vehicle/climate.py").read_text(
        encoding="utf-8"
    )
    coordinator_source = (
        ROOT / "custom_components/smartthings_vehicle/coordinator.py"
    ).read_text(encoding="utf-8")

    assert "lock_vehicle" not in button_source
    assert "unlock_vehicle" not in button_source
    assert "start_engine" not in button_source
    assert "stop_engine" not in button_source
    assert "turn_hvac_on" not in button_source
    assert "turn_hvac_off" not in button_source
    assert "LockEntity" in lock_source
    assert "SwitchEntity" in switch_source
    assert "door_lock" in lock_source
    assert "key=\"engine\"" not in switch_source
    assert "async_start_engine" not in switch_source
    assert "async_stop_engine" not in switch_source
    assert "hvac" in switch_source
    assert "NumberEntity" in number_source
    assert "hvac_temperature" in number_source
    assert "hvac_ignition_duration" in number_source
    assert "SelectEntity" in select_source
    assert "hvac_defog" in select_source
    assert "hvac_ignition_duration_select" in select_source
    assert "_DURATION_OPTIONS" in select_source
    assert "ClimateEntity" in climate_source
    assert "ClimateEntityFeature.TARGET_TEMPERATURE" in climate_source
    assert "HVACMode.COOL" in climate_source
    assert "async_set_temperature" in climate_source
    assert "self.hvac_settings.as_command_kwargs()" in coordinator_source
    assert "_async_wait_for_status" in coordinator_source
    assert "VehicleCommandStatus.idle()" in coordinator_source
    assert "mark_pending" in coordinator_source
    assert "mark_accepted" in coordinator_source
    assert "mark_converged" in coordinator_source
    assert "mark_timeout" in coordinator_source
    assert "publish_intermediate_statuses=False" not in coordinator_source
    assert "command_state" in sensor_source
    assert "extra_state_attributes" in sensor_source
    assert "_TOKEN_REFRESH_MARGIN_SECONDS" not in coordinator_source
    assert "async_call_later" not in coordinator_source
    assert "_async_ensure_fresh_token" in coordinator_source
    assert "ConfigEntryState.LOADED" in coordinator_source
    assert "force_reload or" not in coordinator_source
    assert "SmartThingsUnauthorizedError" in coordinator_source
    assert "retrying once" in coordinator_source
