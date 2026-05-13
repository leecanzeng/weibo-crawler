"""
任务 A - MPV 比稿 5 车型微博营销动作分析

输入: 5 个车型的 JSON (weibo-crawler 输出)
  weibo_data/岚图汽车/7351024207.json    → 岚图梦想家
  weibo_data/腾势汽车/2664689831.json    → 腾势D9
  weibo_data/别克/1667553532.json        → 别克GL8
  weibo_data/魏牌/6055831093.json        → 长城高山(魏牌)
  weibo_data/智界汽车/7861851237.json    → 智界V9

输出:
  weibo_data/_taskA_明细汇总.csv          (5 车型分类明细)
  任务A_MPV比稿分析.md                   (主报告)
"""
import csv as csvlib
import json
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from statistics import mean, median, stdev

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

REPO = os.path.dirname(os.path.abspath(__file__))  # 脚本目录
REPO_ROOT = os.path.dirname(os.path.dirname(REPO))  # 项目根

# 5 车型配置：JSON 路径、显示名、关键词(本次抓取已 API 过滤,这里仅做兜底)
CARS = [
    {"label": "岚图梦想家", "brand": "岚图", "json": "weibo_data/岚图汽车/7351024207.json",  "query": "梦想家"},
    {"label": "腾势D9",     "brand": "腾势", "json": "weibo_data/腾势汽车/2664689831.json",  "query": "D9"},
    {"label": "别克GL8",    "brand": "别克", "json": "weibo_data/别克/1667553532.json",      "query": "GL8"},
    {"label": "长城高山",   "brand": "魏牌", "json": "weibo_data/魏牌/6055831093.json",       "query": "高山"},
    {"label": "智界V9",     "brand": "智界", "json": "weibo_data/智界汽车/7861851237.json",  "query": "V9"},
]

REPORT_PATH = os.path.join(REPO, "任务A_MPV比稿分析.md")
DETAIL_CSV = os.path.join(REPO, "明细汇总.csv")

WINDOW_START = datetime(2025, 11, 12)
WINDOW_END = datetime(2026, 5, 12, 23, 59, 59)


# ============================================================
# 1) MPV 比稿专属营销动作分类规则
# ============================================================
def classify(text: str, topics: str, at_users: str, source: str = ""):
    """返回标签列表，一条可属多类"""
    tags = []
    t = (text or "")
    tp = (topics or "")
    full = t + " " + tp

    # 上市发布(节点事件) —— 最重要
    if re.search(r"上市|预售|发布会|开启预订|开启交付|首发|官降|价格|新车|正式登场|焕新|焕新登场|限时|权益购|权益升级", full):
        tags.append("上市发布")

    # 试驾/媒体评测
    if re.search(r"试驾|实测|静态品鉴|首试|抢先体验|横评|对比测试|车评|测评", full):
        tags.append("试驾评测")

    # 跨界/联名/IP合作
    if re.search(r"联名|联合|跨界|合作伙伴|战略合作|签约|签订|品牌联手|携手", full):
        tags.append("跨界联名")

    # 明星/综艺/影视植入
    if re.search(r"张智霖|王宝强|何冰|演员|明星|代言人|品牌大使|综艺|电影|影视|微电影", full):
        tags.append("明星综艺")

    # 互动激励 —— 转评赞抽奖
    if re.search(r"转发并|转评赞|抽取\d*位?|送出|福袋|抽奖|获奖名单|恭喜@", full):
        tags.append("互动激励")

    # 创始人/高管 IP
    if re.search(r"@?李斌|@?何小鹏|@?余承东|@?王传福|@?魏建军|@?李想|@?卢放|@?王俊|董事长|总裁|CEO|总经理|创始人", full):
        tags.append("高管IP")

    # 场景叙事(MPV 核心场景)
    if re.search(r"家庭|宝爸|宝妈|带娃|亲子|出游|长途|露营|奶爸|二孩|二胎|商务|接送|全家|出行|远行|度假|周末|车主故事|首程", full):
        tags.append("场景叙事")

    # 节日借势
    if re.search(r"国庆|春节|元旦|妇女节|劳动节|五一|中秋|端午|圣诞|新年|元宵|清明|父亲节|母亲节|教师节|儿童节|七夕|情人节|感恩节|双十一|双十二|开学|高考|跨年", full):
        tags.append("节日借势")

    # 数据仪式 / 销量通报
    if re.search(r"销量|交付|累计|万辆|连续\d+周|连续\d+月|月销|周销|环比|同比|登顶|蝉联|榜首|冠军|纪录", full):
        tags.append("销量通报")

    # 车主权益 / 服务
    if re.search(r"权益|质保|保修|车主专享|车主专属|金石之约|尊享服务|售后|换电|补能|VIP|赠送|免费", full):
        tags.append("车主权益")

    # 产品/技术亮点(MPV 通用要素)
    if re.search(r"舒适|静谧|静音|空间|储物|二排|三排|座椅|按摩|皇后|老板|商务舱|MPV|轴距|续航|油耗|电耗|底盘|悬挂|发动机|电池|快充", full):
        tags.append("产品亮点")

    # 安全性强调
    if re.search(r"安全|碰撞|防护|安全性|气囊|车身|结构|主动安全|被动安全|超五星|C-NCAP|E-NCAP", full):
        tags.append("安全强调")

    if not tags:
        tags.append("未分类")
    return tags


# ============================================================
# 2) 加载 5 车型数据
# ============================================================
def load_car(car_cfg):
    path = os.path.join(REPO_ROOT, car_cfg["json"])
    if not os.path.isfile(path):
        print(f"[WARN] {path} 不存在")
        return {**car_cfg, "weibos": [], "raw_count": 0}
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    weibos = data.get("weibo", [])
    # 二次过滤：确保时间窗 + query 命中 + 按 id 去重
    q = car_cfg["query"]
    filtered = []
    seen_ids = set()
    for w in weibos:
        wid = w.get("id")
        if wid in seen_ids:
            continue
        dt = None
        try:
            dt = datetime.strptime(w["full_created_at"], "%Y-%m-%d %H:%M:%S")
        except Exception:
            continue
        if not (WINDOW_START <= dt <= WINDOW_END):
            continue
        # query 命中 (text 或 topics)
        text = (w.get("text") or "") + " " + (w.get("topics") or "")
        if q not in text:
            continue
        seen_ids.add(wid)
        w["_dt"] = dt
        w["_month"] = dt.strftime("%Y-%m")
        w["_week"] = dt.strftime("%Y-W%V")
        w["_dow"] = dt.strftime("%A")
        w["_hour"] = dt.hour
        w["_tags"] = classify(w.get("text", ""), w.get("topics", ""), w.get("at_users", ""), w.get("source", ""))
        likes = int(w.get("attitudes_count") or 0)
        comments = int(w.get("comments_count") or 0)
        reposts = int(w.get("reposts_count") or 0)
        w["_likes"] = likes
        w["_comments"] = comments
        w["_reposts"] = reposts
        w["_engagement"] = likes + comments + reposts
        filtered.append(w)
    filtered.sort(key=lambda x: x["_dt"])  # 按时间正序
    print(f"  [{car_cfg['label']}] 加载 {len(weibos)} 条 → 过滤后 {len(filtered)} 条")
    return {**car_cfg, "weibos": filtered, "raw_count": len(weibos)}


def fmt(n):
    if isinstance(n, float):
        return f"{n:,.0f}"
    return f"{n:,}"


def avg(lst):
    return sum(lst) / len(lst) if lst else 0


def med(lst):
    return median(lst) if lst else 0


# ============================================================
# 3) 主流程
# ============================================================
def main():
    print("=" * 70)
    print("Phase 3/4 - 任务A MPV 比稿分析")
    print("=" * 70)
    print()

    cars = [load_car(c) for c in CARS]
    cars = [c for c in cars if c["weibos"]]
    if not cars:
        print("ERROR: 无任何车型数据")
        sys.exit(1)
    print()

    # 全量明细 CSV
    os.makedirs(os.path.dirname(DETAIL_CSV), exist_ok=True)
    with open(DETAIL_CSV, "w", encoding="utf-8-sig", newline="") as f:
        w = csvlib.writer(f)
        w.writerow(["车型", "日期", "时间", "标签(多)", "正文摘要", "话题", "点赞", "评论", "转发", "互动总和", "URL"])
        for car in cars:
            for wb in car["weibos"]:
                w.writerow([
                    car["label"],
                    wb["_dt"].strftime("%Y-%m-%d"),
                    wb["_dt"].strftime("%H:%M"),
                    "|".join(wb["_tags"]),
                    (wb.get("text") or "").replace("\n", " ")[:140],
                    wb.get("topics") or "",
                    wb["_likes"], wb["_comments"], wb["_reposts"], wb["_engagement"],
                    f"https://m.weibo.cn/detail/{wb['id']}",
                ])
    print(f"明细 CSV → {DETAIL_CSV}")

    # ===========================================
    # 报告主体
    # ===========================================
    L = []
    P = L.append

    P("# 任务A · MPV 比稿微博营销分析报告")
    P("")
    P(f"> 比稿目标：**岚图梦想家** 用户运营策略 ")
    P(f"> 数据范围：{WINDOW_START.strftime('%Y-%m-%d')} ~ {WINDOW_END.strftime('%Y-%m-%d')}（最近 6 个月） ")
    P(f"> 数据源：5 个品牌官方微博账号 ")
    P(f"> 数据维度：发文量 + 互动量 + 营销动作分类 + 时间序列对比")
    P("")
    P("---")
    P("")

    # —— 一、数据概览 ——
    P("## 一、数据概览（5 车型横向对比）")
    P("")
    P("| 车型 | 微博数 | 总互动 | 单条均互动 | 中位互动 | 单条 Top 互动 | 日均 |")
    P("|---|---|---|---|---|---|---|")
    overview_rows = []
    for car in cars:
        wbs = car["weibos"]
        total_eng = sum(w["_engagement"] for w in wbs)
        avg_eng = avg([w["_engagement"] for w in wbs])
        med_eng = med([w["_engagement"] for w in wbs])
        top_eng = max(w["_engagement"] for w in wbs) if wbs else 0
        days = (WINDOW_END - WINDOW_START).days + 1
        overview_rows.append({
            "label": car["label"], "count": len(wbs),
            "total_eng": total_eng, "avg_eng": avg_eng, "med_eng": med_eng, "top_eng": top_eng,
            "daily": len(wbs) / days,
        })
        P(f"| **{car['label']}** | {fmt(len(wbs))} | {fmt(total_eng)} | {fmt(avg_eng)} | {fmt(med_eng)} | {fmt(top_eng)} | {len(wbs)/days:.2f} |")
    P("")
    # 排序观察
    by_count = sorted(overview_rows, key=lambda x: -x["count"])
    by_eng = sorted(overview_rows, key=lambda x: -x["avg_eng"])
    P("**发文密度排名：** " + " > ".join([f"{x['label']}({x['count']})" for x in by_count]))
    P("")
    P("**单条均互动排名：** " + " > ".join([f"{x['label']}({fmt(x['avg_eng'])})" for x in by_eng]))
    P("")
    P("---")
    P("")

    # —— 二、月度发文趋势 ——
    P("## 二、月度发文趋势")
    P("")
    P("各车型按月发文量：")
    P("")
    # 收集所有月份
    all_months = set()
    month_data = {}
    for car in cars:
        cnt = Counter(w["_month"] for w in car["weibos"])
        month_data[car["label"]] = cnt
        all_months.update(cnt.keys())
    months_sorted = sorted(all_months)
    # 表头
    head = "| 月份 | " + " | ".join([c["label"] for c in cars]) + " |"
    sep = "|---|" + "|".join(["---"] * len(cars)) + "|"
    P(head)
    P(sep)
    for m in months_sorted:
        row = [m] + [str(month_data[c["label"]].get(m, 0)) for c in cars]
        P("| " + " | ".join(row) + " |")
    P("")

    # 月度峰谷观察
    P("**观察：**")
    P("")
    for car in cars:
        cnt = month_data[car["label"]]
        if not cnt: continue
        peak_m, peak_v = max(cnt.items(), key=lambda x: x[1])
        low_m, low_v = min(cnt.items(), key=lambda x: x[1])
        P(f"- **{car['label']}**：峰值 {peak_m}（{peak_v} 条），谷底 {low_m}（{low_v} 条）")
    P("")
    P("---")
    P("")

    # —— 三、重要营销事件时间轴 ——
    P("## 三、重要营销事件时间轴")
    P("")
    P("> 阈值：互动量 ≥ 该车型互动量 80 分位 或 单条互动 ≥ 500")
    P("")
    # 收集所有车型的"大事件"
    events = []
    for car in cars:
        wbs = car["weibos"]
        if not wbs: continue
        engs = sorted([w["_engagement"] for w in wbs])
        p80 = engs[int(len(engs) * 0.8)] if len(engs) >= 5 else 0
        threshold = max(p80, 500)
        for w in wbs:
            if w["_engagement"] >= threshold:
                events.append({"car": car["label"], "w": w})
    events.sort(key=lambda x: x["w"]["_dt"])

    if not events:
        P("（未匹配到达阈值的事件）")
    else:
        P(f"共 **{len(events)}** 条达阈值的事件，按时间正序：")
        P("")
        P("| 日期 | 车型 | 标签 | 互动 | 摘要 |")
        P("|---|---|---|---|---|")
        for e in events[:60]:  # 列前 60 条
            w = e["w"]
            text = (w.get("text") or "").replace("\n", " ").replace("|", "/")[:60]
            P(f"| {w['_dt'].strftime('%m-%d')} | {e['car']} | {','.join(w['_tags'][:2])} | {fmt(w['_engagement'])} | {text} |")
        P("")
    P("---")
    P("")

    # —— 四、营销动作分类对比 ——
    P("## 四、营销动作分类对比")
    P("")
    P("> 一条微博可属多个标签（如『上市发布+互动激励』）")
    P("")
    all_tags = []
    car_tag_count = {}
    for car in cars:
        c = Counter()
        for w in car["weibos"]:
            for t in w["_tags"]:
                c[t] += 1
        car_tag_count[car["label"]] = c
        for t in c:
            if t not in all_tags:
                all_tags.append(t)
    # 全局排序：按 5 车型合计
    total_tag = Counter()
    for c in car_tag_count.values():
        for t, v in c.items():
            total_tag[t] += v
    sorted_tags = [t for t, _ in total_tag.most_common()]

    head = "| 标签 | " + " | ".join([c["label"] for c in cars]) + " |"
    P(head)
    P("|---|" + "|".join(["---"] * len(cars)) + "|")
    for tag in sorted_tags:
        row = [tag]
        for car in cars:
            cnt = car_tag_count[car["label"]].get(tag, 0)
            total = len(car["weibos"])
            row.append(f"{cnt} ({cnt/total*100:.0f}%)" if total else "0")
        P("| " + " | ".join(row) + " |")
    P("")
    P("---")
    P("")

    # —— 五、各车型 Top 5 爆款 ——
    P("## 五、各车型 Top 5 爆款微博")
    P("")
    for car in cars:
        P(f"### {car['label']}")
        P("")
        top5 = sorted(car["weibos"], key=lambda x: -x["_engagement"])[:5]
        for i, w in enumerate(top5, 1):
            text = (w.get("text") or "").replace("\n", " ")[:150]
            P(f"**#{i}** | {w['_dt'].strftime('%Y-%m-%d %H:%M')} | 标签：{', '.join(w['_tags'])}")
            P("")
            P(f"> {text}{'...' if len(w.get('text') or '') > 150 else ''}")
            P("")
            P(f"  👍 {fmt(w['_likes'])} | 💬 {fmt(w['_comments'])} | 🔁 {fmt(w['_reposts'])} | **互动 {fmt(w['_engagement'])}**")
            P(f"  🔗 [原文](https://m.weibo.cn/detail/{w['id']})")
            P("")
        P("---")
        P("")

    # —— 六、给岚图梦想家的建议 ——
    P("## 六、给岚图梦想家的关键建议")
    P("")
    # 找岚图梦想家
    lt = next((c for c in cars if c["label"] == "岚图梦想家"), None)
    if not lt:
        P("（岚图梦想家数据缺失）")
    else:
        ltc = car_tag_count["岚图梦想家"]
        lt_total = len(lt["weibos"])
        P(f"基于 {lt_total} 条岚图梦想家半年微博，结合 4 个 MPV 竞品（腾势D9 / 别克GL8 / 长城高山 / 智界V9）的对比，分析如下：")
        P("")

        # 1) 与对手的发文密度差距
        lt_count = lt_total
        opponents = [c for c in cars if c["label"] != "岚图梦想家"]
        avg_opp = mean([len(c["weibos"]) for c in opponents])
        P(f"### 1) 发文密度")
        P("")
        if lt_count > avg_opp * 1.2:
            P(f"- 岚图梦想家发文 {lt_count} 条，**高于 4 竞品均值 {avg_opp:.0f} 条**（高 {(lt_count/avg_opp-1)*100:.0f}%）")
        elif lt_count < avg_opp * 0.8:
            P(f"- 岚图梦想家发文 {lt_count} 条，**低于 4 竞品均值 {avg_opp:.0f} 条**（低 {(1-lt_count/avg_opp)*100:.0f}%），可适度加密节奏")
        else:
            P(f"- 岚图梦想家发文 {lt_count} 条，与 4 竞品均值 {avg_opp:.0f} 持平")
        P("")

        # 2) 互动结构
        lt_avg_eng = avg([w["_engagement"] for w in lt["weibos"]])
        opp_avg_eng = avg([w["_engagement"] for c in opponents for w in c["weibos"]])
        P(f"### 2) 互动质量")
        P("")
        P(f"- 岚图梦想家单条均互动 **{lt_avg_eng:.0f}**，4 竞品合计均互动 **{opp_avg_eng:.0f}**")
        if lt_avg_eng < opp_avg_eng * 0.8:
            P(f"- 互动效率偏低，可参考下方动作分布优化")
        elif lt_avg_eng > opp_avg_eng * 1.2:
            P(f"- 互动效率高于竞品均值")
        P("")

        # 3) 动作结构对比
        P(f"### 3) 动作结构对比")
        P("")
        # 列出岚图梦想家偏多/偏少的标签
        differences = []
        for tag in sorted_tags:
            lt_pct = ltc.get(tag, 0) / lt_total * 100 if lt_total else 0
            opp_pct_list = []
            for c in opponents:
                oc = car_tag_count[c["label"]]
                tot = len(c["weibos"])
                if tot:
                    opp_pct_list.append(oc.get(tag, 0) / tot * 100)
            opp_pct = mean(opp_pct_list) if opp_pct_list else 0
            differences.append((tag, lt_pct, opp_pct, lt_pct - opp_pct))
        differences.sort(key=lambda x: -abs(x[3]))
        P("**岚图梦想家显著偏多 / 偏少的动作类型（按差距绝对值 Top 8）：**")
        P("")
        P("| 动作类型 | 岚图梦想家占比 | 4 竞品均占比 | 差距 |")
        P("|---|---|---|---|")
        for tag, lt_p, opp_p, diff in differences[:8]:
            sign = "+" if diff > 0 else ""
            P(f"| {tag} | {lt_p:.0f}% | {opp_p:.0f}% | {sign}{diff:.0f}pp |")
        P("")

        # 4) 给出战略建议（基于差距）
        P("### 4) 战术建议")
        P("")
        # 标识对手 Top 案例的明星/IP（用于"借力建议"）
        opponent_top_cases = []
        for c in opponents:
            tops = sorted(c["weibos"], key=lambda x: -x["_engagement"])[:3]
            for tw in tops:
                opponent_top_cases.append({"car": c["label"], "w": tw})
        suggestions = []
        for tag, lt_p, opp_p, diff in differences[:8]:
            if diff > 8:
                suggestions.append(f"- **【削减】{tag}** 占比 {lt_p:.0f}%，竞品均值 {opp_p:.0f}%（高 {diff:+.0f}pp）— 可适度减少，腾出版位做其他动作")
            elif diff < -8:
                suggestions.append(f"- **【补齐】{tag}** 占比 {lt_p:.0f}%，竞品均值 {opp_p:.0f}%（低 {diff:+.0f}pp）— 竞品都在做，岚图梦想家可参考补齐")
        if suggestions:
            for s in suggestions:
                P(s)
        else:
            P("- 动作结构与竞品基本对齐，无显著结构缺口")
        P("")

        # 5) 借力建议:看竞品 Top 案例的打法
        P("### 5) 竞品爆款打法可借鉴的方向")
        P("")
        P("**4 个竞品的 Top 3 爆款合计 12 条，从中提炼可借鉴的方向：**")
        P("")
        top_engs = sorted(opponent_top_cases, key=lambda x: -x["w"]["_engagement"])[:8]
        for case in top_engs:
            w = case["w"]
            text = (w.get("text") or "").replace("\n", " ")[:100]
            tags = ", ".join(w["_tags"][:3])
            P(f"- **{case['car']}** [{w['_dt'].strftime('%m-%d')}] 互动 {fmt(w['_engagement'])} | {tags}")
            P(f"  > {text}")
            P("")

    P("---")
    P("")
    P("## 附录")
    P("")
    P(f"- 明细 CSV：[`{os.path.basename(DETAIL_CSV)}`]({os.path.basename(DETAIL_CSV)})")
    P(f"- 数据来源：各品牌官方微博账号通过 `100103type=401` 搜索接口按车型关键词过滤")
    P(f"- 反爬配置：5-10s 请求延迟，50 条/批次 + 15s 批延迟")
    P("")

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(L))
    print(f"\n报告 → {REPORT_PATH}")


if __name__ == "__main__":
    main()
