from __future__ import annotations

DOMAIN = "smartthings_vehicle"
SMARTTHINGS_DOMAIN = "smartthings"
CONF_DEVICE_ID = "device_id"
CONF_TITLE = "title"
DEFAULT_SCAN_INTERVAL_SECONDS = 60
PLATFORMS = ["sensor", "button", "lock", "switch", "number", "select", "climate"]
REMOVED_ENTITY_KEYS = frozenset(
    {
        "vehicle_make",
        "vehicle_model",
        "vehicle_year",
        "vehicle_trim",
        "vehicle_color",
        "vehicle_plate",
        "vehicle_image",
        "charging_remaining_time",
    }
)


def removed_entity_unique_ids(device_id: str) -> frozenset[str]:
    """Return entity unique IDs retired by newer integration versions."""

    return frozenset(f"{device_id}_{key}" for key in REMOVED_ENTITY_KEYS)


def build_entity_id(platform: str, key: str) -> str:
    """Build a generic Home Assistant entity ID for a vehicle entity.

    Keep object IDs independent from the user-visible vehicle name so the same
    integration can support multiple Hyundai/Kia/Genesis vehicles consistently.
    Home Assistant will append a numeric suffix when another vehicle exposes the
    same generic entity ID.
    """

    return f"{platform}.{DOMAIN}_{key}"
