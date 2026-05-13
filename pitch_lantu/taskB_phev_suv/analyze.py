"""
任务 B - 中大型 SUV PHEV 比稿 6 车型微博营销分析

输入: 6 车型的 JSON
  weibo_data/岚图汽车/7351024207.json    → 岚图泰山X8 PHEV  (query="泰山")
  weibo_data/AITO汽车/7711487956.json    → 问界 M8
  weibo_data/理想汽车/6001272153.json    → 理想 L8
  weibo_data/小鹏汽车/5710264970.json    → 小鹏 GX (即将上市新车)
  weibo_data/极氪Zeekr/7576049404.json   → 极氪 8X
  weibo_data/蔚来/5675889356.json        → 蔚来 ES8

输出:
  weibo_data/_taskB_明细汇总.csv
  任务B_中大型SUV_PHEV比稿分析.md
"""
import csv as csvlib
import json
import os
import re
import sys
from collections import Counter
from datetime import datetime
from statistics import mean, median

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

REPO = os.path.dirname(os.path.abspath(__file__))  # 脚本目录
REPO_ROOT = os.path.dirname(os.path.dirname(REPO))  # 项目根

CARS = [
    {"label": "岚图泰山X8", "brand": "岚图", "json": "weibo_data/岚图汽车/7351024207.json",     "query": "泰山"},
    {"label": "问界M8",      "brand": "问界", "json": "weibo_data/AITO汽车/7711487956.json",     "query": "M8"},
    {"label": "理想L8",      "brand": "理想", "json": "weibo_data/理想汽车/6001272153.json",     "query": "L8"},
    {"label": "小鹏GX",      "brand": "小鹏", "json": "weibo_data/小鹏汽车/5710264970.json",     "query": "GX"},
    {"label": "极氪8X",      "brand": "极氪", "json": "weibo_data/极氪Zeekr/7576049404.json",   "query": "8X"},
    {"label": "蔚来ES8",     "brand": "蔚来", "json": "weibo_data/蔚来/5675889356.json",          "query": "ES8"},
]

REPORT_PATH = os.path.join(REPO, "任务B_中大型SUV_PHEV比稿分析.md")
DETAIL_CSV = os.path.join(REPO, "明细汇总.csv")
WINDOW_START = datetime(2025, 11, 12)
WINDOW_END = datetime(2026, 5, 12, 23, 59, 59)


def classify(text, topics, at_users, source=""):
    """SUV PHEV 比稿专属分类(覆盖产品定位 + 营销动作)"""
    tags = []
    full = (text or "") + " " + (topics or "")

    if re.search(r"上市|预售|发布会|开启预订|开启交付|首发|官降|价格|新车|焕新登场|限时|权益购|大订", full):
        tags.append("上市发布")
    if re.search(r"试驾|实测|静态品鉴|首试|抢先体验|横评|对比测试|车评|测评", full):
        tags.append("试驾评测")
    if re.search(r"联名|联合|跨界|合作伙伴|战略合作|签约|签订|品牌联手|携手", full):
        tags.append("跨界联名")
    if re.search(r"@?李斌|@?何小鹏|@?余承东|@?王传福|@?李想|@?安聪慧|@?卢放|董事长|总裁|CEO|创始人", full):
        tags.append("高管IP")
    if re.search(r"家庭|宝爸|宝妈|带娃|亲子|出游|长途|露营|奶爸|二孩|二胎|商务|接送|全家|出行|远行|度假|车主故事|首程", full):
        tags.append("场景叙事")
    if re.search(r"销量|交付|累计|万辆|连续\d+周|连续\d+月|月销|周销|环比|同比|登顶|蝉联|榜首|冠军|纪录|保值率", full):
        tags.append("销量通报")
    if re.search(r"权益|质保|保修|车主专享|车主专属|金石之约|尊享服务|售后|换电|补能|VIP|赠送|免费|NIO Life", full):
        tags.append("车主权益")
    if re.search(r"舒适|静谧|静音|空间|储物|二排|三排|座椅|按摩|皇后|商务舱|轴距|续航|油耗|电耗|底盘|悬挂|发动机|电池|快充|增程", full):
        tags.append("产品亮点")
    if re.search(r"安全|碰撞|防护|气囊|车身|结构|主动安全|被动安全|超五星|C-NCAP|E-NCAP", full):
        tags.append("安全强调")
    if re.search(r"国庆|春节|元旦|妇女节|劳动节|五一|中秋|端午|圣诞|新年|元宵|清明|父亲节|母亲节|教师节|儿童节|七夕|情人节|感恩节|双十一|双十二|开学|高考|跨年", full):
        tags.append("节日借势")
    if re.search(r"刘亦菲|张智霖|蔡卓妍|王宝强|何冰|郭碧婷|代言人|品牌大使|综艺|电影|影视|微电影", full):
        tags.append("明星综艺")
    if re.search(r"转发并|转评赞|抽取\d*位?|送出|福袋|抽奖|获奖名单|恭喜@", full):
        tags.append("互动激励")
    if re.search(r"智驾|城市NOA|城市NCA|高速NOA|端到端|大模型|算力|芯片|XNGP|MAX|无图|纯视觉|激光雷达", full):
        tags.append("智驾科技")
    if re.search(r"鸿蒙|HarmonyOS|车机|生态|OTA|智能座舱|大屏|HUD|声学", full):
        tags.append("智能座舱")

    if not tags:
        tags.append("未分类")
    return tags


def load_car(car_cfg):
    path = os.path.join(REPO_ROOT, car_cfg["json"])
    if not os.path.isfile(path):
        print(f"[WARN] {path} 不存在")
        return {**car_cfg, "weibos": [], "raw_count": 0}
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    weibos = data.get("weibo", [])
    q = car_cfg["query"]
    filtered = []
    seen_ids = set()
    for w in weibos:
        # 按 id 去重 (weibo.py 多次合并写入可能产生重复)
        wid = w.get("id")
        if wid in seen_ids:
            continue
        try:
            dt = datetime.strptime(w["full_created_at"], "%Y-%m-%d %H:%M:%S")
        except Exception:
            continue
        if not (WINDOW_START <= dt <= WINDOW_END):
            continue
        text = (w.get("text") or "") + " " + (w.get("topics") or "")
        if q not in text:
            continue
        seen_ids.add(wid)
        w["_dt"] = dt
        w["_month"] = dt.strftime("%Y-%m")
        w["_tags"] = classify(w.get("text", ""), w.get("topics", ""), w.get("at_users", ""), w.get("source", ""))
        likes = int(w.get("attitudes_count") or 0)
        comments = int(w.get("comments_count") or 0)
        reposts = int(w.get("reposts_count") or 0)
        w["_likes"] = likes
        w["_comments"] = comments
        w["_reposts"] = reposts
        w["_engagement"] = likes + comments + reposts
        filtered.append(w)
    filtered.sort(key=lambda x: x["_dt"])
    print(f"  [{car_cfg['label']}] 加载 {len(weibos)} 条 → 过滤后 {len(filtered)} 条 (去重)")
    return {**car_cfg, "weibos": filtered, "raw_count": len(weibos)}


def fmt(n):
    if isinstance(n, float):
        return f"{n:,.0f}"
    return f"{n:,}"


def avg(lst):
    return sum(lst) / len(lst) if lst else 0


def med(lst):
    return median(lst) if lst else 0


def main():
    print("=" * 70)
    print("Phase 3/4 - 任务B 中大型 SUV PHEV 比稿分析")
    print("=" * 70)
    print()

    cars = [load_car(c) for c in CARS]
    cars = [c for c in cars if c["weibos"]]
    if not cars:
        print("ERROR: 无任何车型数据")
        sys.exit(1)
    print()

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

    L = []
    P = L.append

    P("# 任务B · 中大型 SUV PHEV 比稿微博营销分析报告")
    P("")
    P(f"> 比稿目标：**岚图泰山 X8 PHEV** 用户运营策略 ")
    P(f"> 数据范围：{WINDOW_START.strftime('%Y-%m-%d')} ~ {WINDOW_END.strftime('%Y-%m-%d')}（最近 6 个月） ")
    P(f"> 数据源：6 个品牌官方微博账号 ")
    P("")
    P("---")
    P("")

    # 一、数据概览
    P("## 一、数据概览（6 车型横向对比）")
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
    by_count = sorted(overview_rows, key=lambda x: -x["count"])
    by_eng = sorted(overview_rows, key=lambda x: -x["avg_eng"])
    P("**发文密度排名：** " + " > ".join([f"{x['label']}({x['count']})" for x in by_count]))
    P("")
    P("**单条均互动排名：** " + " > ".join([f"{x['label']}({fmt(x['avg_eng'])})" for x in by_eng]))
    P("")
    P("---")
    P("")

    # 二、月度趋势
    P("## 二、月度发文趋势")
    P("")
    all_months = set()
    month_data = {}
    for car in cars:
        cnt = Counter(w["_month"] for w in car["weibos"])
        month_data[car["label"]] = cnt
        all_months.update(cnt.keys())
    months_sorted = sorted(all_months)
    head = "| 月份 | " + " | ".join([c["label"] for c in cars]) + " |"
    P(head)
    P("|---|" + "|".join(["---"] * len(cars)) + "|")
    for m in months_sorted:
        row = [m] + [str(month_data[c["label"]].get(m, 0)) for c in cars]
        P("| " + " | ".join(row) + " |")
    P("")
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

    # 三、时间轴
    P("## 三、重要营销事件时间轴")
    P("")
    P("> 阈值：互动量 ≥ 该车型互动量 80 分位 或 单条互动 ≥ 500")
    P("")
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
        P(f"共 **{len(events)}** 条达阈值的事件：")
        P("")
        P("| 日期 | 车型 | 标签 | 互动 | 摘要 |")
        P("|---|---|---|---|---|")
        for e in events[:80]:
            w = e["w"]
            text = (w.get("text") or "").replace("\n", " ").replace("|", "/")[:60]
            P(f"| {w['_dt'].strftime('%m-%d')} | {e['car']} | {','.join(w['_tags'][:2])} | {fmt(w['_engagement'])} | {text} |")
        P("")
    P("---")
    P("")

    # 四、营销动作分类
    P("## 四、营销动作分类对比")
    P("")
    P("> 一条微博可属多个标签")
    P("")
    all_tags = []
    car_tag_count = {}
    for car in cars:
        c_counter = Counter()
        for w in car["weibos"]:
            for t in w["_tags"]:
                c_counter[t] += 1
        car_tag_count[car["label"]] = c_counter
        for t in c_counter:
            if t not in all_tags:
                all_tags.append(t)
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

    # 五、Top 5
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

    # 六、岚图泰山X8 战术建议
    P("## 六、给岚图泰山 X8 PHEV 的关键建议")
    P("")
    lt = next((c for c in cars if c["label"] == "岚图泰山X8"), None)
    if not lt:
        P("（岚图泰山数据缺失）")
    else:
        ltc = car_tag_count["岚图泰山X8"]
        lt_total = len(lt["weibos"])
        P(f"基于 {lt_total} 条岚图泰山半年微博，结合 5 个竞品（问界M8 / 理想L8 / 小鹏GX / 极氪8X / 蔚来ES8）对比，分析如下：")
        P("")
        opponents = [c for c in cars if c["label"] != "岚图泰山X8"]

        P("### 1) 发文密度")
        P("")
        if opponents:
            avg_opp = mean([len(c["weibos"]) for c in opponents])
            if lt_total > avg_opp * 1.2:
                P(f"- 岚图泰山X8 发文 {lt_total} 条，**高于 5 竞品均值 {avg_opp:.0f} 条**（高 {(lt_total/avg_opp-1)*100:.0f}%）")
            elif lt_total < avg_opp * 0.8:
                P(f"- 岚图泰山X8 发文 {lt_total} 条，**低于 5 竞品均值 {avg_opp:.0f} 条**（低 {(1-lt_total/avg_opp)*100:.0f}%）")
            else:
                P(f"- 岚图泰山X8 发文 {lt_total} 条，与 5 竞品均值 {avg_opp:.0f} 持平")
        P("")

        P("### 2) 互动质量")
        P("")
        lt_avg_eng = avg([w["_engagement"] for w in lt["weibos"]])
        opp_avg_eng = avg([w["_engagement"] for c in opponents for w in c["weibos"]])
        P(f"- 岚图泰山X8 单条均互动 **{lt_avg_eng:.0f}**，5 竞品合计均互动 **{opp_avg_eng:.0f}**")
        P("")

        P("### 3) 动作结构对比")
        P("")
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
        P("**岚图泰山X8 显著偏多 / 偏少的动作类型（按差距绝对值 Top 8）：**")
        P("")
        P("| 动作类型 | 岚图泰山X8 占比 | 5 竞品均占比 | 差距 |")
        P("|---|---|---|---|")
        for tag, lt_p, opp_p, diff in differences[:8]:
            sign = "+" if diff > 0 else ""
            P(f"| {tag} | {lt_p:.0f}% | {opp_p:.0f}% | {sign}{diff:.0f}pp |")
        P("")

        P("### 4) 战术建议")
        P("")
        suggestions = []
        for tag, lt_p, opp_p, diff in differences[:8]:
            if diff > 8:
                suggestions.append(f"- **【削减】{tag}** 占比 {lt_p:.0f}%，竞品均值 {opp_p:.0f}%（高 {diff:+.0f}pp）— 可适度减少，腾出版位做其他动作")
            elif diff < -8:
                suggestions.append(f"- **【补齐】{tag}** 占比 {lt_p:.0f}%，竞品均值 {opp_p:.0f}%（低 {diff:+.0f}pp）— 竞品都在做，岚图泰山X8 可参考补齐")
        if suggestions:
            for s in suggestions:
                P(s)
        else:
            P("- 动作结构与竞品基本对齐，无显著结构缺口")
        P("")

        P("### 5) 竞品爆款打法可借鉴")
        P("")
        P("**5 个竞品的 Top 2 爆款合计 10 条，从中提炼方向：**")
        P("")
        opp_top = []
        for c in opponents:
            tops = sorted(c["weibos"], key=lambda x: -x["_engagement"])[:2]
            for tw in tops:
                opp_top.append({"car": c["label"], "w": tw})
        opp_top.sort(key=lambda x: -x["w"]["_engagement"])
        for case in opp_top[:10]:
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
    P(f"- 蔚来ES8 数据来自任务A 之前已抓取的 5675889356.json (全年数据中切片)")
    P("")

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(L))
    print(f"\n报告 → {REPORT_PATH}")


if __name__ == "__main__":
    main()
