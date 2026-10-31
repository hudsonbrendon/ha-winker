"""Coordinator: puxa boletos, avisos, reservas e encomendas de um portal."""

from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import WinkerApiError, WinkerClient
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class WinkerCoordinator(DataUpdateCoordinator):
    """Um coordinator por portal (condomínio)."""

    def __init__(
        self, hass: HomeAssistant, client: WinkerClient, id_portal: int
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{id_portal}",
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self._client = client
        self._id_portal = id_portal

    async def _async_update_data(self) -> dict:
        try:
            billings = await self._client.get_billings(self._id_portal)
            messages = await self._client.get_messages(self._id_portal)
            booking_count = await self._client.get_booking_count(self._id_portal)
            packages = await self._client.get_packages_todeliver(self._id_portal)
            consumption = await self._client.get_consumption(self._id_portal)
        except WinkerApiError as err:
            raise UpdateFailed(str(err)) from err

        opened = [b for b in billings if b.get("situation") == "opened"]
        return {
            "billings": billings,
            "billings_opened": opened,
            "messages": messages,
            "booking_count": booking_count,
            "packages": packages,
            "consumption": consumption,
        }
