"""Sensores Winker: boletos em aberto, próximo vencimento, avisos, reservas, encomendas."""

from __future__ import annotations

from datetime import datetime

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_ID_PORTAL, CONF_PORTAL_NAME, DOMAIN
from .coordinator import WinkerCoordinator


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: WinkerCoordinator = hass.data[DOMAIN][entry.entry_id]
    name = entry.data.get(CONF_PORTAL_NAME, "Winker")
    id_portal = entry.data[CONF_ID_PORTAL]
    async_add_entities(
        [
            BoletosAbertosSensor(coordinator, entry, name, id_portal),
            ProximoVencimentoSensor(coordinator, entry, name, id_portal),
            AvisosSensor(coordinator, entry, name, id_portal),
            ReservasSensor(coordinator, entry, name, id_portal),
            EncomendasSensor(coordinator, entry, name, id_portal),
        ]
    )


class _Base(CoordinatorEntity[WinkerCoordinator], SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, entry, portal_name, id_portal, key, name) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_name = name
        self._attr_device_info = {
            "identifiers": {(DOMAIN, str(id_portal))},
            "name": f"Winker {portal_name}",
            "manufacturer": "Winker / Beelive",
        }


class BoletosAbertosSensor(_Base):
    _attr_icon = "mdi:file-document-alert"

    def __init__(self, c, e, pn, p) -> None:
        super().__init__(c, e, pn, p, "boletos_abertos", "Boletos em aberto")

    @property
    def native_value(self) -> int:
        return len(self.coordinator.data["billings_opened"])

    @property
    def extra_state_attributes(self) -> dict:
        boletos = []
        for b in self.coordinator.data["billings_opened"]:
            boletos.append(
                {
                    "referencia": b.get("reference"),
                    "vencimento": b.get("due_date"),
                    "valor": b.get("amount"),
                    "linha_digitavel": b.get("digitable_line"),
                    "pdf": b.get("file_url"),
                }
            )
        return {"boletos": boletos}


class ProximoVencimentoSensor(_Base):
    _attr_icon = "mdi:calendar-clock"
    _attr_device_class = "timestamp"

    def __init__(self, c, e, pn, p) -> None:
        super().__init__(c, e, pn, p, "proximo_vencimento", "Próximo vencimento")

    @property
    def native_value(self):
        abertos = self.coordinator.data["billings_opened"]
        datas = []
        for b in abertos:
            raw = b.get("due_date")
            if not raw:
                continue
            try:
                datas.append(datetime.fromisoformat(raw))
            except ValueError:
                continue
        return min(datas) if datas else None

    @property
    def extra_state_attributes(self) -> dict:
        abertos = self.coordinator.data["billings_opened"]
        valor = None
        if abertos:
            try:
                valor = min(
                    (b for b in abertos if b.get("due_date")),
                    key=lambda x: x["due_date"],
                ).get("amount")
            except (ValueError, KeyError):
                valor = None
        return {"valor": valor}


class AvisosSensor(_Base):
    _attr_icon = "mdi:bullhorn"

    def __init__(self, c, e, pn, p) -> None:
        super().__init__(c, e, pn, p, "avisos", "Avisos")

    @property
    def native_value(self) -> int:
        return len(self.coordinator.data["messages"])

    @property
    def extra_state_attributes(self) -> dict:
        msgs = self.coordinator.data["messages"][:10]
        return {
            "ultimos": [
                {"assunto": m.get("subject"), "data": m.get("created")} for m in msgs
            ]
        }


class ReservasSensor(_Base):
    _attr_icon = "mdi:calendar-check"

    def __init__(self, c, e, pn, p) -> None:
        super().__init__(c, e, pn, p, "reservas", "Reservas")

    @property
    def native_value(self) -> int:
        return self.coordinator.data["booking_count"]


class EncomendasSensor(_Base):
    _attr_icon = "mdi:package-variant-closed"

    def __init__(self, c, e, pn, p) -> None:
        super().__init__(c, e, pn, p, "encomendas", "Encomendas a retirar")

    @property
    def native_value(self) -> int:
        return len(self.coordinator.data["packages"])
