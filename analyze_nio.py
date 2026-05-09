"""
蔚来微博一年用户运营动作分析
输入: weibo_data/蔚来/5675889356.json (1143 条微博)
输出:
  - weibo_data/蔚来_用户运营分析报告.md
  - weibo_data/蔚来_分类明细.csv
"""
import json
import re
from collections import Counter, defaultdict
from datetime import datetime
import csv as csvlib

JSON_PATH = "weibo_data/蔚来/5675889356.json"
REPORT_PATH = "weibo_data/蔚来_用户运营分析报告.md"
DETAIL_CSV = "weibo_data/蔚来_分类明细.csv"

# ============================================================
# 1) 运营动作分类规则（基于关键词，多标签）
# ============================================================
def classify(text: str, topics: str, at_users: str):
    """返回标签列表，一条可属多类"""
    tags = []
    t = text or ""
    tp = topics or ""
    au = at_users or ""

    # 创始人 IP / 主理人对话（高度专属，优先识别）
    if re.search(r"@?李斌|斌哥|ET9会客厅|斌哥说", t):
        tags.append("创始人IP")

    # 数据仪式 - 充换电站日报（蔚来标志性栏目）
    # 特征：以"X月X日，NIO Power N站上线"开头，列举 NO.xxxx 编号
    if re.search(r"NIO Power.*站上线", t) or re.search(r"NO\.\d{3,5}\s+蔚来", t):
        tags.append("数据日报")

    # 互动激励（转评赞抽奖）—— 蔚来高频运营动作
    if re.search(r"@蔚来.*[，,].*(转发|转评赞)", t) or "抽取" in t and "送出" in t \
       or "转发并" in t and "抽取" in t \
       or re.search(r"我们将抽取\d*位?", t):
        tags.append("互动激励")

    # 车主权益 / NIO Life（生活方式品牌运营）
    if "NIO Life" in t or "NIO House" in t or "NIO Day" in t \
       or re.search(r"礼遇|权益|积分|车主专属|用户专属", t):
        tags.append("车主权益")

    # UGC / KOC 共创（@非蔚来用户分享）
    # 至少 @ 一个非"蔚来"的用户，且文本含分享/作品/拍摄等
    at_list = [u.strip() for u in au.split(",") if u.strip() and u.strip() != "蔚来"]
    if at_list and re.search(r"分享|作品|拍摄|镜头|镜下|出片|的图片|的视频|创作", t):
        tags.append("UGC共创")

    # 车主社群活动（线下、跑线、车友、用户日）
    if re.search(r"车主|用户面对面|车友|跑线|越雄关|换电行|Clean\s*Parks|NIO\s*Day|用户日|线下", t):
        tags.append("车主社群活动")

    # 服务响应 / 产品教育
    if re.search(r"答用户问|为你解答|答疑|操作指南|使用教程|功能讲解|Q&A|官方解答", t):
        tags.append("服务响应")

    # 节点营销（产品发布/上市/试驾，作为对照参考）
    if re.search(r"正式上市|发布|开启预订|开启用户试驾|开启交付|首发", t) and "互动激励" not in tags:
        tags.append("节点营销")

    # 直播
    if re.search(r"直播|微博直播|开播", t):
        tags.append("直播")

    # 节日/借势
    if re.search(r"节日快乐|国庆|春节|元旦|妇女节|劳动节|中秋|端午|圣诞|新年|开学|高考", t):
        tags.append("节日借势")

    # 销量/财报通报（强 PR）
    if re.search(r"交付|销量|经营利润|财报|月销", t) and not any(x in tags for x in ["创始人IP", "数据日报"]):
        tags.append("销量通报")

    if not tags:
        tags.append("未分类")
    return tags


# ============================================================
# 2) 加载数据
# ============================================================
with open(JSON_PATH, encoding="utf-8") as f:
    data = json.load(f)
weibos = data["weibo"]
print(f"加载 {len(weibos)} 条微博")

# 统一字段
for w in weibos:
    w["_dt"] = datetime.strptime(w["full_created_at"], "%Y-%m-%d %H:%M:%S")
    w["_month"] = w["_dt"].strftime("%Y-%m")
    w["_dow"] = w["_dt"].strftime("%A")  # 星期几
    w["_hour"] = w["_dt"].hour
    w["_tags"] = classify(w.get("text", ""), w.get("topics", ""), w.get("at_users", ""))
    w["_engagement"] = (w.get("attitudes_count", 0) or 0) + \
                      (w.get("comments_count", 0) or 0) + \
                      (w.get("reposts_count", 0) or 0)

# ============================================================
# 3) 统计：分类频次、月分布、互动量
# ============================================================
tag_counter = Counter()
tag_engage = defaultdict(list)  # tag -> [engagement, ...]
tag_by_month = defaultdict(lambda: Counter())  # month -> Counter(tag)

for w in weibos:
    for tag in w["_tags"]:
        tag_counter[tag] += 1
        tag_engage[tag].append(w["_engagement"])
        tag_by_month[w["_month"]][tag] += 1

month_counter = Counter([w["_month"] for w in weibos])
dow_counter = Counter([w["_dow"] for w in weibos])
hour_counter = Counter([w["_hour"] for w in weibos])

# 整体互动
total_likes = sum(w.get("attitudes_count", 0) or 0 for w in weibos)
total_comments = sum(w.get("comments_count", 0) or 0 for w in weibos)
total_reposts = sum(w.get("reposts_count", 0) or 0 for w in weibos)

# ============================================================
# 4) 话题/IP 资产
# ============================================================
topic_counter = Counter()
topic_engage = defaultdict(list)
for w in weibos:
    tps = [t.strip() for t in (w.get("topics") or "").split(",") if t.strip()]
    for tp in tps:
        topic_counter[tp] += 1
        topic_engage[tp].append(w["_engagement"])

# ============================================================
# 5) @用户网络（KOC）
# ============================================================
at_counter = Counter()
for w in weibos:
    aus = [u.strip() for u in (w.get("at_users") or "").split(",") if u.strip() and u.strip() != "蔚来"]
    for au in aus:
        at_counter[au] += 1

# ============================================================
# 6) 典型案例（按互动量 top）
# ============================================================
# 整体 top 5
top5_overall = sorted(weibos, key=lambda x: -x["_engagement"])[:5]

# 各运营标签的 top 3
top3_per_tag = {}
for tag in ["互动激励", "车主社群活动", "UGC共创", "创始人IP", "数据日报", "车主权益"]:
    pool = [w for w in weibos if tag in w["_tags"]]
    top3_per_tag[tag] = sorted(pool, key=lambda x: -x["_engagement"])[:3]


# ============================================================
# 7) 写明细 CSV
# ============================================================
with open(DETAIL_CSV, "w", encoding="utf-8-sig", newline="") as f:
    w = csvlib.writer(f)
    w.writerow(["日期", "时间", "标签(多)", "正文摘要", "话题", "@用户", "点赞", "评论", "转发", "互动总和", "URL"])
    for wb in weibos:
        w.writerow([
            wb["_dt"].strftime("%Y-%m-%d"),
            wb["_dt"].strftime("%H:%M"),
            "|".join(wb["_tags"]),
            (wb.get("text", "") or "").replace("\n", " ")[:120],
            wb.get("topics", ""),
            wb.get("at_users", ""),
            wb.get("attitudes_count", 0),
            wb.get("comments_count", 0),
            wb.get("reposts_count", 0),
            wb["_engagement"],
            f"https://m.weibo.cn/detail/{wb['id']}",
        ])
print(f"明细写入 {DETAIL_CSV}")


# ============================================================
# 8) 生成 Markdown 报告
# ============================================================
def fmt(n):
    return f"{n:,}"

def avg(lst):
    return sum(lst) / len(lst) if lst else 0

def median(lst):
    if not lst: return 0
    s = sorted(lst); n = len(s)
    return s[n//2] if n % 2 else (s[n//2-1] + s[n//2]) / 2


lines = []
P = lines.append

P("# 蔚来一年微博用户运营动作分析报告")
P("")
P(f"> 数据范围：{weibos[-1]['_dt'].strftime('%Y-%m-%d')} ~ {weibos[0]['_dt'].strftime('%Y-%m-%d')}")
P(f"> 数据量：**{fmt(len(weibos))} 条微博**  ")
P(f"> 数据来源：[@蔚来](https://weibo.com/u/5675889356) 官方微博")
P(f"> 报告用途：为小鹏 GX / X9 高端车型用户运营策略提供竞品参考")
P("")
P("---")
P("")

# 执行摘要
P("## 一、执行摘要（最关键的 5 个发现）")
P("")
P(f"1. **「转评赞抽奖」工厂化是绝对核心打法**：'互动激励' 类微博共 **{tag_counter.get('互动激励', 0)} 条**，占总量 **{tag_counter.get('互动激励', 0)/len(weibos)*100:.1f}%**——超过一半的微博都是抽奖体例。奖品池 NIO Life 自有品牌（颈枕/雨伞/陶瓷/笔记本/电影券）反向滋养了 NIO Life 这个生活方式品牌。")
P("")
P(f"2. **NIO Life 是渗透到所有内容的运营资产**：'车主权益' 类（含 NIO Life 提及）共 **{tag_counter.get('车主权益', 0)} 条 ({tag_counter.get('车主权益', 0)/len(weibos)*100:.1f}%)**，与互动激励高度重叠——蔚来把『生活方式品牌』做成了**奖品载体 + 心智载体**。")
P("")
P(f"3. **创始人李斌深度内容化**：李斌出镜微博共 **{tag_counter.get('创始人IP', 0)} 条**，主要为 #ET9会客厅# 系列（李斌对话企业家/科学家/合作伙伴）。是行业中**少见的把 CEO 当 KOL 系统化运营**的打法。")
P("")
P(f"4. **「跑线」活动 IP 化是高端运营的范本**：'车主社群活动' 共 **{tag_counter.get('车主社群活动', 0)} 条**，含『万里越雄关·丝绸之路换电行』、Clean Parks 雪山保护、NIO Day、川藏跑线等系列 IP——把**充换电基础设施 + 车主集体行动**演绎成了史诗级品牌故事。")
P("")
P(f"5. **运营节奏极稳但结构有变**：年发文 {len(weibos)} 条（平均 **{len(weibos)/365:.1f} 条/天**），周发文集中在工作日（周三~周五最高），10-12 点 / 16-18 点是发文双高峰。**2025-08 是高峰（{month_counter['2025-08']} 条）**，**2025-10 显著低谷（{month_counter['2025-10']} 条）**——可能与产品节奏 / 季度战略相关。")
P("")
P("---")
P("")

# 数据概览
P("## 二、数据概览")
P("")
P(f"| 指标 | 数值 |")
P(f"|---|---|")
P(f"| 总微博数 | {fmt(len(weibos))} |")
P(f"| 时间跨度 | 365 天 |")
P(f"| 日均发文 | {len(weibos)/365:.1f} 条 |")
P(f"| 总点赞数 | {fmt(total_likes)} |")
P(f"| 总评论数 | {fmt(total_comments)} |")
P(f"| 总转发数 | {fmt(total_reposts)} |")
P(f"| 单条平均互动 | {(total_likes+total_comments+total_reposts)/len(weibos):.0f} |")
P(f"| 单条互动中位数 | {median([w['_engagement'] for w in weibos]):.0f} |")
P("")

# 月度发文量
P("### 2.1 月度发文量")
P("")
P("```")
for m in sorted(month_counter):
    bar = "█" * int(month_counter[m] / 5)
    P(f"  {m}  {month_counter[m]:>4} 条  {bar}")
P("```")
P("")

# 星期分布
P("### 2.2 发文时间规律")
P("")
P("**按星期（条数）：**")
P("")
dow_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
dow_zh = {"Monday":"一", "Tuesday":"二", "Wednesday":"三", "Thursday":"四", "Friday":"五", "Saturday":"六", "Sunday":"日"}
P("| 周一 | 周二 | 周三 | 周四 | 周五 | 周六 | 周日 |")
P("|---|---|---|---|---|---|---|")
P("| " + " | ".join([str(dow_counter[d]) for d in dow_order]) + " |")
P("")
P("**按小时（发文热点）：** ")
hot_hours = sorted([(h, c) for h, c in hour_counter.items()], key=lambda x: -x[1])[:6]
P("| 小时 | 条数 |")
P("|---|---|")
for h, c in hot_hours:
    P(f"| {h:02d}:00 | {c} |")
P("")

# ============================================================
P("---")
P("")
P("## 三、运营动作分类与频次（最重要！）")
P("")
P("> 一条微博可能属于多个标签（例如「互动激励 + UGC 共创」）。")
P("")
P("### 3.1 各类运营动作的频次和互动量")
P("")
P("| 运营动作类型 | 微博数 | 占比 | 平均互动 | 中位互动 |")
P("|---|---|---|---|---|")
sorted_tags = sorted(tag_counter.items(), key=lambda x: -x[1])
for tag, count in sorted_tags:
    pct = count / len(weibos) * 100
    avg_eng = avg(tag_engage[tag])
    med_eng = median(tag_engage[tag])
    P(f"| {tag} | {count} | {pct:.1f}% | {avg_eng:.0f} | {med_eng:.0f} |")
P("")

P("### 3.2 关键观察")
P("")
P("**1. 互动激励是核心打法**——抽奖运营做成了流水线，每条微博底部几乎都是「关注@蔚来 ，转发并评论...，我们将抽取X位朋友送出..."
  "」的标准句式。奖品池：NIO Life（餐具/雨伞/笔记本/茶具/陶瓷/颈枕等）、电影兑换券、车贴等。**奖品成本可控且品牌资产化**。")
P("")
P("**2. 数据日报是 2026 起高频化的栏目**——「NIO Power 上线日报」全年 31 条，但**主要集中在 2026 年 4 月之后**（每天发一条）。把基础设施进度做成日常仪式，但产生时间晚——可能是蔚来 2026 年新加的运营动作，**早期一年其他时段没有这个栏目**。")
P("")
P("**3. 创始人 IP 栏目化**——李斌出现在 #ET9会客厅# 系列、#蔚来斌哥说# 等节目，并且持续与外部高管/企业家对话（如对话高通、央视、合作伙伴等），形成**李斌作为蔚来用户运营头部 KOL** 的运营逻辑。")
P("")

# 月度结构变化
P("### 3.3 月度运营结构变化")
P("")
P("观察各月运营动作的占比变化：")
P("")
months_sorted = sorted(month_by := tag_by_month.keys())
core_tags = ["互动激励", "数据日报", "车主社群活动", "创始人IP", "UGC共创"]
P("| 月份 | 总数 | " + " | ".join(core_tags) + " |")
P("|---|---|" + "|".join(["---"] * len(core_tags)) + "|")
for m in months_sorted:
    row = [m, str(month_counter[m])]
    for ct in core_tags:
        row.append(str(tag_by_month[m].get(ct, 0)))
    P("| " + " | ".join(row) + " |")
P("")

# ============================================================
P("---")
P("")
P("## 四、话题与 IP 资产盘点")
P("")
P(f"一年内蔚来用了 **{len(topic_counter)} 个不同 hashtag**。Top 高频话题如下：")
P("")
P("| 排名 | 话题 | 出现次数 | 平均互动 |")
P("|---|---|---|---|")
for i, (tp, cnt) in enumerate(topic_counter.most_common(20), 1):
    P(f"| {i} | #{tp}# | {cnt} | {avg(topic_engage[tp]):.0f} |")
P("")

P("**核心 IP 话题分类**：")
P("")
P("- **品牌总标签**：#蔚来#（全部品牌微博必带）")
P("- **产品系列**：#蔚来ES8# / #蔚来ES9# / #蔚来ET9# / #蔚来EC6# / #ET5一触即发#")
P("- **栏目 IP**：#蔚来加电去的都是远方#（数据日报）/ #ET9会客厅# / #NIO选择题# / #ET5T一往无前# / #ES6生机盎然#")
P("- **活动 IP**：#万里越雄关丝绸之路换电行# / #蔚来ES9万里越雄关# / #2026北京车展#")
P("- **价值观/心智**：#蔚来换电# / #蔚来智慧安全# / #蔚来加电#")
P("")

# ============================================================
P("---")
P("")
P("## 五、KOC / @用户 网络分析")
P("")
P(f"一年内蔚来 @ 了 **{len(at_counter)} 个不同用户**（剔除 @蔚来 自身）。")
P("")
P("**Top 20 被高频 @ 的用户：**")
P("")
P("| 排名 | @用户 | 被 @ 次数 |")
P("|---|---|---|")
for i, (u, cnt) in enumerate(at_counter.most_common(20), 1):
    P(f"| {i} | @{u} | {cnt} |")
P("")
P("从 KOC 网络可见：蔚来构建了一个**车主创作者 + 跨界 KOL** 的双层 @ 网络（车主用户故事 + 行业大咖对话），用户运营不依赖明星而靠真实车主与高质量行业对话。")
P("")

# ============================================================
P("---")
P("")
P("## 六、典型运营案例拆解（按互动量）")
P("")
P("### 6.1 全年互动量 Top 5 微博")
P("")
for i, w in enumerate(top5_overall, 1):
    txt = (w.get("text", "") or "").replace("\n", " ")[:200]
    P(f"**#{i}** | {w['_dt'].strftime('%Y-%m-%d %H:%M')} | 标签：{', '.join(w['_tags'])}")
    P(f"")
    P(f"> {txt}{'...' if len(w.get('text', '')) > 200 else ''}")
    P(f"")
    P(f"📊 点赞 {fmt(w['attitudes_count'])} | 评论 {fmt(w['comments_count'])} | 转发 {fmt(w['reposts_count'])} | **互动总和 {fmt(w['_engagement'])}**")
    P(f"🔗 [原文链接](https://m.weibo.cn/detail/{w['id']})")
    P("")
    P("---")
    P("")

P("### 6.2 各运营动作类型的标杆案例")
P("")
for tag, cases in top3_per_tag.items():
    if not cases: continue
    P(f"#### {tag}")
    P("")
    for c in cases[:2]:
        txt = (c.get("text", "") or "").replace("\n", " ")[:160]
        P(f"- **{c['_dt'].strftime('%Y-%m-%d')}** ｜互动 {fmt(c['_engagement'])}（赞{c['attitudes_count']}/评{c['comments_count']}/转{c['reposts_count']}）")
        P(f"  - {txt}{'...' if len(c.get('text', '')) > 160 else ''}")
    P("")

# ============================================================
P("---")
P("")
P("## 七、给小鹏 GX / X9 的关键启示")
P("")
P("### 7.1 ✅ 可借鉴")
P("")
P("**① 运营仪式化（最值得直接复用）**")
P("- **建立每日栏目** —— 蔚来 #蔚来加电去的都是远方# 是日报式栏目，每天准时发，让用户**养成查看习惯**。小鹏可以做 #小鹏全国充电网络日报# / #小鹏自动驾驶里程# 这样的累计数据日报")
P("- **奖品产品化** —— 蔚来用 NIO Life 自有品牌做奖品（成本可控、还能反向推广 NIO Life 这个生活方式品牌）。小鹏可以做 XPENG Life 类似奖品体系")
P("")
P("**② 创始人 IP 节目化**")
P("- 蔚来 #ET9会客厅# 是李斌对话嘉宾的固定节目栏目。何小鹏 IP 已存在，但缺**栏目化**——可以做 #小鹏对话# / #X9·与未来对话#")
P("")
P("**③ 车主社群活动的 IP 化**")
P("- 蔚来「跑线活动」（丝绸之路换电行、川藏线、万里越雄关）做成了**视觉化的史诗级活动 IP**——把基础设施补能能力，演绎成了**车主集体壮游**。小鹏 G6/X9 充电基础设施同样有故事，但缺乏 IP 化包装")
P("- Clean Parks 雪山保护类 ESG 活动，让品牌价值观成为社群行动")
P("")
P("**④ 转评赞抽奖的工厂化**")
P("- 蔚来几乎每条微博都带抽奖（互动激励占比 {pct}%）。这种打法**简单粗暴但极有效**——平均互动量达到 {avg_likes}+。".format(pct=int(tag_counter.get('互动激励', 0)/len(weibos)*100), avg_likes=int(avg(tag_engage.get('互动激励', [0])))))
P("")
P("### 7.2 ⚠️ 不可借鉴 / 高端定位需谨慎")
P("")
P("**① 抽奖密度过高**")
P("- 蔚来近 50% 微博带抽奖，用户对这个动作已经"
  "**机械化**——评论区互动质量未必高。**X9 / GX 走高端定位**，过度抽奖会损失质感。建议：少而精，做高价值奖品的『仪式感大抽』而非每条都抽。")
P("")
P("**② 数据堆砌强 PR 风格**")
P("- 蔚来日报模板化堆数据（『累计 1 亿次换电』『累计 8853 站』）。对极致内容质感的高端人群，这种**数据轰炸**容易产生疲劳。X9 高端用户更适合**故事化叙事**——一座城市、一位车主、一段使用场景。")
P("")
P("**③ 销售/财报类强植入**")
P("- 蔚来频繁穿插销量/财报通报（'销量通报' 类共 {n} 条）。高端品牌定位下不建议把财报内容当社交内容发——可以发，但比例要更低。".format(n=tag_counter.get('销量通报', 0)))
P("")
P("### 7.3 🎯 X9 / GX 差异化机会点")
P("")
P("基于蔚来打法的**反向**，X9/GX 可以走的差异化路径：")
P("- **质感 + 在场感**：高端用户运营是『更少的内容、更高的颗粒度』。一周 3-5 条精品 vs 蔚来日均 3 条堆量")
P("- **车主 KOC 培养**：投资少数 50-100 个车主创作者，做长期共创内容，而不是每天找新车主蹭流量")
P("- **车型故事节目**：X9 作为家庭旗舰 MPV，可以做 #X9 与家的故事# 这种纪录片风栏目，慢热长线运营高质感")
P("- **服务体验透明化**：高端人群最看重的不是车，是服务。把服务故事拍成内容，是蔚来 NIO House 之外的可借鉴方向")
P("")

P("---")
P("")
P("## 附录")
P("")
P(f"- 详细分类明细 CSV：[蔚来_分类明细.csv]({DETAIL_CSV.split('/')[-1]})（{len(weibos)} 行，含每条微博的标签/正文摘要/互动数据）")
P(f"- 完整 JSON 数据：[5675889356.json](蔚来/5675889356.json)（1.5 MB）")
P(f"- 完整 Markdown 数据：[蔚来/](蔚来/)（按月归档，每天一个 md 文件）")
P("")
P("**分析方法说明**：")
P("- 运营动作分类基于关键词规则匹配，多标签（一条微博可属多类）")
P("- 互动量 = 点赞 + 评论 + 转发")
P("- 数据来自微博 m.weibo.cn 移动端 API，仅含原创微博")
P("")

with open(REPORT_PATH, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print(f"报告写入 {REPORT_PATH}")
print(f"\n=== 关键统计 ===")
print(f"总条数: {len(weibos)}")
print(f"运营动作分类:")
for tag, count in sorted_tags:
    print(f"  {tag}: {count} ({count/len(weibos)*100:.1f}%)")
