# JobPulse 招聘情报站

> 爬取真实招聘数据 → 清洗建库 → 分析岗位市场规律 → 预测薪资 → 交互看板展示，数据科学全流程闭环项目。
> 面向方向：**数据分析 / 数据科学（实习 + 秋招）**

![数据量](https://img.shields.io/badge/数据-7%2C387%20条%20有效-blue)
![R²](https://img.shields.io/badge/模型%20R%C2%B2-0.5144-success)
![Python](https://img.shields.io/badge/Python-3.13-green)

## 一、项目简介

JobPulse 是一个个人学习展示项目，打通**获取 → 存储 → 清洗 → 分析 → 建模 → 可视化**全链路：

| 环节 | 实现 |
|---|---|
| 数据获取 | 51job 主爬验证被阿里云 WAF 拦截（按合规边界放弃）→ 切换 **GitHub 开源数据集**（Rayair019/Job-posting-data，2025 年中国 BOSS/智联/猎聘 10,114 条数据科学岗位） |
| 数据存储 | MySQL 8.x（SQLite 开发兜底），SQLAlchemy 2.x ORM，`jobs`（最新状态）+ `job_snapshots`（按批次快照，支持增量与时间趋势） |
| 数据清洗 | 薪资归一化纯函数（9 条规则，含实习日薪×20、薪数换算、异常检测）+ 字段枚举归一化（城市/学历/经验/规模/行业），全部单测覆盖 |
| 数据分析 | EDA 8 图（城市/大类/行业分布 + 学历/经验/城市/类别薪资对比 + 热力图），6 条量化洞察 |
| 文本挖掘 | jieba 分词 + 89 个技能词表，技能 Top30（命中岗位占比口径）、城市/类别差异对比、中文词云，产出建模特征 |
| 薪资建模 | XGBoost 回归（log 目标变换 + 标题/JD 文本特征），测试集 **R² = 0.5144**（≥0.50 达标），MAE 8,733 / RMSE 12,508 |
| 可视化 | **ECharts 交互看板**：单 HTML 数据内嵌，双击即开，城市/类别/学历筛选联动 |
| 工程化 | adapter 可插拔数据源、断点续爬 checkpoint、请求重试退避、采集健康监控、日志、幂等增量、一键链路 |

## 二、架构

```
┌─────────────────────────────────────────────────────┐
│ 交互层：ECharts 看板（HTML，数据内嵌） / 分析报告（MD） │
├─────────────────────────────────────────────────────┤
│ 分析层：EDA（matplotlib） + 技能图谱（jieba/wordcloud）│
│         + 薪资预测（XGBoost/scikit-learn）           │
├─────────────────────────────────────────────────────┤
│ 数据层：ETL 清洗纯函数 + SQLAlchemy ORM → MySQL      │
│         （SQLite 开发兜底）                          │
├─────────────────────────────────────────────────────┤
│ 采集层：adapter（backup / job51）                    │
│         重试 + 限速 + UA 池 + 幂等写入 + checkpoint   │
└─────────────────────────────────────────────────────┘
```

## 三、目录结构

```
jobpulse/
├── docs/REQUIREMENTS.md      # 需求文档（唯一事实来源）
├── config/
│   ├── config.yaml           # 数据库/城市/关键词/延时重试/技能词表路径
│   ├── skill_words.json      # 89 个核心技能词（REQ-NLP-02）
│   ├── stopwords.txt         # 停用词
│   └── userdict.txt          # jieba 自定义词典
├── src/
│   ├── cli.py                # 命令行入口（check-env/init-db/crawl/etl/analyze/nlp/model/viz/report/all）
│   ├── crawler/              # adapter（backup/job51）+ 反爬容错 + checkpoint + 健康监控
│   ├── storage/              # ORM models（jobs/job_snapshots）+ 建表 + 幂等写入
│   ├── etl/                  # 薪资归一化 + 字段清洗 + JD 解析 + 数据质量报告
│   ├── analysis/             # EDA（8 图 + 洞察）
│   ├── nlp/                  # 技能匹配 + Top30 + 差异 + 词云 + features.parquet
│   ├── model/                # 特征工程 + XGBoost 训练评估
│   ├── viz/                  # ECharts 看板生成（单 HTML）
│   └── scheduler/            # 增量调度（APScheduler 可选）
├── tests/                    # 130+ 项单测/集成测试
├── data/                     # 中间产物 + 数据集（.gitignore，不入库）
├── output/                   # 图表 / 报告 / 看板 / features.parquet（入库展示）
├── run_all.py                # 一键链路（AC-1）
└── requirements.txt
```

## 四、快速开始

### 环境要求
- Python 3.10+（本项目 3.13 验证）
- MySQL 8.x（本机已装；无 MySQL 可切 SQLite 开发兜底）
- 中文字体（Windows：Microsoft YaHei / SimHei 自带）

### 一条命令跑通

```bash
# 1. 安装依赖
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt     # Windows

# 2. 配置数据库密码（环境变量注入，不入库）
$env:DB_PASSWORD="你的MySQL密码"                  # Windows PowerShell

# 3. 放置数据集（已下载）
#    data/raw/job_posting_data.xlsx
#    下载：https://github.com/Rayair019/Job-posting-data/raw/main/job_posting_data.xlsx

# 4. 一键链路（check-env → 建库 → 采集 → 分析 → 建模 → 看板 → 报告）
python run_all.py

# 5. 打开看板（双击即可，无需服务端）
output\dashboard\jobpulse_dashboard.html
```

### 分步命令

```bash
python src/cli.py check-env               # 环境检查
python src/cli.py init-db                 # 建库
python src/cli.py crawl --source backup   # 采集（backup 数据集导入）
python src/cli.py etl                     # 数据质量报告
python src/cli.py analyze                 # EDA
python src/cli.py nlp                     # 技能图谱
python src/cli.py model                   # 薪资预测
python src/cli.py viz                     # 看板
python src/cli.py report                  # 分析报告
```

### 增量与调度

```bash
python -m src.scheduler.run --once                # 手动执行一次增量（幂等）
python -m src.scheduler.run --interval-hours 24   # APScheduler 每 24h 定时
```

## 五、成果

### 看板（双击 `output/dashboard/jobpulse_dashboard.html`）
- 薪资分布 / 城市薪资对比 / 技能 Top15 / 岗位量占比 / 城市×类别热力图
- 城市、岗位类别、学历三维筛选联动

### 核心洞察（节选，全部见 `output/reports/report.md`）
1. 北京是数据分析/数据科学岗位最集中的城市：有效岗位 3,270 条，占 44.3%（样本 N=7,387）
2. 城市薪资差异明显：上海月薪中位数 25,000 元 vs 西安 11,375 元，差距 2.2 倍
3. 大数据岗薪资中位数最高 22,500 元，高于数据科学岗（16,000 元）41%
4. 硕士学历薪资溢价 24%（中位数 22,500 vs 本科 18,083）
5. 5-10 年经验月薪中位数 38,750 元，是 1-3 年（18,812 元）的 2.1 倍
6. 算法类实习月薪中位数 24,000 元（实习日薪×20 折月口径）

### 模型
- XGBoost 回归预测月薪：**测试集 R² = 0.5144**、MAE = 8,733 元、RMSE = 12,508 元
- 优于线性回归基线（R² = 0.335）与均值基线（R² ≈ 0）
- 建模集：7,210 条全职（剔除实习 177 条、薪资非空），8:2 按城市×类别分层划分，固定种子
- 详见 `output/reports/model_evaluation.md`

## 六、数据源与合规声明（REQ-DEL-01 / NFR-05）

- **主爬源 51job**：2026-02 实测全端点被阿里云 WAF 深度保护（JS 挑战），按项目边界（3.2：不逆向、不绕过验证码）判定不可用，已保留 adapter 骨架（`src/crawler/job51.py`）并记录验证结论。
- **兜底数据集**：`Rayair019/Job-posting-data`（10,114 条，2025 年中国 BOSS直聘/智联/猎聘数据科学岗位文本，含城市与薪资）。
  - 该仓库**无明确开源许可证**，本项目仅用于个人学习展示，**不二次分发**；如需商用请自行评估或替换数据集。
  - 字段映射清单见需求文档附录 11.4 及 `src/crawler/backup.py` 注释。
- 本项目的爬虫实现（UA 池、限速、重试）遵守合理频率；数据仅作市场趋势参考（需求 3.2）。

## 七、测试

```bash
.venv\Scripts\python -m pytest tests -q
```

覆盖：薪资归一化规则 1~9、字段清洗 11.5 枚举、存储幂等（jobs 不增/快照按批次增/失效标记）、
采集反爬容错（403 不重试/5xx 退避）、checkpoint、健康监控、backup 字段映射、
数据质量统计、EDA 图表与洞察、NLP 技能匹配与特征、建模评估、看板生成。

## 八、Roadmap / 已知限制

- [x] 一期：数据集全链路（采集-存储-清洗-分析-建模-看板）
- [ ] 二期（P1）：接入可用的公开 API 数据源（adapter 已预留）
- [ ] 时间趋势（P2）：积累 ≥2 个采集批次后，基于 job_snapshots 产出趋势图
- 南京(190)/西安(143)/苏州(110) 单城样本 <200，属数据集覆盖限制，已在报告中声明

## 九、许可证

本仓库代码 MIT License（数据集版权归原数据集作者，仅供个人学习）。
