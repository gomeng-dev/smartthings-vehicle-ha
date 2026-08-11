from __future__ import annotations

from typing import Any

REDACTED = "**REDACTED**"
_PREVIEW_TERMS = ("seat", "heat", "vent", "hvac", "climate", "defog")
_SENSITIVE_TERMS = (
    "authorization",
    "coordinate",
    "deviceid",
    "latitude",
    "locationid",
    "longitude",
    "ownerid",
    "password",
    "plate",
    "secret",
    "token",
    "vehicleid",
    "vin",
)
_MAX_LIST_ITEMS = 50
_MAX_STRING_LENGTH = 160


def _normalized_path(path: tuple[str, ...]) -> str:
    return ".".join(path).replace("_", "").replace("-", "").lower()


def _path_contains(path: tuple[str, ...], terms: tuple[str, ...]) -> bool:
    normalized = _normalized_path(path)
    return any(term in normalized for term in terms)


def _type_placeholder(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return "<boolean>"
    if isinstance(value, int):
        return "<integer>"
    if isinstance(value, float):
        return "<number>"
    if isinstance(value, str):
        return "<string>"
    return f"<{type(value).__name__}>"


def _sanitize_value(value: Any, path: tuple[str, ...]) -> Any:
    if _path_contains(path, _SENSITIVE_TERMS):
        return REDACTED

    if isinstance(value, dict):
        return {
            str(key): _sanitize_value(child, (*path, str(key)))
            for key, child in value.items()
        }

    if isinstance(value, list):
        items = [
            _sanitize_value(child, (*path, str(index)))
            for index, child in enumerate(value[:_MAX_LIST_ITEMS])
        ]
        if len(value) > _MAX_LIST_ITEMS:
            items.append(f"<{len(value) - _MAX_LIST_ITEMS} more items>")
        return items

    if not _path_contains(path, _PREVIEW_TERMS):
        return _type_placeholder(value)

    if isinstance(value, str) and len(value) > _MAX_STRING_LENGTH:
        return f"{value[:_MAX_STRING_LENGTH]}…"
    return value


def _capability_id(capability: Any) -> str | None:
    if isinstance(capability, str):
        return capability
    if not isinstance(capability, dict):
        return None
    capability_id = capability.get("id")
    return capability_id if isinstance(capability_id, str) else None


def extract_device_capability_ids(device_payload: dict[str, Any]) -> tuple[str, ...]:
    """Return unique capability IDs from a raw SmartThings device payload."""

    capability_ids: set[str] = set()
    components = device_payload.get("components")
    if not isinstance(components, list):
        return ()

    for component in components:
        if not isinstance(component, dict):
            continue
        capabilities = component.get("capabilities")
        if not isinstance(capabilities, list):
            continue
        for capability in capabilities:
            capability_id = _capability_id(capability)
            if capability_id:
                capability_ids.add(capability_id)
    return tuple(sorted(capability_ids))


def _sanitize_device_components(device_payload: dict[str, Any]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    components = device_payload.get("components")
    if not isinstance(components, list):
        return result

    for component in components:
        if not isinstance(component, dict):
            continue
        component_id = component.get("id")
        if not isinstance(component_id, str):
            continue
        capabilities = component.get("capabilities")
        sanitized_capabilities: list[dict[str, Any]] = []
        if isinstance(capabilities, list):
            for capability in capabilities:
                capability_id = _capability_id(capability)
                if not capability_id:
                    continue
                item: dict[str, Any] = {"id": capability_id}
                if isinstance(capability, dict) and isinstance(
                    capability.get("version"), int
                ):
                    item["version"] = capability["version"]
                sanitized_capabilities.append(item)
        result.append(
            {
                "id": component_id,
                "capabilities": sorted(
                    sanitized_capabilities,
                    key=lambda item: item["id"],
                ),
            }
        )
    return result


def _sanitize_status(status_payload: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    components = status_payload.get("components")
    if not isinstance(components, dict):
        return result

    for component_id, capabilities in components.items():
        if not isinstance(component_id, str) or not isinstance(capabilities, dict):
            continue
        component_result: dict[str, Any] = {}
        for capability_id, attributes in capabilities.items():
            if not isinstance(capability_id, str) or not isinstance(attributes, dict):
                continue
            capability_result: dict[str, Any] = {}
            for attribute_id, attribute_status in attributes.items():
                if not isinstance(attribute_id, str):
                    continue
                path = (component_id, capability_id, attribute_id)
                if not isinstance(attribute_status, dict):
                    capability_result[attribute_id] = {
                        "value": _sanitize_value(attribute_status, path)
                    }
                    continue

                sanitized_attribute: dict[str, Any] = {}
                if "value" in attribute_status:
                    sanitized_attribute["value"] = _sanitize_value(
                        attribute_status["value"],
                        (*path, "value"),
                    )
                unit = attribute_status.get("unit")
                if isinstance(unit, str):
                    sanitized_attribute["unit"] = unit
                capability_result[attribute_id] = sanitized_attribute
            component_result[capability_id] = capability_result
        result[component_id] = component_result
    return result


def _sanitize_capability_definitions(
    definitions: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for capability_id, definition in sorted(definitions.items()):
        if not isinstance(definition, dict):
            continue
        result[capability_id] = {
            key: definition[key]
            for key in ("id", "name", "status", "attributes", "commands")
            if key in definition
        }
    return result


def build_vehicle_diagnostics(
    device_payload: dict[str, Any],
    status_payload: dict[str, Any],
    capability_definitions: dict[str, dict[str, Any]] | None = None,
    unavailable_capability_definitions: list[str] | None = None,
) -> dict[str, Any]:
    """Build diagnostics that retain seat schemas without vehicle identifiers."""

    return {
        "privacy": (
            "Identifiers and non-HVAC values are redacted. Review this file before sharing."
        ),
        "device": {"components": _sanitize_device_components(device_payload)},
        "status": {"components": _sanitize_status(status_payload)},
        "capability_definitions": _sanitize_capability_definitions(
            capability_definitions or {}
        ),
        "unavailable_capability_definitions": sorted(
            unavailable_capability_definitions or []
        ),
    }
