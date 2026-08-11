from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from datetime import timedelta
from time import time
from typing import Any, Protocol, TypeVar

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.event import async_call_later
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    CONF_DEVICE_ID,
    CONF_TITLE,
    DEFAULT_SCAN_INTERVAL_SECONDS,
    DOMAIN,
    SMARTTHINGS_DOMAIN,
)
from .hvac import HvacSettings
from .vehicle import (
    SmartThingsApiError,
    SmartThingsTokenInfo,
    SmartThingsUnauthorizedError,
    SmartThingsVehicleClient,
    VehicleCommandResult,
    VehicleCommandStatus,
    VehicleStatus,
    VehicleStatusConvergenceResult,
    async_wait_for_vehicle_status,
    extract_token_info,
)

_LOGGER = logging.getLogger(__name__)
_COMMAND_CONVERGENCE_TIMEOUT_SECONDS = 24
_COMMAND_CONVERGENCE_POLL_SECONDS = 2
_TOKEN_REFRESH_MARGIN_SECONDS = 600
_ON_STATES = {"on", "running", "started"}
_OFF_STATES = {"off", "stopped"}
_T = TypeVar("_T")


class _StatusPredicate(Protocol):
    def __call__(self, status: VehicleStatus) -> bool: ...


class SmartThingsVehicleCoordinator(DataUpdateCoordinator[VehicleStatus]):
    """Coordinates SmartThings vehicle status polling."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.config_entry = entry
        self.hvac_settings = HvacSettings()
        self.command_status = VehicleCommandStatus.idle()
        token_info = self._find_smartthings_token_info(hass)
        self.client = SmartThingsVehicleClient(
            async_get_clientsession(hass),
            token_info.access_token,
            entry.data[CONF_DEVICE_ID],
        )
        self._token_expires_at = token_info.expires_at
        self._remove_token_refresh_timer: Callable[[], None] | None = None
        super().__init__(
            hass,
            _LOGGER,
            name=entry.data.get(CONF_TITLE) or "스마트싱스 차량",
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL_SECONDS),
        )
        self._schedule_token_refresh()

    async def _async_update_data(self) -> VehicleStatus:
        return await self._async_get_status_with_fresh_token()

    async def async_refresh_vehicle(self) -> None:
        await self._async_send_tracked_command(
            "refresh",
            "status=refreshed",
            self.client.async_refresh,
        )
        await self.async_request_refresh()
        self._set_command_status(self.command_status.mark_converged(completed_at=time()))

    async def async_ping_vehicle(self) -> None:
        await self._async_send_tracked_command(
            "ping",
            "health=online",
            self.client.async_ping,
        )
        await self.async_request_refresh()
        self._set_command_status(self.command_status.mark_converged(completed_at=time()))

    async def async_lock_vehicle(self) -> None:
        await self._async_send_tracked_command(
            "lock",
            "lock_state=locked",
            self.client.async_lock,
        )
        result = await self._async_wait_for_status(
            lambda status: status.lock_state == "locked",
            "lock_state=locked",
        )
        self._finalize_command_status(result, "status did not converge to lock_state=locked")

    async def async_unlock_vehicle(self) -> None:
        await self._async_send_tracked_command(
            "unlock",
            "lock_state=unlocked",
            self.client.async_unlock,
        )
        result = await self._async_wait_for_status(
            lambda status: status.lock_state == "unlocked",
            "lock_state=unlocked",
        )
        self._finalize_command_status(result, "status did not converge to lock_state=unlocked")

    async def async_start_engine(self) -> None:
        await self._async_send_tracked_command(
            "start_engine",
            "engine_state=running",
            self.client.async_start_engine,
        )
        result = await self._async_wait_for_status(
            lambda status: status.engine_state == "running",
            "engine_state=running",
            timeout_seconds=60,
        )
        self._finalize_command_status(result, "status did not converge to engine_state=running")

    async def async_stop_engine(self) -> None:
        await self._async_send_tracked_command(
            "stop_engine",
            "engine_state=off",
            self.client.async_stop_engine,
        )
        result = await self._async_wait_for_status(
            lambda status: status.engine_state == "off",
            "engine_state=off",
            timeout_seconds=60,
        )
        self._finalize_command_status(result, "status did not converge to engine_state=off")

    async def async_turn_hvac_on(self) -> None:
        await self._async_send_tracked_command(
            "turn_hvac_on",
            "hvac_state=on",
            self.client.async_turn_hvac_on,
            **self.hvac_settings.as_command_kwargs(),
        )
        result = await self._async_wait_for_status(
            lambda status: status.hvac_state in _ON_STATES,
            "hvac_state=on",
        )
        self._finalize_command_status(result, "status did not converge to hvac_state=on")

    async def async_turn_hvac_off(self) -> None:
        await self._async_send_tracked_command(
            "turn_hvac_off",
            "hvac_state=off",
            self.client.async_turn_hvac_off,
        )
        result = await self._async_wait_for_status(
            lambda status: status.hvac_state in _OFF_STATES,
            "hvac_state=off",
        )
        self._finalize_command_status(result, "status did not converge to hvac_state=off")

    @property
    def is_hvac_on(self) -> bool:
        if self.data is None:
            return False
        return self.data.hvac_state in _ON_STATES

    async def async_set_hvac_defog_on(self) -> None:
        self.set_hvac_defog("on")

    async def async_set_hvac_defog_off(self) -> None:
        self.set_hvac_defog("off")

    async def _async_get_status_with_fresh_token(self) -> VehicleStatus:
        return await self._async_call_with_fresh_token(self.client.async_get_status)

    async def async_get_diagnostics_payloads(
        self,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        """Return raw device and status payloads using a fresh OAuth token."""

        device = await self._async_call_with_fresh_token(self.client.async_get_device)
        status = await self._async_call_with_fresh_token(self.client.async_get_raw_status)
        return device, status

    async def async_get_capability_definition(
        self,
        capability_id: str,
    ) -> dict[str, Any]:
        """Return a SmartThings capability definition for diagnostics."""

        return await self._async_call_with_fresh_token(
            self.client.async_get_capability_definition,
            capability_id,
        )

    async def _async_call_with_fresh_token(
        self,
        callback: Callable[..., Awaitable[_T]],
        *args: Any,
        **kwargs: Any,
    ) -> _T:
        await self._async_ensure_fresh_token()
        try:
            return await callback(*args, **kwargs)
        except SmartThingsUnauthorizedError:
            _LOGGER.info(
                "SmartThings vehicle access token was rejected; refreshing official "
                "SmartThings entry and retrying once"
            )
            await self._async_ensure_fresh_token(force_reload=True)
            return await callback(*args, **kwargs)

    async def _async_send_tracked_command(
        self,
        command: str,
        target: str | None,
        callback: Callable[..., Awaitable[VehicleCommandResult]],
        *args: Any,
        **kwargs: Any,
    ) -> VehicleCommandResult:
        self._set_command_status(
            self.command_status.mark_pending(
                command=command,
                target=target,
                started_at=time(),
            )
        )
        try:
            result = await self._async_call_with_fresh_token(callback, *args, **kwargs)
        except Exception as err:
            self._set_command_status(
                self.command_status.mark_failed(str(err), completed_at=time())
            )
            raise

        self._set_command_status(self.command_status.mark_accepted(result.command_id))
        return result

    def _set_command_status(self, status: VehicleCommandStatus) -> None:
        self.command_status = status
        self.async_update_listeners()

    def _finalize_command_status(
        self,
        result: VehicleStatusConvergenceResult,
        timeout_message: str,
    ) -> None:
        if result.converged:
            self._set_command_status(self.command_status.mark_converged(completed_at=time()))
            return

        last_error = (
            f"{timeout_message}; last status error: {result.last_error}"
            if result.last_error
            else timeout_message
        )
        self._set_command_status(
            self.command_status.mark_timeout(last_error, completed_at=time())
        )

    async def _async_ensure_fresh_token(self, *, force_reload: bool = False) -> None:
        token_info = self._find_smartthings_token_info(self.hass)
        should_reload = force_reload or self._token_expires_soon(token_info)

        if should_reload:
            await self._async_reload_smartthings_entries()
            token_info = self._find_smartthings_token_info(self.hass)

        self._apply_token_info(token_info)

    async def _async_reload_smartthings_entries(self) -> None:
        entries = list(self.hass.config_entries.async_entries(SMARTTHINGS_DOMAIN))
        if not entries:
            raise SmartThingsApiError(
                "No Home Assistant SmartThings config entry found for OAuth refresh."
            )

        for entry in entries:
            _LOGGER.debug(
                "Reloading SmartThings config entry %s before token expiry",
                entry.entry_id,
            )
            await self.hass.config_entries.async_reload(entry.entry_id)

    def _apply_token_info(self, token_info: SmartThingsTokenInfo) -> None:
        self.client.set_access_token(token_info.access_token)
        self._token_expires_at = token_info.expires_at
        self._schedule_token_refresh()

    def _token_expires_soon(self, token_info: SmartThingsTokenInfo) -> bool:
        if token_info.expires_at is None:
            return False
        return token_info.expires_at - time() <= _TOKEN_REFRESH_MARGIN_SECONDS

    def _schedule_token_refresh(self) -> None:
        if self._remove_token_refresh_timer is not None:
            self._remove_token_refresh_timer()
            self._remove_token_refresh_timer = None

        if self._token_expires_at is None:
            return

        delay = max(self._token_expires_at - time() - _TOKEN_REFRESH_MARGIN_SECONDS, 0)
        self._remove_token_refresh_timer = async_call_later(
            self.hass,
            delay,
            self._handle_scheduled_token_refresh,
        )

    def _handle_scheduled_token_refresh(self, _: Any) -> None:
        self._remove_token_refresh_timer = None
        self.hass.async_create_task(self._async_scheduled_token_refresh())

    async def _async_scheduled_token_refresh(self) -> None:
        try:
            await self._async_ensure_fresh_token(force_reload=True)
        except Exception:  # noqa: BLE001 - keep polling fallback alive after scheduled refresh errors
            _LOGGER.exception("Scheduled SmartThings vehicle token refresh failed")

    def async_shutdown(self) -> None:
        if self._remove_token_refresh_timer is not None:
            self._remove_token_refresh_timer()
            self._remove_token_refresh_timer = None

    async def _async_wait_for_status(
        self,
        predicate: _StatusPredicate,
        target_description: str,
        *,
        timeout_seconds: int = _COMMAND_CONVERGENCE_TIMEOUT_SECONDS,
        poll_seconds: int = _COMMAND_CONVERGENCE_POLL_SECONDS,
    ) -> VehicleStatusConvergenceResult:
        """Poll SmartThings status until an accepted vehicle command settles."""

        def update_status(status: VehicleStatus) -> None:
            self.async_set_updated_data(status)

        result = await async_wait_for_vehicle_status(
            self._async_get_status_with_fresh_token,
            predicate,
            update_status,
            timeout_seconds=timeout_seconds,
            poll_seconds=poll_seconds,
        )
        if result.converged:
            return result

        _LOGGER.warning(
            "SmartThings vehicle command was accepted but status did not converge to %s "
            "within %ss%s",
            target_description,
            timeout_seconds,
            f"; last status error: {result.last_error}" if result.last_error else "",
        )
        return result

    def set_hvac_temperature(self, temperature: float | int) -> None:
        self.hvac_settings = self.hvac_settings.with_temperature(temperature)
        self.async_update_listeners()

    def set_hvac_ignition_duration(self, ignition_duration: float | int) -> None:
        self.hvac_settings = self.hvac_settings.with_ignition_duration(ignition_duration)
        self.async_update_listeners()

    def set_hvac_defog(self, defog: str) -> None:
        self.hvac_settings = self.hvac_settings.with_defog(defog)
        self.async_update_listeners()

    @staticmethod
    def _find_smartthings_token_info(hass: HomeAssistant) -> SmartThingsTokenInfo:
        for entry in hass.config_entries.async_entries(SMARTTHINGS_DOMAIN):
            try:
                return extract_token_info(dict(entry.data))
            except SmartThingsApiError:
                continue
        raise SmartThingsApiError(
            "No usable Home Assistant SmartThings OAuth token found. "
            "Set up the official SmartThings integration first."
        )

    @property
    def device_info(self) -> dict[str, Any]:
        return {
            "identifiers": {(DOMAIN, self.client.device_id)},
            "name": self.config_entry.data.get(CONF_TITLE) or "스마트싱스 차량",
            "manufacturer": "Hyundai Motor Group / SmartThings",
            "model": "한국 SmartThings 차량",
        }
