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
        p = self._id_portal

        async def safe(coro, default):
            """Um endpoint que falhe não zera os demais sensores."""
            try:
                return await coro
            except WinkerApiError as err:
                _LOGGER.debug("Winker endpoint falhou: %s", err)
                return default

        # 'me' é a sonda de sessão: se cair aqui, a atualização toda falha (re-login).
        try:
            me = await self._client.get_me()
        except WinkerApiError as err:
            raise UpdateFailed(str(err)) from err

        billings = await safe(self._client.get_billings(p), [])
        data = {
            "me": me,
            "units": await safe(self._client.get_my_units(p), []),
            "billings": billings,
            "billings_opened": [b for b in billings if b.get("situation") == "opened"],
            "messages": await safe(self._client.get_messages(p), []),
            "booking_count": await safe(self._client.get_booking_count(p), 0),
            "booking_resources": await safe(self._client.get_booking_resources(p), []),
            "packages": await safe(self._client.get_packages_todeliver(p), []),
            "maintenance": await safe(self._client.get_maintenance(p), []),
            "meetings": await safe(self._client.get_meetings(p), []),
            "document_types": await safe(self._client.get_document_types(p), []),
            "keys_withdrawn": await safe(self._client.get_keys_withdrawn(p), []),
            "consumption": await safe(self._client.get_consumption(p), []),
        }
        return data
