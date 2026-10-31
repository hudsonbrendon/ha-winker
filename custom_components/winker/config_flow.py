"""Config flow: email + senha -> login -> escolhe condomínio."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import WinkerApiError, WinkerAuthError, WinkerClient
from .const import CONF_ID_PORTAL, CONF_PORTAL_NAME, DOMAIN


class WinkerConfigFlow(ConfigFlow, domain=DOMAIN):
    """Fluxo em dois passos: credenciais, depois seleção de portal."""

    VERSION = 1

    def __init__(self) -> None:
        self._client: WinkerClient | None = None
        self._username: str | None = None
        self._password: str | None = None
        self._portals: list[dict] = []

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            session = async_get_clientsession(self.hass)
            client = WinkerClient(
                session, user_input[CONF_USERNAME], user_input[CONF_PASSWORD]
            )
            try:
                await client.login()
                self._portals = await client.get_portals()
            except WinkerAuthError:
                errors["base"] = "invalid_auth"
            except WinkerApiError:
                errors["base"] = "cannot_connect"
            else:
                if not self._portals:
                    errors["base"] = "no_portals"
                else:
                    self._client = client
                    self._username = user_input[CONF_USERNAME]
                    self._password = user_input[CONF_PASSWORD]
                    if len(self._portals) == 1:
                        return await self._create(self._portals[0])
                    return await self.async_step_portal()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {vol.Required(CONF_USERNAME): str, vol.Required(CONF_PASSWORD): str}
            ),
            errors=errors,
        )

    async def async_step_portal(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            chosen = next(
                p
                for p in self._portals
                if str(p["id_portal"]) == user_input[CONF_ID_PORTAL]
            )
            return await self._create(chosen)

        options = {str(p["id_portal"]): p.get("name", str(p["id_portal"])) for p in self._portals}
        return self.async_show_form(
            step_id="portal",
            data_schema=vol.Schema({vol.Required(CONF_ID_PORTAL): vol.In(options)}),
        )

    async def _create(self, portal: dict) -> ConfigFlowResult:
        id_portal = int(portal["id_portal"])
        await self.async_set_unique_id(f"{self._username}_{id_portal}")
        self._abort_if_unique_id_configured()
        return self.async_create_entry(
            title=f"{portal.get('name', 'Winker')}",
            data={
                CONF_USERNAME: self._username,
                CONF_PASSWORD: self._password,
                CONF_ID_PORTAL: id_portal,
                CONF_PORTAL_NAME: portal.get("name", "Winker"),
            },
        )
