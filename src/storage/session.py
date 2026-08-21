# -*- coding: utf-8 -*-
"""Session 工厂（REQ-DB-02）：MySQL 主 / SQLite 开发兜底，连接参数集中配置。"""
from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from src.config import Config

_engine: Engine | None = None
_session_factory: sessionmaker | None = None


def get_engine(cfg: Config | None = None) -> Engine:
    """创建（或复用）引擎。MySQL 用 utf8mb4 字符集；SQLite 兜底。"""
    global _engine
    if _engine is None:
        from src.config import load_config

        cfg = cfg or load_config()
        url = cfg.sqlalchemy_url()
        kwargs: dict = {"pool_pre_ping": True, "echo": False}
        if url.startswith("sqlite"):
            kwargs["connect_args"] = {"check_same_thread": False}
        _engine = create_engine(url, **kwargs)
    return _engine


def get_session_factory(cfg: Config | None = None) -> sessionmaker:
    global _session_factory
    if _session_factory is None:
        _session_factory = sessionmaker(bind=get_engine(cfg), expire_on_commit=False)
    return _session_factory


@contextmanager
def session_scope(cfg: Config | None = None) -> Iterator[Session]:
    """事务性 session 上下文：异常回滚，正常提交。"""
    factory = get_session_factory(cfg)
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def reset_engine() -> None:
    """重置引擎（测试用：切换 DB 后重建）。"""
    global _engine, _session_factory
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _session_factory = None
