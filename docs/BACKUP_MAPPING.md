# 兜底数据源字段映射清单（REQ-DC-06 / 附录 11.4）

> 数据集：`Rayair019/Job-posting-data`（2025 年中国 BOSS直聘/智联/猎聘数据科学岗位，10,114 条）
> 仓库：https://github.com/Rayair019/Job-posting-data
> 许可证：**无明确开源许可证**（仅个人学习使用，不二次分发）
> 更新日期：2026-03（仓库最后推送）；数据标注 2025 年发布
> 导入实现：`src/crawler/backup.py`（BackupAdapter）

## 字段映射

| 数据集字段 | 统一 Schema 字段 | 映射/转换规则 |
|---|---|---|
| jobname | job_title | 直接映射；空值补"未命名岗位" |
| company | company_name | 直接映射；空值补"未知公司" |
| salary | salary_raw | 原始文本保留（如 `(25000.0, 50000.0)`） |
| minsalary/maxsalary/meansalary | salary_min/max/salary_avg | 由 `parse_salary(salary_raw)` 归一化（规则 1~9）；异常（上限>30万/下限<1500）→ is_valid=0 |
| city | city | `clean_city` 去"市"后缀；非 10 城白名单（含"其他"）→ is_valid=0 |
| description | job_desc | JD 全文；经验/学历从文本解析（`jd_parse.py`），失败置"不限" |
| other | industry / tags | "行业要求：X"解析为 industry；其余逗号分隔为福利 tags |
| label | job_category | `classify_category`：关键词规则优先（附录 11.2+扩展），label 兜底 |
| — | job_id | `backup_` + 行号（源标识_序号，4.2） |
| — | job_type | `clean_job_type(title+desc)`：实习/校招/社招/不限 |
| — | crawl_date | 导入批次时间（datetime.now()） |
| — | url | 数据集仓库链接 |
| — | is_valid | 默认 1；城市非白名单或薪资异常 → 0 |
| — | source | `backup` |
| — | post_date / company_size | 数据集无此字段 → NULL |

## 清洗结果（2026-08 实测）

- 入库 10,114 条，有效（is_valid=1）7,387 条
- 城市无效 2,719 条（非 10 城白名单）、薪资异常 8 条
- 5 大类均 ≥600：算法 2,390 / 数据分析 2,037 / 数据科学 1,532 / 大数据 823 / BI数仓 605
- 建模集（全职、薪资非空）：7,210 条
