# 任务 B · 中大型 SUV PHEV 比稿

**比稿目标**：为岚图泰山 X8 PHEV 做用户运营策略 ｜ **时间窗**：2025-11-12 ~ 2026-05-12（6 个月）

## 6 车型 + 官方账号

| 车型 | 微博账号 | uid | query_list 关键词 |
|---|---|---|---|
| 岚图泰山X8 PHEV | @岚图汽车 | 7351024207 | `泰山` |
| 问界 M8 | @AITO汽车 | 7711487956 | `M8` |
| 理想 L8 | @理想汽车 | 6001272153 | `L8` |
| 小鹏 GX | @小鹏汽车 | 5710264970 | `GX` |
| 极氪 8X | @极氪Zeekr | 7576049404 | `8X` |
| 蔚来 ES8 | @蔚来 | 5675889356 | `ES8` (本地切片) |

**注**：蔚来 ES8 数据来自项目根 `weibo_data/蔚来/5675889356.json`（任务 A 阶段之前已抓全年），本任务通过 query 二次过滤切片得到。

## 文件说明

| 文件 | 作用 |
|---|---|
| **任务B_中大型SUV_PHEV比稿分析.md** | 主报告（数据概览 + 月度趋势 + 动作分类 + Top 5 + 时间轴 + 战术建议） |
| 明细汇总.csv | 每条微博的车型/日期/标签/正文摘要/互动数据 |
| phase0_lookup.py | 账号定位 + 关键词命中预查（跳过已知岚图 + 蔚来 uid） |
| phase0_result.json | Phase 0 结果（6 个 uid 表 + 命中条数） |
| phase1_crawl.py | 抓取 driver（5 个新组合，蔚来复用现有数据） |
| phase1_summary.json | 抓取耗时统计 |
| analyze.py | 分类规则 + 时间序列 + 报告生成 |
| config.backup.json | 跑抓取前 `config.json` 的备份 |

## 复用步骤（从仓库根目录）

```bash
python pitch_lantu/taskB_phev_suv/phase0_lookup.py     # 账号定位
python pitch_lantu/taskB_phev_suv/phase1_crawl.py      # 抓取（约 20 分钟）
python pitch_lantu/taskB_phev_suv/analyze.py           # 分析 + 生成报告
```

## ⚠️ 与任务 A 的数据交叉

岚图账号同时是任务 A 和任务 B 的官方账号。跑任务 B 抓取时，weibo.py 会**追加合并**到项目根的 `weibo_data/岚图汽车/7351024207.json`，导致该 JSON 同时含"梦想家"+"泰山"两组微博。

- **不影响分析**：`analyze.py` 通过 `query` 关键词做二次过滤切片，按车型独立分析
- **历史快照**：跑任务 B 前，任务 A 阶段的纯"梦想家"数据已备份到 `weibo_data/岚图_梦想家_backup/`
