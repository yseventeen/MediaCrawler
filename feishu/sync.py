from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from tools import utils

from .bitable import BitableService, build_uniq_key
from .client import FeishuClient
from .config import (
    FeishuConfig,
    FEISHU_COMMENT_IP归属地,
    FEISHU_COMMENT_创建时间,
    FEISHU_COMMENT_点赞数,
    FEISHU_COMMENT_图片,
    FEISHU_COMMENT_子评论数,
    FEISHU_COMMENT_昵称,
    FEISHU_COMMENT_最后修改时间,
    FEISHU_COMMENT_评论ID,
    FEISHU_COMMENT_评论内容,
    FEISHU_COMMENT_笔记ID,
    FEISHU_COMMENT_用户ID,
    FEISHU_COMMENT_父评论ID,
    FEISHU_COMMENT_头像,
    FEISHU_COMMENT_元数据,
    FEISHU_CONTENT_IP归属地,
    FEISHU_CONTENT_分享数,
    FEISHU_CONTENT_点赞数,
    FEISHU_CONTENT_图片列表,
    FEISHU_CONTENT_安全令牌,
    FEISHU_CONTENT_收藏数,
    FEISHU_CONTENT_描述,
    FEISHU_CONTENT_最后更新时间,
    FEISHU_CONTENT_最后修改时间戳,
    FEISHU_CONTENT_昵称,
    FEISHU_CONTENT_笔记ID,
    FEISHU_CONTENT_笔记链接,
    FEISHU_CONTENT_用户ID,
    FEISHU_CONTENT_标题,
    FEISHU_CONTENT_标签列表,
    FEISHU_CONTENT_来源关键词,
    FEISHU_CONTENT_评论数,
    FEISHU_CONTENT_发布时间,
    FEISHU_CONTENT_头像,
    FEISHU_CONTENT_类型,
    FEISHU_CONTENT_视频链接,
    FEISHU_CONTENT_元数据,
)


def _stringify_meta(meta: Dict[str, Any]) -> str:
    try:
        return json.dumps(meta, ensure_ascii=False, separators=(",", ":"))
    except Exception:
        return ""


def _to_str(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, str):
        return v
    return str(v)


def _to_json(obj: Any) -> str:
    """单条完整数据的 JSON 字符串，用于写入「元数据」列。"""
    try:
        return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
    except Exception:
        return ""


class FeishuBitableSync:
    """
    同步到飞书多维表格：suggestions / comments / contents 三张表，列名均在 config 中写死。
    """

    def __init__(self, cfg: FeishuConfig):
        self._cfg = cfg
        self._cfg.validate()
        self._client = FeishuClient(cfg.app_id, cfg.app_secret)
        self._bitable = (
            BitableService(self._client, cfg.bitable_app_token, cfg.bitable_table_id)
            if cfg.bitable_table_id
            else None
        )
        self._bitable_comments = (
            BitableService(self._client, cfg.bitable_app_token, cfg.bitable_table_id_comments)
            if cfg.bitable_table_id_comments
            else None
        )
        self._bitable_contents = (
            BitableService(self._client, cfg.bitable_app_token, cfg.bitable_table_id_contents)
            if cfg.bitable_table_id_contents
            else None
        )
        # 启动时打一条日志，方便确认评论/内容是否配置了表 ID
        tables = []
        if self._bitable:
            tables.append("suggestions")
        if self._bitable_comments:
            tables.append("comments")
        if self._bitable_contents:
            tables.append("contents")
        utils.logger.info(
            f"[Feishu] Bitable sync enabled for: {', '.join(tables) or 'none'}. "
            "To sync comments/contents, set FEISHU_BITABLE_TABLE_ID_COMMENTS and FEISHU_BITABLE_TABLE_ID_CONTENTS in .env"
        )

    async def upsert_suggestions(
        self,
        *,
        keyword: str,
        date_str: str,
        suggestion_type: str,
        texts: List[str],
        meta: Optional[Dict[str, Any]] = None,
    ) -> None:
        if not self._cfg.enabled or not self._bitable:
            return
        meta = meta or {}
        c = self._cfg
        for t in texts:
            uniq = build_uniq_key(date_str, keyword, suggestion_type, t)
            full_record = {
                "日期": date_str,
                "关键词": keyword,
                "类型": suggestion_type,
                "内容": t,
                "唯一键": uniq,
                "extra_meta": meta,
            }
            fields = {
                c.field_date: date_str,
                c.field_keyword: keyword,
                c.field_type: suggestion_type,
                c.field_text: t,
                c.field_uniq_key: uniq,
                c.field_meta: _to_json(full_record),
            }
            if self._cfg.upsert:
                await self._bitable.upsert_by_uniq_key(
                    uniq, fields, uniq_key_field=c.field_uniq_key
                )
            else:
                await self._bitable.create_record(fields)

    async def upsert_comment(self, comment_item: Dict[str, Any]) -> None:
        """同步单条评论到飞书 comments 表，列名写死见 config。"""
        if not self._cfg.enabled or not self._bitable_comments:
            return
        d = comment_item
        uniq = _to_str(d.get("comment_id"))
        if not uniq:
            return
        fields = {
            FEISHU_COMMENT_评论ID: _to_str(d.get("comment_id")),
            FEISHU_COMMENT_创建时间: _to_str(d.get("create_time")),
            FEISHU_COMMENT_IP归属地: _to_str(d.get("ip_location")),
            FEISHU_COMMENT_笔记ID: _to_str(d.get("note_id")),
            FEISHU_COMMENT_评论内容: _to_str(d.get("content")),
            FEISHU_COMMENT_用户ID: _to_str(d.get("user_id")),
            FEISHU_COMMENT_昵称: _to_str(d.get("nickname")),
            FEISHU_COMMENT_头像: _to_str(d.get("avatar")),
            FEISHU_COMMENT_子评论数: _to_str(d.get("sub_comment_count")),
            FEISHU_COMMENT_图片: _to_str(d.get("pictures")),
            FEISHU_COMMENT_父评论ID: _to_str(d.get("parent_comment_id")),
            FEISHU_COMMENT_最后修改时间: _to_str(d.get("last_modify_ts")),
            FEISHU_COMMENT_点赞数: _to_str(d.get("like_count")),
            FEISHU_COMMENT_元数据: _to_json(comment_item),
        }
        if self._cfg.upsert:
            await self._bitable_comments.upsert_by_uniq_key(
                uniq, fields, uniq_key_field=FEISHU_COMMENT_评论ID
            )
        else:
            await self._bitable_comments.create_record(fields)

    async def upsert_content(self, content_item: Dict[str, Any]) -> None:
        """同步单条笔记/内容到飞书 contents 表，列名写死见 config。"""
        if not self._cfg.enabled or not self._bitable_contents:
            return
        d = content_item
        uniq = _to_str(d.get("note_id"))
        if not uniq:
            return
        fields = {
            FEISHU_CONTENT_笔记ID: _to_str(d.get("note_id")),
            FEISHU_CONTENT_类型: _to_str(d.get("type")),
            FEISHU_CONTENT_标题: _to_str(d.get("title")),
            FEISHU_CONTENT_描述: _to_str(d.get("desc")),
            FEISHU_CONTENT_视频链接: _to_str(d.get("video_url")),
            FEISHU_CONTENT_发布时间: _to_str(d.get("time")),
            FEISHU_CONTENT_最后更新时间: _to_str(d.get("last_update_time")),
            FEISHU_CONTENT_用户ID: _to_str(d.get("user_id")),
            FEISHU_CONTENT_昵称: _to_str(d.get("nickname")),
            FEISHU_CONTENT_头像: _to_str(d.get("avatar")),
            FEISHU_CONTENT_点赞数: _to_str(d.get("liked_count")),
            FEISHU_CONTENT_收藏数: _to_str(d.get("collected_count")),
            FEISHU_CONTENT_评论数: _to_str(d.get("comment_count")),
            FEISHU_CONTENT_分享数: _to_str(d.get("share_count")),
            FEISHU_CONTENT_IP归属地: _to_str(d.get("ip_location")),
            FEISHU_CONTENT_图片列表: _to_str(d.get("image_list")),
            FEISHU_CONTENT_标签列表: _to_str(d.get("tag_list")),
            FEISHU_CONTENT_最后修改时间戳: _to_str(d.get("last_modify_ts")),
            FEISHU_CONTENT_笔记链接: _to_str(d.get("note_url")),
            FEISHU_CONTENT_来源关键词: _to_str(d.get("source_keyword")),
            FEISHU_CONTENT_安全令牌: _to_str(d.get("xsec_token")),
            FEISHU_CONTENT_元数据: _to_json(content_item),
        }
        if self._cfg.upsert:
            await self._bitable_contents.upsert_by_uniq_key(
                uniq, fields, uniq_key_field=FEISHU_CONTENT_笔记ID
            )
        else:
            await self._bitable_contents.create_record(fields)


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


async def sync_xhs_comment_to_feishu(comment_item: Dict[str, Any]) -> None:
    """将单条 XHS 评论同步到飞书 comments 表（search/detail/creator 三种模式产出均会调用）。"""
    syncer = get_sync_from_env()
    if not syncer:
        return
    try:
        await syncer.upsert_comment(comment_item)
    except Exception as e:
        utils.logger.warning(f"[Feishu] Sync comment failed: {e}")


async def sync_xhs_content_to_feishu(content_item: Dict[str, Any]) -> None:
    """将单条 XHS 笔记/内容同步到飞书 contents 表（search/detail/creator 三种模式产出均会调用）。"""
    syncer = get_sync_from_env()
    if not syncer:
        return
    try:
        await syncer.upsert_content(content_item)
    except Exception as e:
        utils.logger.warning(f"[Feishu] Sync content failed: {e}")

