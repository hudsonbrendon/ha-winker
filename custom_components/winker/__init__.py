"""Integração Winker (app Beelive) para Home Assistant."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import WinkerApiError, WinkerAuthError, WinkerClient
from .const import CONF_ID_PORTAL, DOMAIN
from .coordinator import WinkerCoordinator

PLATFORMS = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    session = async_get_clientsession(hass)
    client = WinkerClient(
        session, entry.data[CONF_USERNAME], entry.data[CONF_PASSWORD]
    )
    try:
        await client.login()
    except WinkerAuthError as err:
        raise ConfigEntryAuthFailed(str(err)) from err
    except WinkerApiError as err:
        raise ConfigEntryNotReady(str(err)) from err

    coordinator = WinkerCoordinator(hass, client, entry.data[CONF_ID_PORTAL])
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unloaded
