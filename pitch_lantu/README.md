# 岚图汽车比稿 · 微博营销分析

为岚图汽车两个比稿方向产出的微博数据采集 + 营销时间轴分析，时间窗 **2025-11-12 ~ 2026-05-12（最近 6 个月）**。

## 目录结构

```
pitch_lantu/
├── README.md                       (本文件)
├── taskA_mpv/                       任务 A: MPV 比稿
│   ├── README.md                    比稿任务说明
│   ├── 任务A_MPV比稿分析.md          主报告 ★
│   ├── 明细汇总.csv                  5 车型每条微博明细 + 标签
│   ├── phase0_lookup.py             阶段 0: 账号定位 + 命中预查
│   ├── phase0_result.json           5 个品牌官方账号 uid 表
│   ├── phase1_crawl.py              阶段 1: 抓取 driver
│   ├── phase1_summary.json          抓取耗时统计
│   ├── analyze.py                   阶段 3-4: 分类标注 + 报告生成
│   └── config.backup.json           跑抓取前 config.json 的备份
└── taskB_phev_suv/                  任务 B: 中大型 SUV PHEV 比稿
    └── (同上结构)
```

## 两个比稿任务

| 任务 | 比稿目标 | 竞品 (按比稿要求) |
|---|---|---|
| **A · MPV** | 岚图梦想家 | 腾势D9 / 别克GL8 / 长城高山 / 智界V9 |
| **B · 中大型 SUV PHEV** | 岚图泰山X8 PHEV | 问界M8 / 理想L8 / 小鹏GX / 极氪8X / 蔚来ES8 |

## 复用流程（按需）

每个 taskX 都是自包含的，重跑步骤：

```bash
# 从仓库根目录运行
python pitch_lantu/taskA_mpv/phase0_lookup.py     # 1. 账号定位
python pitch_lantu/taskA_mpv/phase1_crawl.py      # 2. 抓取（10-25 分钟）
python pitch_lantu/taskA_mpv/analyze.py           # 3. 分析 + 报告
```

抓取数据落到项目根的 `weibo_data/<品牌screen_name>/<uid>.json`，分析直接读这里。

## 依赖说明

- 抓取依赖项目根的 `weibo.py` + `config.json` + `.env.local` (WEIBO_COOKIE)
- 分析仅依赖 `weibo_data/<品牌>/` 下的 JSON
- 蔚来 ES8 数据复用项目根 `weibo_data/蔚来/5675889356.json`（任务 A 之前已抓取一年数据，本次任务从中切片）
