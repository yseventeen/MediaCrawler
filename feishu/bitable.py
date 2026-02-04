from __future__ import annotations

import hashlib
from typing import Any, AsyncIterator, Dict, Optional, Tuple

from .client import FeishuClient


def build_uniq_key(*parts: str) -> str:
    """
    Stable unique key for upsert.
    Use sha1 to keep short and URL-safe.
    """
    raw = "\u0001".join(p.strip() for p in parts)
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


class BitableService:
    def __init__(self, client: FeishuClient, app_token: str, table_id: str):
        self._client = client
        self._app_token = app_token
        self._table_id = table_id

    def _records_path(self) -> str:
        return f"/bitable/v1/apps/{self._app_token}/tables/{self._table_id}/records"

    async def list_records(self, *, page_size: int = 500) -> AsyncIterator[Dict[str, Any]]:
        """
        Iterate all records (pagination).
        Note: This is used for upsert lookup. For large tables, consider
        switching to server-side search with filters.
        """
        page_token: Optional[str] = None
        while True:
            params: Dict[str, Any] = {"page_size": page_size}
            if page_token:
                params["page_token"] = page_token
            data = await self._client.request("GET", self._records_path(), params=params)
            records = (((data.get("data") or {}).get("items")) or [])
            for r in records:
                yield r
            has_more = bool((data.get("data") or {}).get("has_more"))
            page_token = (data.get("data") or {}).get("page_token")
            if not has_more:
                break

    async def create_record(self, fields: Dict[str, Any]) -> Dict[str, Any]:
        payload = {"fields": fields}
        return await self._client.request("POST", self._records_path(), json=payload)

    async def update_record(self, record_id: str, fields: Dict[str, Any]) -> Dict[str, Any]:
        path = f"{self._records_path()}/{record_id}"
        payload = {"fields": fields}
        return await self._client.request("PUT", path, json=payload)

    async def upsert_by_uniq_key(
        self,
        uniq_key: str,
        fields: Dict[str, Any],
        *,
        uniq_key_field: str = "uniq_key",
    ) -> Tuple[str, str]:
        """
        Upsert by scanning existing records for matching field value.
        Returns (action, record_id): action in {"created","updated"}.
        """
        record_id = None
        async for record in self.list_records():
            f = record.get("fields") or {}
            if f.get(uniq_key_field) == uniq_key:
                record_id = record.get("record_id")
                break

        if record_id:
            await self.update_record(record_id, fields)
            return "updated", record_id
        res = await self.create_record(fields)
        rid = ((res.get("data") or {}).get("record") or {}).get("record_id") or ""
        return "created", rid

