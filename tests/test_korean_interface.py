import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_readme_is_distribution_focused_and_korean_first():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "현대자동차·기아·제네시스" in readme
    assert "## HACS 설치" in readme
    assert "## 최초 설정" in readme
    assert "## 주요 기능" in readme
    assert "## 개발" not in readme
    assert "설계 원칙" not in readme


def test_home_assistant_visible_strings_are_korean_first():
    manifest = json.loads(
        (ROOT / "custom_components/smartthings_vehicle/manifest.json").read_text(
            encoding="utf-8"
        )
    )
    hacs = json.loads((ROOT / "hacs.json").read_text(encoding="utf-8"))
    strings = json.loads(
        (ROOT / "custom_components/smartthings_vehicle/strings.json").read_text(
            encoding="utf-8"
        )
    )
    ko = json.loads(
        (ROOT / "custom_components/smartthings_vehicle/translations/ko.json").read_text(
            encoding="utf-8"
        )
    )

    assert manifest["name"] == "스마트싱스 차량"
    assert hacs["name"] == "스마트싱스 차량"
    assert strings["config"]["step"]["user"]["title"] == "스마트싱스 차량"
    assert strings["entity"]["sensor"]["range_km"]["name"] == (
        "주행 · 주행 가능 거리"
    )
    assert strings["entity"]["sensor"]["command_state"]["name"] == (
        "시스템 · 명령 상태"
    )
    assert strings["entity"]["sensor"]["ev_battery_level"]["name"] == (
        "전기차 · 고전압 배터리 잔량"
    )
    assert strings["entity"]["sensor"]["charging_state"]["name"] == (
        "전기차 · 충전 상태"
    )
    assert strings["entity"]["sensor"]["charging_detail"]["name"] == (
        "전기차 · 충전 방식"
    )
    assert strings["entity"]["sensor"]["charging_plug"]["name"] == (
        "전기차 · 충전 커넥터 상태"
    )
    assert strings["entity"]["sensor"]["tire_pressure_warning"]["name"] == (
        "경고 · 타이어 공기압"
    )
    assert strings["entity"]["sensor"]["lamp_wire_warning"]["name"] == (
        "경고 · 외장 램프 회로"
    )
    assert strings["entity"]["sensor"]["washer_fluid_warning"]["name"] == (
        "경고 · 워셔액"
    )
    assert strings["entity"]["sensor"]["brake_fluid_warning"]["name"] == (
        "경고 · 브레이크액"
    )
    assert strings["entity"]["sensor"]["engine_oil_warning"]["name"] == (
        "경고 · 엔진오일"
    )
    assert {
        "fuel_warning",
        "smart_key_battery",
        "tire_pressure_warning",
        "tire_pressure_front_left",
        "tire_pressure_front_right",
        "tire_pressure_rear_left",
        "tire_pressure_rear_right",
        "lamp_wire_warning",
        "washer_fluid_warning",
        "brake_fluid_warning",
        "engine_oil_warning",
        "auxiliary_battery_warning",
        "electric_vehicle_battery_warning",
    } <= set(strings["entity"]["sensor"])
    assert not {
        "vehicle_make",
        "vehicle_model",
        "vehicle_year",
        "vehicle_trim",
        "vehicle_color",
        "vehicle_plate",
        "charging_remaining_time",
    } & set(strings["entity"]["sensor"])
    assert all(
        " · " in translation["name"]
        for translation in strings["entity"]["sensor"].values()
    )
    assert set(strings["entity"]["button"]) == {"refresh", "ping_vehicle"}
    assert strings["entity"]["lock"]["door_lock"]["name"] == "차량 제어 · 잠금"
    assert set(strings["entity"]["switch"]) == {"hvac", "hvac_defog"}
    assert strings["entity"]["switch"]["hvac"]["name"] == (
        "공조 제어 · 켜기/끄기"
    )
    assert strings["entity"]["switch"]["hvac_defog"]["name"] == (
        "공조 설정 · 앞유리 김서림 제거"
    )
    assert set(strings["entity"]["select"]) == {"hvac_defog", "hvac_ignition_duration"}
    assert strings["entity"]["select"]["hvac_ignition_duration"]["name"] == (
        "공조 설정 · 작동 시간"
    )
    assert strings["entity"]["climate"]["hvac_climate"]["name"] == (
        "공조 제어 · 에어컨"
    )
    assert ko == strings


def test_home_assistant_entity_categories_are_applied():
    component = ROOT / "custom_components/smartthings_vehicle"
    sensor_source = (component / "sensor.py").read_text(encoding="utf-8")
    button_source = (component / "button.py").read_text(encoding="utf-8")
    number_source = (component / "number.py").read_text(encoding="utf-8")
    select_source = (component / "select.py").read_text(encoding="utf-8")
    switch_source = (component / "switch.py").read_text(encoding="utf-8")

    assert "_attr_entity_category = EntityCategory.DIAGNOSTIC" in sensor_source
    assert "EntityCategory.DIAGNOSTIC" not in button_source
    assert number_source.count("entity_category=EntityCategory.CONFIG") == 2
    assert select_source.count("entity_category=EntityCategory.CONFIG") == 2
    assert switch_source.count("entity_category=EntityCategory.CONFIG") == 1
