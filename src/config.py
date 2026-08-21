# -*- coding: utf-8 -*-
"""全局配置加载器（REQ-DB-02 / 7.4 配置管理）。

从 config/config.yaml 读取配置，DB 密码优先从环境变量注入。
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "config.yaml"


class Config:
    """配置容器：属性访问 + 环境变量注入 DB 密码"""

    def __init__(self, data: dict[str, Any]):
        self._data = data

    def __getattr__(self, item: str) -> Any:
        try:
            return self._data[item]
        except KeyError:
            raise AttributeError(item)

    @property
    def raw(self) -> dict[str, Any]:
        return self._data

    def database(self) -> dict[str, Any]:
        """数据库配置，含解析后的密码（环境变量 > 默认值）"""
        db = dict(self._data["database"])
        pw_env = db.get("password_env")
        if pw_env:
            db["password"] = os.environ.get(pw_env) or db.get("password_default", "")
        else:
            db["password"] = db.get("password_default", "")
        return db

    def sqlalchemy_url(self) -> str:
        """SQLAlchemy 连接串：mysql+pymysql://... 或 sqlite:///...（REQ-DB-02）"""
        db = self.database()
        if db.get("driver") == "sqlite":
            path = PROJECT_ROOT / db.get("sqlite_path", "data/jobpulse.db")
            path.parent.mkdir(parents=True, exist_ok=True)
            return f"sqlite:///{path.as_posix()}"
        user = db["user"]
        password = db.get("password", "")
        host = db.get("host", "localhost")
        port = db.get("port", 3306)
        name = db["name"]
        charset = db.get("charset", "utf8mb4")
        return f"mysql+pymysql://{user}:{password}@{host}:{port}/{name}?charset={charset}"

    # ---- 便捷访问 ----
    @property
    def cities(self) -> list[str]:
        return list(self._data["crawler"]["cities"])

    @property
    def categories(self) -> dict[str, list[str]]:
        return dict(self._data["crawler"]["categories"])

    def save(self, path: str | Path | None = None) -> None:
        target = Path(path) if path else DEFAULT_CONFIG_PATH
        target.write_text(yaml.safe_dump(self._data, allow_unicode=True, sort_keys=False), encoding="utf-8")


def load_config(path: str | Path | None = None) -> Config:
    cfg_path = Path(path) if path else DEFAULT_CONFIG_PATH
    if not cfg_path.exists():
        raise FileNotFoundError(f"配置文件不存在: {cfg_path}")
    with open(cfg_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return Config(data or {})
