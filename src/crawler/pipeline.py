# -*- coding: utf-8 -*-
"""采集主流程（REQ-DC-03/05/07）：
- 按 --source 选择 adapter（可插拔）
- 幂等写入 jobs（ON DUPLICATE 更新最新状态）+ 快照按批次追加
- 健康监控统计输出
- 重复运行：jobs 不增行，job_snapshots 按批次增加（增量语义）
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from src.config import Config
from src.crawler.adapter_factory import get_adapter
from src.crawler.monitor import HealthMonitor
from src.storage import insert_snapshots, upsert_jobs

logger = logging.getLogger(__name__)


@dataclass
class CrawlResult:
    source: str
    crawl_date: datetime
    jobs_total: int = 0          # 本次写入 jobs 行数（upsert 口径）
    valid_total: int = 0         # 其中 is_valid=1 数
    snapshots_added: int = 0     # 本次新增快照数
    monitor_rows: list = field(default_factory=list)
    warnings: list = field(default_factory=list)


def run_crawl(cfg: Config, source: str = "backup",
              crawl_date: Optional[datetime] = None) -> CrawlResult:
    """执行一次采集批次。source: backup | job51（当前 job51 不可用）。"""
    crawl_date = crawl_date or datetime.now()
    adapter = get_adapter(source, cfg)

    if source == "backup":
        jobs, snaps = adapter.import_all(crawl_date)
        n_upsert = upsert_jobs(jobs, cfg)
        n_snap = insert_snapshots(snaps, cfg)
        valid = sum(1 for j in jobs if j["is_valid"] == 1)

        # 健康监控：按 城市×大类 统计（backup 为本地导入，请求=命中=条数）
        monitor = HealthMonitor(cfg.raw["crawler"].get("alert_hit_rate", 0.30))
        from collections import defaultdict

        combo: dict[tuple[str, str], int] = defaultdict(int)
        for j in jobs:
            combo[(j["city"], j["job_category"])] += 1
        for (city, cat), n in combo.items():
            monitor.record_request(city, cat, ok=True, hits=n)
        logger.info(monitor.report())

        result = CrawlResult(
            source=source, crawl_date=crawl_date,
            jobs_total=len(jobs), valid_total=valid,
            snapshots_added=n_snap,
            monitor_rows=monitor.summary()["rows"],
        )
        logger.info(
            "采集完成: source=%s jobs_total=%d valid=%d snapshots_added=%d",
            source, result.jobs_total, result.valid_total, result.snapshots_added,
        )
        return result

    # job51（W1 验证不可用）
    from src.crawler.job51 import Job51Adapter

    reason = Job51Adapter.availability()
    logger.error("数据源 %s 不可用: %s", source, reason)
    result = CrawlResult(source=source, crawl_date=crawl_date)
    result.warnings.append(reason)
    return result
