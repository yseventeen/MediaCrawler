from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from tools import utils

from .bitable import BitableService, build_uniq_key
from .client import FeishuClient
from .config import FeishuConfig


def _stringify_meta(meta: Dict[str, Any]) -> str:
    try:
        return json.dumps(meta, ensure_ascii=False, separators=(",", ":"))
    except Exception:
        return ""


class FeishuBitableSync:
    """
    Sync suggestions to Feishu Bitable.

    飞书表格列名固定为：日期、关键词、类型、内容、唯一键、元数据（均为文本）。
    """

    def __init__(self, cfg: FeishuConfig):
        self._cfg = cfg
        self._cfg.validate()
        self._client = FeishuClient(cfg.app_id, cfg.app_secret)
        self._bitable = BitableService(self._client, cfg.bitable_app_token, cfg.bitable_table_id)

    async def upsert_suggestions(
        self,
        *,
        keyword: str,
        date_str: str,
        suggestion_type: str,
        texts: List[str],
        meta: Optional[Dict[str, Any]] = None,
    ) -> None:
        if not self._cfg.enabled:
            return
        meta = meta or {}
        c = self._cfg
        for t in texts:
            uniq = build_uniq_key(date_str, keyword, suggestion_type, t)
            fields = {
                c.field_date: date_str,
                c.field_keyword: keyword,
                c.field_type: suggestion_type,
                c.field_text: t,
                c.field_uniq_key: uniq,
                c.field_meta: _stringify_meta(meta),
            }
            if self._cfg.upsert:
                await self._bitable.upsert_by_uniq_key(
                    uniq, fields, uniq_key_field=c.field_uniq_key
                )
            else:
                await self._bitable.create_record(fields)


_singleton: Optional[FeishuBitableSync] = None


def get_sync_from_env() -> Optional[FeishuBitableSync]:
    global _singleton
    cfg = FeishuConfig.from_env()
    if not cfg.enabled:
        return None
    if _singleton is None:
        _singleton = FeishuBitableSync(cfg)
    return _singleton


async def sync_xhs_suggestions_to_feishu(
    *,
    keyword: str,
    date_str: str,
    recommend_texts: List[str],
    hot_query_texts: List[str],
    recommend_meta: Optional[Dict[str, Any]] = None,
    hot_query_meta: Optional[Dict[str, Any]] = None,
) -> None:
    syncer = get_sync_from_env()
    if not syncer:
        return
    try:
        await syncer.upsert_suggestions(
            keyword=keyword,
            date_str=date_str,
            suggestion_type="recommend",
            texts=recommend_texts,
            meta=recommend_meta,
        )
        await syncer.upsert_suggestions(
            keyword=keyword,
            date_str=date_str,
            suggestion_type="hot_query",
            texts=hot_query_texts,
            meta=hot_query_meta,
        )
        utils.logger.info("[Feishu] Synced xhs suggestions to Bitable")
    except Exception as e:
        # do not crash crawling
        utils.logger.warning(f"[Feishu] Sync failed: {e}")

