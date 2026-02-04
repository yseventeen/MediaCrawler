from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

import httpx


@dataclass
class _TokenCache:
    token: str = ""
    expire_at: float = 0.0  # epoch seconds

    def valid(self) -> bool:
        # keep a small buffer
        return bool(self.token) and time.time() < (self.expire_at - 30)


class FeishuClient:
    """
    Minimal Feishu OpenAPI client for:
    - tenant_access_token (internal app)
    - bitable records CRUD
    """

    def __init__(self, app_id: str, app_secret: str, *, timeout: float = 30.0):
        self._app_id = app_id
        self._app_secret = app_secret
        self._timeout = timeout
        self._base = "https://open.feishu.cn/open-apis"
        self._token_cache = _TokenCache()

    async def _tenant_access_token(self) -> str:
        if self._token_cache.valid():
            return self._token_cache.token

        url = f"{self._base}/auth/v3/tenant_access_token/internal"
        payload = {"app_id": self._app_id, "app_secret": self._app_secret}
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
        if data.get("code") != 0:
            raise RuntimeError(f"Feishu token error: code={data.get('code')} msg={data.get('msg')}")
        token = data["tenant_access_token"]
        expire = int(data.get("expire", 3600))
        self._token_cache.token = token
        self._token_cache.expire_at = time.time() + expire
        return token

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        token = await self._tenant_access_token()
        url = f"{self._base}{path}"
        headers = {"Authorization": f"Bearer {token}"}
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.request(method, url, headers=headers, params=params, json=json)
            resp.raise_for_status()
            data = resp.json()
        # Bitable typically returns code=0 for success
        if isinstance(data, dict) and data.get("code") not in (None, 0):
            raise RuntimeError(f"Feishu API error: code={data.get('code')} msg={data.get('msg')}")
        return data

