from dataclasses import dataclass

from custom_components.smartthings_vehicle import _remove_matching_entities
from custom_components.smartthings_vehicle.const import removed_entity_unique_ids


@dataclass
class RegistryEntry:
    entity_id: str
    unique_id: str


class Registry:
    def __init__(self) -> None:
        self.removed_entity_ids: list[str] = []

    def async_remove(self, entity_id: str) -> None:
        self.removed_entity_ids.append(entity_id)


def test_remove_matching_entities_deletes_only_retired_vehicle_entities():
    registry = Registry()
    entries = [
        RegistryEntry("sensor.old_model", "device-1_vehicle_model"),
        RegistryEntry("sensor.old_charge_time", "device-1_charging_remaining_time"),
        RegistryEntry("sensor.range", "device-1_range_km"),
        RegistryEntry("sensor.other_vehicle_model", "device-2_vehicle_model"),
    ]

    removed = _remove_matching_entities(
        registry,
        entries,
        removed_entity_unique_ids("device-1"),
    )

    assert removed == 2
    assert registry.removed_entity_ids == ["sensor.old_model", "sensor.old_charge_time"]
