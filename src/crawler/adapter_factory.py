# -*- coding: utf-8 -*-
"""adapter 工厂（REQ-DC-05）：按 --source 参数切换数据源，至少 2 源可插拔。"""
from __future__ import annotations

from typing import Union

from src.config import Config
from src.crawler.backup import BackupAdapter
from src.crawler.job51 import Job51Adapter

Adapter = Union[BackupAdapter, Job51Adapter]

SUPPORTED_SOURCES = ("backup", "job51")


def get_adapter(source: str, cfg: Config) -> Adapter:
    """返回数据源 adapter。

    - backup: 兜底 GitHub 数据集（当前主线数据源）
    - job51: 51job（W1 验证被 WAF 拦截，不可用，保留接口）
    """
    source = (source or "").lower()
    if source == "backup":
        return BackupAdapter(cfg.raw["crawler"]["backup_dataset"])
    if source == "job51":
        return Job51Adapter()
    raise ValueError(f"未知数据源 {source!r}，可选: {SUPPORTED_SOURCES}")
