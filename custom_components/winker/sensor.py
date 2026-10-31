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
            ConsumoSensor(coordinator, entry, name, id_portal),
            ManutencoesSensor(coordinator, entry, name, id_portal),
            AssembleiasSensor(coordinator, entry, name, id_portal),
            DocumentosSensor(coordinator, entry, name, id_portal),
            EspacosSensor(coordinator, entry, name, id_portal),
            VeiculosSensor(coordinator, entry, name, id_portal),
            PetsSensor(coordinator, entry, name, id_portal),
            ChavesSensor(coordinator, entry, name, id_portal),
            UnidadeSensor(coordinator, entry, name, id_portal),
        ]
    )


def _parse_dt(raw: str | None):
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw)
    except ValueError:
        return None


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


class ConsumoSensor(_Base):
    """Leituras de água/gás. Fica 0 se a medição não estiver ativa no condomínio."""

    _attr_icon = "mdi:water-meter"

    def __init__(self, c, e, pn, p) -> None:
        super().__init__(c, e, pn, p, "consumo", "Leituras de consumo")

    @property
    def native_value(self) -> int:
        return len(self.coordinator.data.get("consumption", []))

    @property
    def extra_state_attributes(self) -> dict:
        return {"leituras": self.coordinator.data.get("consumption", [])[:12]}


class ManutencoesSensor(_Base):
    """Manutenções acompanhadas pelo condomínio."""

    _attr_icon = "mdi:wrench-clock"

    def __init__(self, c, e, pn, p) -> None:
        super().__init__(c, e, pn, p, "manutencoes", "Manutenções")

    @property
    def native_value(self) -> int:
        return len(self.coordinator.data.get("maintenance", []))

    @property
    def extra_state_attributes(self) -> dict:
        itens = self.coordinator.data.get("maintenance", [])
        datas = [d for d in (_parse_dt(m.get("next_notification")) for m in itens) if d]
        agora = datetime.now().astimezone()
        futuras = [d for d in datas if d >= agora]
        return {
            "proxima": min(futuras).isoformat() if futuras else None,
            "atrasadas": len(datas) - len(futuras),
            "itens": [
                {"nome": (m.get("name") or "").strip(), "proxima": m.get("next_notification")}
                for m in itens
            ],
        }


class AssembleiasSensor(_Base):
    """Assembleias / reuniões do condomínio."""

    _attr_icon = "mdi:gavel"

    def __init__(self, c, e, pn, p) -> None:
        super().__init__(c, e, pn, p, "assembleias", "Assembleias")

    @property
    def native_value(self) -> int:
        return len(self.coordinator.data.get("meetings", []))

    @property
    def extra_state_attributes(self) -> dict:
        return {
            "reunioes": [
                {"nome": m.get("name"), "tipo": m.get("type")}
                for m in self.coordinator.data.get("meetings", [])
            ]
        }


class DocumentosSensor(_Base):
    """Total de documentos disponíveis, por categoria."""

    _attr_icon = "mdi:file-document-multiple"

    def __init__(self, c, e, pn, p) -> None:
        super().__init__(c, e, pn, p, "documentos", "Documentos")

    @property
    def native_value(self) -> int:
        return sum(
            int(t.get("count_documents") or 0)
            for t in self.coordinator.data.get("document_types", [])
        )

    @property
    def extra_state_attributes(self) -> dict:
        return {
            "por_categoria": {
                t.get("name"): int(t.get("count_documents") or 0)
                for t in self.coordinator.data.get("document_types", [])
            }
        }


class EspacosSensor(_Base):
    """Espaços reserváveis (churrasqueira, salão, quadra...)."""

    _attr_icon = "mdi:home-city"

    def __init__(self, c, e, pn, p) -> None:
        super().__init__(c, e, pn, p, "espacos", "Espaços reserváveis")

    @property
    def native_value(self) -> int:
        return len(self.coordinator.data.get("booking_resources", []))

    @property
    def extra_state_attributes(self) -> dict:
        return {
            "espacos": [
                (r.get("name") or "").strip()
                for r in self.coordinator.data.get("booking_resources", [])
            ]
        }


class VeiculosSensor(_Base):
    _attr_icon = "mdi:car"

    def __init__(self, c, e, pn, p) -> None:
        super().__init__(c, e, pn, p, "veiculos", "Veículos cadastrados")

    @property
    def native_value(self) -> int:
        return len(self.coordinator.data.get("me", {}).get("vehicles") or [])

    @property
    def extra_state_attributes(self) -> dict:
        return {"veiculos": self.coordinator.data.get("me", {}).get("vehicles") or []}


class PetsSensor(_Base):
    _attr_icon = "mdi:paw"

    def __init__(self, c, e, pn, p) -> None:
        super().__init__(c, e, pn, p, "pets", "Pets cadastrados")

    @property
    def native_value(self) -> int:
        return len(self.coordinator.data.get("me", {}).get("pets") or [])

    @property
    def extra_state_attributes(self) -> dict:
        return {"pets": self.coordinator.data.get("me", {}).get("pets") or []}


class ChavesSensor(_Base):
    _attr_icon = "mdi:key-variant"

    def __init__(self, c, e, pn, p) -> None:
        super().__init__(c, e, pn, p, "chaves", "Chaves retiradas")

    @property
    def native_value(self) -> int:
        return len(self.coordinator.data.get("keys_withdrawn", []))


class UnidadeSensor(_Base):
    """Minha unidade (apto/bloco) e seus dados."""

    _attr_icon = "mdi:door"

    def __init__(self, c, e, pn, p) -> None:
        super().__init__(c, e, pn, p, "unidade", "Unidade")

    def _unit(self) -> dict:
        units = self.coordinator.data.get("units") or []
        return units[0] if units else {}

    @property
    def native_value(self):
        u = self._unit()
        name = (u.get("name") or "").strip()
        div = (u.get("division") or "").strip()
        return f"{name} - {div}" if div else (name or None)

    @property
    def extra_state_attributes(self) -> dict:
        u = self._unit()
        me = self.coordinator.data.get("me", {})
        return {
            "bloco": u.get("division"),
            "setor": u.get("sector"),
            "vaga": u.get("parking_spot"),
            "area": u.get("area"),
            "fracao_ideal": u.get("fractional_ownership"),
            "morador": me.get("name"),
            "perfil": (u.get("responsibles") or [{}])[0].get("responsible_type")
            if u.get("responsibles")
            else None,
        }
