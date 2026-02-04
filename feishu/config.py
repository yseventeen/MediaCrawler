from __future__ import annotations

import os
from dataclasses import dataclass


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "t", "y", "yes", "on")


# Bitable 列名写死为以下中文（与飞书表格列名一致）
FEISHU_FIELD_DATE = "日期"
FEISHU_FIELD_KEYWORD = "关键词"
FEISHU_FIELD_TYPE = "类型"
FEISHU_FIELD_TEXT = "内容"
FEISHU_FIELD_UNIQ_KEY = "唯一键"
FEISHU_FIELD_META = "元数据"


@dataclass(frozen=True)
class FeishuConfig:
    enabled: bool
    app_id: str
    app_secret: str
    bitable_app_token: str
    bitable_table_id: str
    upsert: bool
    field_date: str
    field_keyword: str
    field_type: str
    field_text: str
    field_uniq_key: str
    field_meta: str

    @staticmethod
    def from_env() -> "FeishuConfig":
        return FeishuConfig(
            enabled=_env_bool("FEISHU_ENABLED", False),
            app_id=os.getenv("FEISHU_APP_ID", "").strip(),
            app_secret=os.getenv("FEISHU_APP_SECRET", "").strip(),
            bitable_app_token=os.getenv("FEISHU_BITABLE_APP_TOKEN", "").strip(),
            bitable_table_id=os.getenv("FEISHU_BITABLE_TABLE_ID", "").strip(),
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
        if not self.bitable_table_id:
            missing.append("FEISHU_BITABLE_TABLE_ID")
        if missing:
            raise ValueError(f"Feishu enabled but missing env: {', '.join(missing)}")

