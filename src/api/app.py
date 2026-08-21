# -*- coding: utf-8 -*-
"""JobPulse REST API（FastAPI）：前后端分离后的后端服务。

接口一览：
- GET  /api/health            健康检查（jobs/snapshots 计数 + DB 驱动）
- GET  /api/jobs/summary      看板聚合数据（summary + 5 图表模块，支持城市/类别/学历筛选）
- GET  /api/jobs              岗位明细分页（筛选 + 关键词搜索，含技能字段）
- POST /api/model/predict     薪资预测（模型文件存在时可用）
- 静态托管 web/dist（前端构建产物，单端口部署）
"""
from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Optional

import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.config import Config, load_config
from src.storage import count_jobs, count_snapshots, fetch_jobs_for_analysis
from src.viz.dashboard import _load_features, build_dashboard_data
from src.api import stats as stats_mod

logger = logging.getLogger(__name__)

# 全量看板数据缓存：features.parquet 变更或超时后自动重建（7k 行全量 merge 没必要每次请求做）
_cache: dict = {"data": None, "features_mtime": None, "at": 0.0}
CACHE_TTL = 60.0


def _full_data(cfg: Config) -> dict:
    """加载全量看板数据（summary + records，复用 viz.build_dashboard_data）。"""
    now = time.time()
    feat_path = Path(cfg.raw["paths"]["features_path"])
    mtime = feat_path.stat().st_mtime if feat_path.exists() else None
    cached = _cache["data"]
    if (cached is not None and _cache["features_mtime"] == mtime
            and now - _cache["at"] < CACHE_TTL):
        return cached
    df = fetch_jobs_for_analysis(cfg, valid_only=True)
    data = build_dashboard_data(df, _load_features(cfg))
    _cache.update(data=data, features_mtime=mtime, at=now)
    return data


# ---------------------------------------------------------------- 岗位明细查询
def _query_jobs(cfg: Config, city: str | None = None, category: str | None = None,
                education: str | None = None, experience: str | None = None,
                job_type: str | None = None, keyword: str | None = None,
                source: str | None = None,
                page: int = 1, page_size: int = 20,
                sort_by: str = "crawl_date", order: str = "desc") -> dict:
    """DB 层分页查询（避免全量加载），返回 {total, items}。"""
    from sqlalchemy import func, or_, select

    from src.storage.models import Job
    from src.storage.session import session_scope

    def _filters(stmt):
        if city:
            stmt = stmt.where(Job.city == city)
        if category:
            stmt = stmt.where(Job.job_category == category)
        if education:
            stmt = stmt.where(Job.education_req == education)
        if experience:
            stmt = stmt.where(Job.experience_req == experience)
        if job_type:
            stmt = stmt.where(Job.job_type == job_type)
        if source:
            stmt = stmt.where(Job.source == source)
        if keyword:
            like = f"%{keyword.strip()}%"
            stmt = stmt.where(or_(
                Job.job_title.like(like), Job.company_name.like(like),
                Job.job_desc.like(like)))
        return stmt

    page = max(1, page)
    page_size = min(max(1, page_size), 100)
    order_col = {"crawl_date": Job.crawl_date, "post_date": Job.post_date,
                 "salary_avg": Job.salary_avg}.get(sort_by, Job.crawl_date)
    order_clause = order_col.asc() if order == "asc" else order_col.desc()

    with session_scope(cfg) as s:
        total = int(s.scalar(_filters(select(func.count()).select_from(Job))) or 0)
        stmt = _filters(select(Job)).order_by(order_clause) \
            .offset((page - 1) * page_size).limit(page_size)
        rows = list(s.scalars(stmt))

    return {"total": total, "items": rows}


def _serialize_job(job, skills_map: dict) -> dict:
    skills = skills_map.get(str(job.job_id), [])
    return {
        "job_id": job.job_id,
        "title": job.job_title,
        "category": job.job_category,
        "type": job.job_type,
        "company": job.company_name,
        "industry": job.industry,
        "company_size": job.company_size,
        "city": job.city,
        "salary_raw": job.salary_raw,
        "salary_min": job.salary_min,
        "salary_max": job.salary_max,
        "salary_avg": job.salary_avg,
        "experience": job.experience_req,
        "education": job.education_req,
        "tags": job.tags or [],
        "post_date": job.post_date.isoformat() if job.post_date else None,
        "crawl_date": job.crawl_date.strftime("%Y-%m-%d %H:%M") if job.crawl_date else None,
        "url": job.url,
        "source": job.source,
        "skills": [str(x) for x in skills],
        "skills_count": len(skills),
    }


def _skills_map(cfg: Config) -> dict:
    """features.parquet 的 job_id -> skills_hit 映射（无文件时返回空表）。"""
    feat_path = Path(cfg.raw["paths"]["features_path"])
    if not feat_path.exists():
        return {}
    try:
        df = pd.read_parquet(feat_path)
    except Exception:  # pragma: no cover - 文件损坏时降级
        return {}
    out: dict = {}
    if "job_id" in df.columns and "skills_hit" in df.columns:
        for jid, sk in zip(df["job_id"].astype(str), df["skills_hit"]):
            out.setdefault(jid, [x for x in (sk.tolist() if hasattr(sk, "tolist") else sk)])
    return out


# ---------------------------------------------------------------- 模型预测
class PredictRequest(BaseModel):
    job_title: str = Field(..., description="岗位标题")
    city: str = Field(..., description="城市（不带市后缀，如 北京）")
    job_category: str = Field(..., description="岗位类别：数据分析/数据科学/大数据/算法/BI数仓")
    education_req: str = Field("本科", description="学历要求：不限/大专/本科/硕士/博士")
    experience_req: str = Field("1-3年", description="经验要求，如 1-3年/3-5年/不限")
    job_type: str = Field("社招", description="岗位类型：社招/校招/实习/不限")
    industry: str = Field("其他", description="所属行业（训练 Top-20 外归为其他）")
    company_size: Optional[str] = Field(None, description="公司规模（可选）")
    skills: list[str] = Field(default_factory=list, description="技能关键词列表")


class PredictResponse(BaseModel):
    predicted_salary_avg: float
    salary_band: str
    note: str


def _load_predictor(cfg: Config):
    """加载模型文件（含特征列名），不存在返回 None。"""
    model_path = Path(cfg.raw["paths"].get("model_dir", "output/model")) / "jobpulse_xgb.joblib"
    if not model_path.exists():
        return None
    import joblib
    return joblib.load(model_path)


def _predict(cfg: Config, req: PredictRequest) -> dict:
    from src.model.features import build_features

    payload = _load_predictor(cfg)
    if payload is None:
        raise HTTPException(
            status_code=404,
            detail="模型文件不存在，请先运行 python src/cli.py model 生成 output/model/jobpulse_xgb.joblib")

    one = pd.DataFrame([{
        "job_id": "predict_1", "salary_avg": None,
        "job_title": req.job_title, "city": req.city,
        "job_category": req.job_category, "job_type": req.job_type,
        "education_req": req.education_req, "experience_req": req.experience_req,
        "industry": req.industry, "company_size": req.company_size,
        "job_desc": "", "skills_count": len(req.skills),
    }])
    X = build_features(one)
    feat_cols = payload["features"]
    X = X.reindex(columns=[c for c in feat_cols if c in X.columns]).fillna(0)
    for c in feat_cols:
        if c not in X.columns:
            X[c] = 0
    pred = float(__import__("numpy").exp(payload["model"].predict(X[feat_cols])[0]))
    band = f"{int(round(pred * 0.8 / 1000) * 1000):,} - {int(round(pred * 1.2 / 1000) * 1000):,} 元"
    return {"predicted_salary_avg": round(pred), "salary_band": band,
            "note": "预测值来自 XGBoost（log 目标还原），仅供市场趋势参考"}


# ---------------------------------------------------------------- FastAPI app
def create_app(cfg: Config | None = None) -> FastAPI:
    cfg = cfg or load_config()
    app = FastAPI(title="JobPulse API", version="0.3.0",
                  description="招聘情报站后端接口：看板聚合 / 岗位明细 / 薪资预测")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 本地学习项目；生产可收紧
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/health")
    def health():
        try:
            jobs = count_jobs(cfg)
            snaps = count_snapshots(cfg)
            driver = cfg.raw["database"]["driver"]
        except Exception as e:  # pragma: no cover
            raise HTTPException(status_code=500, detail=f"DB 不可用: {e}")
        return {"status": "ok", "jobs": jobs, "snapshots": snaps, "db": driver}

    @app.get("/api/jobs/summary")
    def jobs_summary(city: str = "", category: str = "", education: str = "",
                     source: str = ""):
        data = _full_data(cfg)
        summary = dict(data["summary"])
        sources = sorted({r.get("src") for r in data["records"] if r.get("src")})
        records = stats_mod.filter_records(data["records"], city or None,
                                           category or None, education or None,
                                           source or None)
        filtered = stats_mod.stats(records)
        charts = stats_mod.build_charts(records, summary["categories"], summary["cities"])
        return {"summary": summary, "filtered": filtered, "charts": charts,
                "sources": sources}

    @app.get("/api/jobs")
    def jobs(
        city: str = "", category: str = "", education: str = "",
        experience: str = "", job_type: str = "", keyword: str = "",
        source: str = "",
        page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
        sort_by: str = "crawl_date", order: str = "desc",
    ):
        res = _query_jobs(cfg, city or None, category or None, education or None,
                          experience or None, job_type or None, keyword or None,
                          source or None, page, page_size, sort_by, order)
        smap = _skills_map(cfg)
        items = [_serialize_job(j, smap) for j in res["items"]]
        total_pages = (res["total"] + page_size - 1) // page_size
        return {"total": res["total"], "page": page, "page_size": page_size,
                "total_pages": total_pages, "items": items}

    @app.get("/api/meta")
    def meta():
        """筛选选项（供前端初始化下拉，避免依赖 summary 全量数据）。"""
        data = _full_data(cfg)
        sources = sorted({r.get("src") for r in data["records"] if r.get("src")})
        return {**data["summary"], "sources": sources}

    @app.post("/api/model/predict", response_model=PredictResponse)
    def predict(req: PredictRequest):
        return _predict(cfg, req)

    # 前端构建产物静态托管（web/dist，单端口部署）+ SPA history 路由 fallback
    from fastapi.responses import FileResponse

    dist = Path(__file__).resolve().parent.parent.parent / "web" / "dist"

    @app.get("/{full_path:path}", include_in_schema=False)
    def spa(full_path: str):
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not Found")
        target = dist / full_path
        if dist.exists() and full_path and target.is_file():
            return FileResponse(target)
        index = dist / "index.html"
        if index.exists():
            return FileResponse(index)
        return {"detail": "前端未构建：cd web && npm run build"}

    return app


app = create_app()
