from __future__ import annotations

import os
from dataclasses import dataclass


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "t", "y", "yes", "on")


def _env_str(name: str, default: str = "") -> str:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip()


# ========== Suggestions 表列名（写死） ==========
FEISHU_FIELD_DATE = "日期"
FEISHU_FIELD_KEYWORD = "关键词"
FEISHU_FIELD_TYPE = "类型"
FEISHU_FIELD_TEXT = "内容"
FEISHU_FIELD_UNIQ_KEY = "唯一键"
FEISHU_FIELD_META = "元数据"

# ========== Comments 表列名（写死） ==========
FEISHU_COMMENT_评论ID = "评论ID"
FEISHU_COMMENT_创建时间 = "创建时间"
FEISHU_COMMENT_IP归属地 = "IP归属地"
FEISHU_COMMENT_笔记ID = "笔记ID"
FEISHU_COMMENT_评论内容 = "评论内容"
FEISHU_COMMENT_用户ID = "用户ID"
FEISHU_COMMENT_昵称 = "昵称"
FEISHU_COMMENT_头像 = "头像"
FEISHU_COMMENT_子评论数 = "子评论数"
FEISHU_COMMENT_图片 = "图片"
FEISHU_COMMENT_父评论ID = "父评论ID"
FEISHU_COMMENT_最后修改时间 = "最后修改时间"
FEISHU_COMMENT_点赞数 = "点赞数"
FEISHU_COMMENT_元数据 = "元数据"

# ========== Contents 表列名（写死） ==========
FEISHU_CONTENT_笔记ID = "笔记ID"
FEISHU_CONTENT_类型 = "类型"
FEISHU_CONTENT_标题 = "标题"
FEISHU_CONTENT_描述 = "描述"
FEISHU_CONTENT_视频链接 = "视频链接"
FEISHU_CONTENT_发布时间 = "发布时间"
FEISHU_CONTENT_最后更新时间 = "最后更新时间"
FEISHU_CONTENT_用户ID = "用户ID"
FEISHU_CONTENT_昵称 = "昵称"
FEISHU_CONTENT_头像 = "头像"
FEISHU_CONTENT_点赞数 = "点赞数"
FEISHU_CONTENT_收藏数 = "收藏数"
FEISHU_CONTENT_评论数 = "评论数"
FEISHU_CONTENT_分享数 = "分享数"
FEISHU_CONTENT_IP归属地 = "IP归属地"
FEISHU_CONTENT_图片列表 = "图片列表"
FEISHU_CONTENT_标签列表 = "标签列表"
FEISHU_CONTENT_最后修改时间戳 = "最后修改时间戳"
FEISHU_CONTENT_笔记链接 = "笔记链接"
FEISHU_CONTENT_来源关键词 = "来源关键词"
FEISHU_CONTENT_安全令牌 = "安全令牌"
FEISHU_CONTENT_元数据 = "元数据"


@dataclass(frozen=True)
class FeishuConfig:
    enabled: bool
    app_id: str
    app_secret: str
    bitable_app_token: str
    bitable_table_id: str  # suggestions 表（兼容旧配置 FEISHU_BITABLE_TABLE_ID）
    bitable_table_id_comments: str
    bitable_table_id_contents: str
    upsert: bool
    field_date: str
    field_keyword: str
    field_type: str
    field_text: str
    field_uniq_key: str
    field_meta: str

    @staticmethod
    def from_env() -> "FeishuConfig":
        table_id = _env_str("FEISHU_BITABLE_TABLE_ID") or _env_str("FEISHU_BITABLE_TABLE_ID_SUGGESTIONS")
        return FeishuConfig(
            enabled=_env_bool("FEISHU_ENABLED", False),
            app_id=os.getenv("FEISHU_APP_ID", "").strip(),
            app_secret=os.getenv("FEISHU_APP_SECRET", "").strip(),
            bitable_app_token=os.getenv("FEISHU_BITABLE_APP_TOKEN", "").strip(),
            bitable_table_id=table_id,
            bitable_table_id_comments=_env_str("FEISHU_BITABLE_TABLE_ID_COMMENTS"),
            bitable_table_id_contents=_env_str("FEISHU_BITABLE_TABLE_ID_CONTENTS"),
            upsert=_env_bool("FEISHU_UPSERT", True),
            field_date=FEISHU_FIELD_DATE,
            field_keyword=FEISHU_FIELD_KEYWORD,
            field_type=FEISHU_FIELD_TYPE,
            field_text=FEISHU_FIELD_TEXT,
            field_uniq_key=FEISHU_FIELD_UNIQ_KEY,
            field_meta=FEISHU_FIELD_META,
        )

    def validate(self) -> None:
        if not self.enabled:
            return
        missing = []
        if not self.app_id:
            missing.append("FEISHU_APP_ID")
        if not self.app_secret:
            missing.append("FEISHU_APP_SECRET")
        if not self.bitable_app_token:
            missing.append("FEISHU_BITABLE_APP_TOKEN")
        if not self.bitable_table_id and not self.bitable_table_id_comments and not self.bitable_table_id_contents:
            missing.append("至少配置 FEISHU_BITABLE_TABLE_ID 或 FEISHU_BITABLE_TABLE_ID_COMMENTS 或 FEISHU_BITABLE_TABLE_ID_CONTENTS")
        if missing:
            raise ValueError(f"Feishu enabled but missing env: {', '.join(missing)}")

