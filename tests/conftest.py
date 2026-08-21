# -*- coding: utf-8 -*-
"""pytest 公共配置：项目根路径 + 环境变量默认值。"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# 测试默认使用 SQLite 兜底，避免依赖本机 MySQL
os.environ.setdefault("JOBPULSE_TEST_DB", "sqlite")
os.environ.setdefault("DB_PASSWORD", "123456")
