import asyncio

import pytest

from custom_components.smartthings_vehicle.vehicle import (
    SmartThingsUnauthorizedError,
    SmartThingsVehicleClient,
    extract_access_token,
    extract_token_info,
)


class FakeResponse:
    def __init__(self, status, payload=None, text=""):
        self.status = status
        self._payload = payload or {}
        self._text = text

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def json(self):
        return self._payload

    async def text(self):
        return self._text


class FakeSession:
    def __init__(self, *responses):
        self.responses = list(responses)
        self.requests = []

    def request(self, method, url, headers=None, **kwargs):
        self.requests.append({"method": method, "url": url, "headers": headers or {}, **kwargs})
        return self.responses.pop(0)


def test_extract_token_info_reads_nested_home_assistant_oauth_metadata():
    token_info = extract_token_info(
        {
            "location_id": "home",
            "token": {
                "access_token": "access-1",
                "refresh_token": "refresh-1",
                "expires_at": 12345.6,
            },
        }
    )

    assert token_info.access_token == "access-1"
    assert token_info.expires_at == 12345.6
    assert extract_access_token({"token": {"access_token": "access-1"}}) == "access-1"


def test_extract_token_info_accepts_direct_token_and_string_expiry():
    token_info = extract_token_info({"access_token": "direct", "expires_at": "42.5"})

    assert token_info.access_token == "direct"
    assert token_info.expires_at == 42.5


def test_client_raises_specific_unauthorized_error_for_401():
    async def run():
        session = FakeSession(FakeResponse(401, text="expired"))
        client = SmartThingsVehicleClient(session, "old-token", "vehicle-id")

        with pytest.raises(SmartThingsUnauthorizedError):
            await client.async_get_device()

    asyncio.run(run())


def test_client_uses_replaced_access_token_on_next_request():
    async def run():
        session = FakeSession(FakeResponse(200, payload={"deviceId": "vehicle-id"}))
        client = SmartThingsVehicleClient(session, "old-token", "vehicle-id")
        client.set_access_token("new-token")

        await client.async_get_device()

        assert session.requests[0]["headers"]["Authorization"] == "Bearer new-token"

    asyncio.run(run())


def test_client_fetches_raw_status_and_capability_definition_for_diagnostics():
    async def run():
        session = FakeSession(
            FakeResponse(200, payload={"components": {"main": {}}}),
            FakeResponse(200, payload={"id": "custom.vehicleSeat"}),
        )
        client = SmartThingsVehicleClient(session, "token", "vehicle-id")

        await client.async_get_raw_status()
        definition = await client.async_get_capability_definition("custom.vehicleSeat")

        assert definition == {"id": "custom.vehicleSeat"}
        assert session.requests[0]["url"].endswith("/devices/vehicle-id/status")
        assert session.requests[1]["url"].endswith(
            "/capabilities/custom.vehicleSeat/1"
        )

    asyncio.run(run())
