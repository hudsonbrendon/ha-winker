"""Cliente da API Winker (plataforma por trás do app Beelive).

Contrato derivado por engenharia reversa do app Cordova/Ionic
`br.com.winker.wl.beelive` e confirmado contra a API ao vivo:

- POST /auth/login  body {username, password, key=APP_KEY} -> {token, ...}
- Header de auth: `Authorization: <token>` (JWT cru, SEM prefixo "Bearer").
- GET  /me/portals                                   -> [{id_portal, name}]
- GET  /billing_unit?id_portal=                       -> boletos
- GET  /message?id_portal=                            -> avisos/comunicados
- GET  /booking/mybookings/count?id_portal=           -> [n] reservas
- GET  /package/todeliver?id_portal= , /package/delivered?id_portal=  (204 = vazio)
"""

from __future__ import annotations

import logging

from aiohttp import ClientSession

from .const import (
    APP_KEY,
    APP_VERSION,
    BASE_URL,
    CONSUMPTION_BEARER,
    CONSUMPTION_URL,
)

_LOGGER = logging.getLogger(__name__)


class WinkerAuthError(Exception):
    """Usuário/senha inválidos ou sessão expirada."""


class WinkerApiError(Exception):
    """Erro genérico da API."""


class WinkerClient:
    """Cliente mínimo e stateful (guarda o token, re-loga no 401)."""

    def __init__(self, session: ClientSession, username: str, password: str) -> None:
        self._session = session
        self._username = username
        self._password = password
        self._token: str | None = None

    def _headers(self) -> dict[str, str]:
        h = {"Accept": "application/json", "X-Client-Version": APP_VERSION}
        if self._token:
            h["Authorization"] = self._token
        return h

    async def login(self) -> dict:
        """Autentica e guarda o token. Levanta WinkerAuthError em credencial errada."""
        payload = {
            "username": self._username,
            "password": self._password,
            "key": APP_KEY,
        }
        async with self._session.post(
            f"{BASE_URL}/auth/login",
            json=payload,
            headers={"Accept": "application/json", "X-Client-Version": APP_VERSION},
        ) as resp:
            data = await _safe_json(resp)
            if resp.status == 400 or (isinstance(data, dict) and data.get("code") == 400):
                raise WinkerAuthError(
                    data.get("description", "Usuário ou senha incorretos.")
                    if isinstance(data, dict)
                    else "Usuário ou senha incorretos."
                )
            if resp.status != 200 or not isinstance(data, dict) or "token" not in data:
                raise WinkerApiError(f"Login falhou: HTTP {resp.status}")
            self._token = data["token"]
            return data

    async def _get(self, path: str, *, _retry: bool = True):
        """GET autenticado; re-loga uma vez no 401/403. 204 -> None."""
        if not self._token:
            await self.login()
        async with self._session.get(
            f"{BASE_URL}/{path}", headers=self._headers()
        ) as resp:
            if resp.status in (401, 403) and _retry:
                self._token = None
                await self.login()
                return await self._get(path, _retry=False)
            if resp.status == 204:
                return None
            if resp.status != 200:
                raise WinkerApiError(f"GET {path} -> HTTP {resp.status}")
            return await _safe_json(resp)

    async def get_portals(self) -> list[dict]:
        """Lista os condomínios do usuário: [{id_portal, name}, ...]."""
        data = await self._get("me/portals")
        return data if isinstance(data, list) else []

    async def get_billings(self, id_portal: int) -> list[dict]:
        data = await self._get(f"billing_unit?id_portal={id_portal}")
        return data if isinstance(data, list) else []

    async def get_messages(self, id_portal: int) -> list[dict]:
        data = await self._get(f"message?id_portal={id_portal}")
        return data if isinstance(data, list) else []

    async def get_booking_count(self, id_portal: int) -> int:
        data = await self._get(f"booking/mybookings/count?id_portal={id_portal}")
        if isinstance(data, list) and data:
            try:
                return int(data[0])
            except (TypeError, ValueError):
                return 0
        return 0

    async def get_packages_todeliver(self, id_portal: int) -> list[dict]:
        data = await self._get(f"package/todeliver?id_portal={id_portal}")
        return data if isinstance(data, list) else []

    async def get_consumption(self, id_portal: int) -> list[dict]:
        """Leituras de água/gás (API separada, Bearer fixo). [] se não houver."""
        async with self._session.get(
            f"{CONSUMPTION_URL}/consumption/list?id_portal={id_portal}",
            headers={"Accept": "application/json", "Authorization": CONSUMPTION_BEARER},
        ) as resp:
            if resp.status != 200:
                return []
            data = await _safe_json(resp)
        if isinstance(data, dict) and data.get("success"):
            ret = data.get("return")
            return ret if isinstance(ret, list) else []
        return []


async def _safe_json(resp):
    try:
        return await resp.json(content_type=None)
    except Exception:  # noqa: BLE001 - corpo vazio ou não-JSON
        return None
