# 任务 A · MPV 比稿

**比稿目标**：为岚图梦想家做用户运营策略 ｜ **时间窗**：2025-11-12 ~ 2026-05-12（6 个月）

## 5 车型 + 官方账号

| 车型 | 微博账号 | uid | query_list 关键词 |
|---|---|---|---|
| 岚图梦想家 | @岚图汽车 | 7351024207 | `梦想家` |
| 腾势D9 | @腾势汽车 | 2664689831 | `D9` |
| 别克GL8 | @别克 | 1667553532 | `GL8` |
| 长城高山 | @魏牌 | 6055831093 | `高山` |
| 智界V9 | @智界汽车 | 7861851237 | `V9` |

## 文件说明

| 文件 | 作用 |
|---|---|
| **任务A_MPV比稿分析.md** | 主报告（数据概览 + 月度趋势 + 动作分类 + Top 5 + 时间轴 + 战术建议） |
| 明细汇总.csv | 每条微博的车型/日期/标签/正文摘要/互动数据 |
| phase0_lookup.py | 账号定位 + 关键词命中预查 |
| phase0_result.json | Phase 0 结果（5 个 uid 表 + 命中条数） |
| phase1_crawl.py | 抓取 driver（5 个 (uid, query) 组合循环跑 weibo.py） |
| phase1_summary.json | 抓取耗时统计 |
| analyze.py | 分类规则 + 时间序列 + 报告生成 |
| config.backup.json | 跑抓取前 `config.json` 的备份 |

## 复用步骤（从仓库根目录）

```bash
python pitch_lantu/taskA_mpv/phase0_lookup.py     # 账号定位
python pitch_lantu/taskA_mpv/phase1_crawl.py      # 抓取（约 15 分钟，含反爬延迟）
python pitch_lantu/taskA_mpv/analyze.py           # 分析 + 生成报告
```

数据落到 `weibo_data/<品牌screen_name>/<uid>.json`，由 `analyze.py` 读取并产出本目录的 `.csv` 和 `.md`。
