"""
蔚来微博一年用户运营动作分析 - 生成 HTML 可视化报告
咨询公司报告风格（McKinsey / BCG 视觉语言）
输出: weibo_data/蔚来_用户运营分析报告.html
"""
import json
import re
import html
from collections import Counter, defaultdict
from datetime import datetime

JSON_PATH = "weibo_data/蔚来/5675889356.json"
HTML_PATH = "weibo_data/蔚来_用户运营分析报告.html"

# ============================================================
# 分类规则（与 analyze_nio.py 保持一致）
# ============================================================
def classify(text, topics, at_users):
    tags = []
    t = text or ""
    au = at_users or ""
    if re.search(r"@?李斌|斌哥|ET9会客厅|斌哥说", t):
        tags.append("创始人IP")
    if re.search(r"NIO Power.*站上线", t) or re.search(r"NO\.\d{3,5}\s+蔚来", t):
        tags.append("数据日报")
    if re.search(r"@蔚来.*[，,].*(转发|转评赞)", t) or ("抽取" in t and "送出" in t) \
       or ("转发并" in t and "抽取" in t) or re.search(r"我们将抽取\d*位?", t):
        tags.append("互动激励")
    if "NIO Life" in t or "NIO House" in t or "NIO Day" in t \
       or re.search(r"礼遇|权益|积分|车主专属|用户专属", t):
        tags.append("车主权益")
    at_list = [u.strip() for u in au.split(",") if u.strip() and u.strip() != "蔚来"]
    if at_list and re.search(r"分享|作品|拍摄|镜头|镜下|出片|的图片|的视频|创作", t):
        tags.append("UGC共创")
    if re.search(r"车主|用户面对面|车友|跑线|越雄关|换电行|Clean\s*Parks|NIO\s*Day|用户日|线下", t):
        tags.append("车主社群活动")
    if re.search(r"答用户问|为你解答|答疑|操作指南|使用教程|功能讲解|Q&A|官方解答", t):
        tags.append("服务响应")
    if re.search(r"正式上市|发布|开启预订|开启用户试驾|开启交付|首发", t) and "互动激励" not in tags:
        tags.append("节点营销")
    if re.search(r"直播|微博直播|开播", t):
        tags.append("直播")
    if re.search(r"节日快乐|国庆|春节|元旦|妇女节|劳动节|中秋|端午|圣诞|新年|开学|高考", t):
        tags.append("节日借势")
    if re.search(r"交付|销量|经营利润|财报|月销", t) and not any(x in tags for x in ["创始人IP", "数据日报"]):
        tags.append("销量通报")
    if not tags:
        tags.append("未分类")
    return tags

# ============================================================
# 加载数据
# ============================================================
with open(JSON_PATH, encoding="utf-8") as f:
    data = json.load(f)
weibos = data["weibo"]

for w in weibos:
    w["_dt"] = datetime.strptime(w["full_created_at"], "%Y-%m-%d %H:%M:%S")
    w["_month"] = w["_dt"].strftime("%Y-%m")
    w["_dow"] = w["_dt"].weekday()
    w["_hour"] = w["_dt"].hour
    w["_tags"] = classify(w.get("text", ""), w.get("topics", ""), w.get("at_users", ""))
    w["_engagement"] = (w.get("attitudes_count", 0) or 0) + \
                       (w.get("comments_count", 0) or 0) + \
                       (w.get("reposts_count", 0) or 0)

tag_counter = Counter()
tag_engage = defaultdict(list)
for w in weibos:
    for tag in w["_tags"]:
        tag_counter[tag] += 1
        tag_engage[tag].append(w["_engagement"])

month_counter = Counter([w["_month"] for w in weibos])
dow_counter = Counter([w["_dow"] for w in weibos])
hour_counter = Counter([w["_hour"] for w in weibos])

total_likes = sum(w.get("attitudes_count", 0) or 0 for w in weibos)
total_comments = sum(w.get("comments_count", 0) or 0 for w in weibos)
total_reposts = sum(w.get("reposts_count", 0) or 0 for w in weibos)

topic_counter = Counter()
topic_engage = defaultdict(list)
for w in weibos:
    tps = [t.strip() for t in (w.get("topics") or "").split(",") if t.strip()]
    for tp in tps:
        topic_counter[tp] += 1
        topic_engage[tp].append(w["_engagement"])

at_counter = Counter()
for w in weibos:
    aus = [u.strip() for u in (w.get("at_users") or "").split(",") if u.strip() and u.strip() != "蔚来"]
    for au in aus:
        at_counter[au] += 1

top5_overall = sorted(weibos, key=lambda x: -x["_engagement"])[:5]
top3_per_tag = {}
for tag in ["互动激励", "车主社群活动", "UGC共创", "创始人IP", "数据日报", "车主权益"]:
    pool = [w for w in weibos if tag in w["_tags"]]
    top3_per_tag[tag] = sorted(pool, key=lambda x: -x["_engagement"])[:3]

def avg(lst): return sum(lst) / len(lst) if lst else 0
def median(lst):
    if not lst: return 0
    s = sorted(lst); n = len(s)
    return s[n//2] if n % 2 else (s[n//2-1] + s[n//2]) / 2
def fmt(n): return f"{n:,}"

# ============================================================
# Chart.js 数据
# ============================================================
months_sorted = sorted(month_counter.keys())
chart_months = json.dumps(months_sorted, ensure_ascii=False)
chart_month_counts = json.dumps([month_counter[m] for m in months_sorted])

display_tags_order = [tag for tag, _ in tag_counter.most_common() if tag != "未分类"]
chart_tag_labels = json.dumps(display_tags_order, ensure_ascii=False)
chart_tag_counts = json.dumps([tag_counter[t] for t in display_tags_order])
chart_tag_avg_eng = json.dumps([round(avg(tag_engage[t])) for t in display_tags_order])
chart_tag_pcts = json.dumps([round(tag_counter[t]/len(weibos)*100, 1) for t in display_tags_order])

dow_zh = ["MON","TUE","WED","THU","FRI","SAT","SUN"]
chart_dow_labels = json.dumps(dow_zh)
chart_dow_counts = json.dumps([dow_counter[i] for i in range(7)])

hours_sorted = list(range(24))
chart_hour_labels = json.dumps([f"{h:02d}" for h in hours_sorted])
chart_hour_counts = json.dumps([hour_counter[h] for h in hours_sorted])

# ============================================================
# helpers
# ============================================================
def h(s): return html.escape(str(s)) if s is not None else ""
def text_preview(t, n=180):
    if not t: return ""
    t = t.replace("\n", " ").strip()
    return h(t[:n] + ("…" if len(t) > n else ""))

# ============================================================
# 案例 HTML
# ============================================================
top5_html_parts = []
for i, w in enumerate(top5_overall, 1):
    tags_html = "".join(f'<span class="tag-chip">{h(t)}</span>' for t in w["_tags"])
    top5_html_parts.append(f"""
    <article class="case">
      <div class="case-num">{i:02d}</div>
      <div class="case-content">
        <div class="case-head">
          <span class="case-date">{w['_dt'].strftime('%Y · %m · %d  %H:%M')}</span>
          <div class="case-tags">{tags_html}</div>
        </div>
        <p class="case-text">{text_preview(w.get('text', ''), 320)}</p>
        <div class="case-foot">
          <div class="case-metrics">
            <span><em>{fmt(w['attitudes_count'])}</em> 点赞</span>
            <span><em>{fmt(w['comments_count'])}</em> 评论</span>
            <span><em>{fmt(w['reposts_count'])}</em> 转发</span>
            <span class="case-total"><em>{fmt(w['_engagement'])}</em> 总互动</span>
          </div>
          <a href="https://m.weibo.cn/detail/{w['id']}" target="_blank" rel="noopener" class="case-link">原文 ↗</a>
        </div>
      </div>
    </article>
    """)
top5_html = "\n".join(top5_html_parts)

per_tag_html_parts = []
for tag, cases in top3_per_tag.items():
    if not cases: continue
    cards = []
    for c in cases[:2]:
        cards.append(f"""
        <li class="bench-item">
          <div class="bench-meta"><span>{c['_dt'].strftime('%Y-%m-%d')}</span><span class="bench-engage">总互动 <em>{fmt(c['_engagement'])}</em></span></div>
          <p class="bench-text">{text_preview(c.get('text', ''), 180)}</p>
          <div class="bench-stats">点赞 {c['attitudes_count']} · 评论 {c['comments_count']} · 转发 {c['reposts_count']}</div>
        </li>
        """)
    per_tag_html_parts.append(f"""
    <div class="bench-block">
      <h4 class="bench-title">{h(tag)}</h4>
      <ul class="bench-list">{''.join(cards)}</ul>
    </div>
    """)
per_tag_html = "\n".join(per_tag_html_parts)

# 运营动作频次表格
tag_table_rows = ""
for tag, count in tag_counter.most_common():
    pct = count / len(weibos) * 100
    avg_eng = avg(tag_engage[tag])
    med_eng = median(tag_engage[tag])
    tag_table_rows += f"""
    <tr>
      <td class="td-name">{h(tag)}</td>
      <td class="td-num">{count}</td>
      <td class="td-bar">
        <div class="bar-bg"><div class="bar-fill" style="width:{min(pct*1.7, 100)}%"></div></div>
        <span class="td-pct">{pct:.1f}%</span>
      </td>
      <td class="td-num">{avg_eng:.0f}</td>
      <td class="td-num">{med_eng:.0f}</td>
    </tr>
    """

topic_table_rows = ""
for i, (tp, cnt) in enumerate(topic_counter.most_common(15), 1):
    topic_table_rows += f"""
    <tr><td class="td-num td-rank">{i:02d}</td><td>#{h(tp)}#</td><td class="td-num">{cnt}</td><td class="td-num">{avg(topic_engage[tp]):.0f}</td></tr>
    """

koc_table_rows = ""
for i, (u, cnt) in enumerate(at_counter.most_common(15), 1):
    koc_table_rows += f"""
    <tr><td class="td-num td-rank">{i:02d}</td><td>@{h(u)}</td><td class="td-num">{cnt}</td></tr>
    """

date_range = f"{weibos[-1]['_dt'].strftime('%Y.%m.%d')} – {weibos[0]['_dt'].strftime('%Y.%m.%d')}"

# ============================================================
# CSS - 咨询公司风格 (McKinsey/BCG 视觉语言)
# ============================================================
CSS = """
@import url('https://fonts.googleapis.com/css2?family=Source+Serif+4:opsz,wght@8..60,400;8..60,600;8..60,700&family=Inter:wght@400;500;600;700&family=Noto+Serif+SC:wght@400;500;600;700&display=swap');

:root {
  --navy:        #051c2c;
  --navy-mid:    #034b6e;
  --cyan:        #2f99ce;
  --gold:        #c5a45f;
  --red:         #b03a48;
  --bg:          #ffffff;
  --bg-section:  #f4f4f0;
  --bg-card:     #ffffff;
  --border:      #d8d8d2;
  --border-soft: #ebebe5;
  --text:        #051c2c;
  --text-mid:    #4d5358;
  --text-light:  #8d8d85;
  --grid-line:   #e8e8e2;
}

* { box-sizing: border-box; margin: 0; padding: 0; }

html { font-size: 15px; }

body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, "PingFang SC", "Microsoft YaHei", "Helvetica Neue", sans-serif;
  color: var(--text);
  background: var(--bg);
  line-height: 1.65;
  font-feature-settings: 'tnum' on, 'lnum' on;
  -webkit-font-smoothing: antialiased;
}

.serif { font-family: 'Source Serif 4', 'Noto Serif SC', Georgia, "Songti SC", "STSong", serif; font-feature-settings: 'tnum' on; }

.container { max-width: 1400px; margin: 0 auto; padding: 0 56px; }

/* ============ COVER PAGE ============ */
.cover {
  background: var(--navy);
  color: white;
  padding: 80px 0 100px;
  position: relative;
  border-bottom: 4px solid var(--gold);
}
.cover::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 1px;
  background: linear-gradient(90deg, var(--gold) 0%, var(--cyan) 100%);
}
.cover-eyebrow {
  font-size: 11px;
  letter-spacing: 3px;
  text-transform: uppercase;
  color: var(--cyan);
  font-weight: 600;
  margin-bottom: 20px;
}
.cover-title {
  font-family: 'Source Serif 4', 'Noto Serif SC', Georgia, serif;
  font-size: 56px;
  font-weight: 600;
  line-height: 1.15;
  margin-bottom: 28px;
  max-width: 900px;
  letter-spacing: -0.5px;
}
.cover-subtitle {
  font-size: 17px;
  line-height: 1.7;
  max-width: 720px;
  color: rgba(255,255,255,0.78);
  font-weight: 400;
  margin-bottom: 60px;
}
.cover-meta {
  display: grid;
  grid-template-columns: repeat(4, auto);
  gap: 64px;
  border-top: 1px solid rgba(255,255,255,0.18);
  padding-top: 32px;
}
.cover-meta-item .label {
  font-size: 11px;
  letter-spacing: 2px;
  text-transform: uppercase;
  color: rgba(255,255,255,0.55);
  margin-bottom: 8px;
}
.cover-meta-item .value {
  font-family: 'Source Serif 4', 'Noto Serif SC', Georgia, serif;
  font-size: 22px;
  font-weight: 500;
  color: white;
}

/* ============ SECTION ============ */
section { padding: 80px 0; border-bottom: 1px solid var(--border); }
section:nth-of-type(even) { background: var(--bg-section); }

.section-header {
  display: flex;
  align-items: baseline;
  gap: 32px;
  margin-bottom: 56px;
  padding-bottom: 24px;
  border-bottom: 1px solid var(--border);
}
.section-num {
  font-family: 'Source Serif 4', Georgia, serif;
  font-size: 18px;
  font-weight: 400;
  color: var(--gold);
  letter-spacing: 4px;
  flex-shrink: 0;
  width: 80px;
}
.section-title {
  font-family: 'Source Serif 4', 'Noto Serif SC', Georgia, serif;
  font-size: 36px;
  font-weight: 600;
  color: var(--navy);
  letter-spacing: -0.3px;
  line-height: 1.2;
  flex: 1;
}
.section-deck {
  font-size: 15px;
  color: var(--text-mid);
  max-width: 720px;
  margin-top: 8px;
}

/* ============ KEY METRICS BAND ============ */
.metrics-band {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 0;
  border: 1px solid var(--border);
  background: var(--bg-card);
  margin-bottom: 0;
}
.metric {
  padding: 28px 24px;
  border-right: 1px solid var(--border);
}
.metric:last-child { border-right: none; }
.metric-label {
  font-size: 11px;
  letter-spacing: 1.5px;
  text-transform: uppercase;
  color: var(--text-light);
  margin-bottom: 12px;
  font-weight: 500;
}
.metric-value {
  font-family: 'Source Serif 4', Georgia, serif;
  font-size: 36px;
  font-weight: 600;
  color: var(--navy);
  line-height: 1;
  letter-spacing: -0.5px;
}
.metric-unit {
  font-family: 'Inter', sans-serif;
  font-size: 14px;
  font-weight: 400;
  color: var(--text-light);
  margin-left: 4px;
}

/* ============ EXECUTIVE SUMMARY ============ */
.findings {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1px;
  background: var(--border);
  border: 1px solid var(--border);
}
.finding {
  background: var(--bg-card);
  padding: 36px 40px;
}
.finding-num {
  font-family: 'Source Serif 4', Georgia, serif;
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 4px;
  color: var(--cyan);
  margin-bottom: 12px;
  text-transform: uppercase;
}
.finding h3 {
  font-family: 'Source Serif 4', 'Noto Serif SC', Georgia, serif;
  font-size: 21px;
  font-weight: 600;
  line-height: 1.35;
  color: var(--navy);
  margin-bottom: 14px;
  letter-spacing: -0.2px;
}
.finding p {
  font-size: 14.5px;
  color: var(--text-mid);
  line-height: 1.75;
}
.finding p b {
  color: var(--navy);
  font-weight: 600;
}
.finding.span-2 { grid-column: span 2; }

/* ============ EXHIBIT ============ */
.exhibit { margin-bottom: 56px; }
.exhibit:last-child { margin-bottom: 0; }
.exhibit-head {
  display: flex;
  align-items: baseline;
  gap: 16px;
  margin-bottom: 8px;
  padding-bottom: 12px;
  border-bottom: 2px solid var(--navy);
}
.exhibit-eyebrow {
  font-family: 'Source Serif 4', Georgia, serif;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 3px;
  text-transform: uppercase;
  color: var(--gold);
  flex-shrink: 0;
}
.exhibit-title {
  font-family: 'Source Serif 4', 'Noto Serif SC', Georgia, serif;
  font-size: 19px;
  font-weight: 600;
  color: var(--navy);
  letter-spacing: -0.1px;
}
.exhibit-deck {
  font-size: 13px;
  color: var(--text-mid);
  margin-top: 14px;
  margin-bottom: 24px;
  max-width: 880px;
  line-height: 1.7;
}
.exhibit-source {
  font-size: 11px;
  letter-spacing: 0.5px;
  color: var(--text-light);
  margin-top: 16px;
  font-style: italic;
}

.chart-canvas-wrap { position: relative; height: 320px; padding: 12px 0; }
.chart-canvas-wrap.tall { height: 420px; }
.chart-canvas-wrap.short { height: 240px; }

.exhibit-grid-2 {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 48px;
}
.exhibit-grid-2-uneven {
  display: grid;
  grid-template-columns: 5fr 7fr;
  gap: 48px;
}

/* ============ TABLE ============ */
table.exhibit-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13.5px;
  background: var(--bg-card);
}
table.exhibit-table th {
  text-align: left;
  padding: 14px 16px;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 1px;
  text-transform: uppercase;
  color: var(--text-light);
  border-bottom: 2px solid var(--navy);
  background: transparent;
}
table.exhibit-table td {
  padding: 14px 16px;
  border-bottom: 1px solid var(--border-soft);
  vertical-align: middle;
}
table.exhibit-table tr:hover td { background: var(--bg-section); }
table.exhibit-table .td-num { font-variant-numeric: tabular-nums; text-align: right; }
table.exhibit-table .td-rank { color: var(--text-light); font-size: 12px; width: 50px; }
table.exhibit-table .td-name { font-weight: 600; color: var(--navy); }
table.exhibit-table .td-bar { width: 32%; }

.bar-bg { display: inline-block; width: calc(100% - 56px); height: 6px; background: var(--border-soft); vertical-align: middle; margin-right: 12px; }
.bar-fill { height: 100%; background: var(--cyan); }
.td-pct { font-variant-numeric: tabular-nums; font-size: 12.5px; color: var(--text-mid); }

/* ============ CASES (Top 5) ============ */
.case {
  display: grid;
  grid-template-columns: 60px 1fr;
  gap: 32px;
  padding: 32px 0;
  border-bottom: 1px solid var(--border);
}
.case:first-of-type { padding-top: 8px; }
.case:last-of-type { border-bottom: none; }
.case-num {
  font-family: 'Source Serif 4', Georgia, serif;
  font-size: 36px;
  font-weight: 600;
  color: var(--gold);
  line-height: 1;
  font-variant-numeric: tabular-nums;
}
.case-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 14px;
  flex-wrap: wrap;
}
.case-date {
  font-size: 12px;
  letter-spacing: 1.5px;
  color: var(--text-light);
  font-variant-numeric: tabular-nums;
  font-weight: 500;
}
.case-tags { display: flex; gap: 6px; flex-wrap: wrap; }
.tag-chip {
  display: inline-block;
  padding: 3px 10px;
  border: 1px solid var(--border);
  border-radius: 2px;
  font-size: 11px;
  color: var(--navy-mid);
  letter-spacing: 0.3px;
  background: var(--bg-card);
}
.case-text {
  font-family: 'Source Serif 4', 'Noto Serif SC', Georgia, serif;
  font-size: 16px;
  line-height: 1.75;
  color: var(--text);
  margin-bottom: 18px;
}
.case-foot {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
  padding-top: 14px;
  border-top: 1px solid var(--border-soft);
}
.case-metrics {
  display: flex;
  gap: 28px;
  font-size: 12.5px;
  color: var(--text-mid);
}
.case-metrics em {
  font-style: normal;
  font-weight: 600;
  color: var(--navy);
  font-variant-numeric: tabular-nums;
  margin-right: 4px;
  font-size: 13.5px;
}
.case-total em { color: var(--cyan); }
.case-link {
  font-size: 12px;
  color: var(--navy-mid);
  text-decoration: none;
  letter-spacing: 0.5px;
  border-bottom: 1px solid var(--navy-mid);
  padding-bottom: 1px;
}
.case-link:hover { color: var(--cyan); border-color: var(--cyan); }

/* ============ BENCHMARK BLOCKS ============ */
.bench-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 32px;
  margin-top: 32px;
}
.bench-block {
  background: var(--bg-card);
  border: 1px solid var(--border);
  padding: 28px 32px;
}
.bench-title {
  font-family: 'Source Serif 4', 'Noto Serif SC', Georgia, serif;
  font-size: 18px;
  font-weight: 600;
  color: var(--navy);
  margin-bottom: 18px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border-soft);
}
.bench-list { list-style: none; }
.bench-item { padding: 16px 0; border-bottom: 1px dashed var(--border-soft); }
.bench-item:last-child { border-bottom: none; }
.bench-meta {
  display: flex;
  justify-content: space-between;
  font-size: 11.5px;
  letter-spacing: 1px;
  color: var(--text-light);
  text-transform: uppercase;
  font-weight: 500;
  margin-bottom: 8px;
}
.bench-engage em { font-style: normal; font-weight: 600; color: var(--cyan); font-variant-numeric: tabular-nums; }
.bench-text {
  font-size: 13.5px;
  color: var(--text);
  line-height: 1.7;
  margin-bottom: 8px;
}
.bench-stats {
  font-size: 11.5px;
  color: var(--text-light);
  font-variant-numeric: tabular-nums;
  letter-spacing: 0.3px;
}

/* ============ INSIGHTS ============ */
.insights { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1px; background: var(--border); border: 1px solid var(--border); }
.insight {
  background: var(--bg-card);
  padding: 36px 40px;
  position: relative;
}
.insight-marker {
  font-family: 'Source Serif 4', Georgia, serif;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 3px;
  text-transform: uppercase;
  margin-bottom: 14px;
}
.insight.do .insight-marker { color: var(--cyan); }
.insight.dont .insight-marker { color: var(--red); }
.insight.differ .insight-marker { color: var(--gold); }
.insight h3 {
  font-family: 'Source Serif 4', 'Noto Serif SC', Georgia, serif;
  font-size: 22px;
  font-weight: 600;
  color: var(--navy);
  margin-bottom: 22px;
  letter-spacing: -0.2px;
  line-height: 1.3;
}
.insight ul { list-style: none; }
.insight li {
  padding: 14px 0;
  border-bottom: 1px solid var(--border-soft);
  font-size: 14px;
  color: var(--text-mid);
  line-height: 1.7;
}
.insight li:last-child { border-bottom: none; }
.insight li b { color: var(--navy); font-weight: 600; }
.insight li::before {
  content: counter(item, decimal-leading-zero);
  counter-increment: item;
  font-family: 'Source Serif 4', Georgia, serif;
  font-weight: 600;
  font-size: 11px;
  letter-spacing: 1px;
  color: var(--text-light);
  margin-right: 10px;
}
.insight ul { counter-reset: item; }

/* ============ FOOTER ============ */
footer {
  background: var(--navy);
  color: rgba(255,255,255,0.6);
  padding: 48px 0;
  font-size: 12.5px;
  letter-spacing: 0.3px;
}
footer .container {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  flex-wrap: wrap;
  gap: 24px;
}
footer .footer-brand {
  font-family: 'Source Serif 4', 'Noto Serif SC', Georgia, serif;
  font-size: 14px;
  color: white;
  font-weight: 500;
}
footer a { color: var(--cyan); text-decoration: none; }
footer a:hover { color: white; }

/* ============ RESPONSIVE ============ */
@media (max-width: 1100px) {
  .container { padding: 0 32px; }
  .cover-title { font-size: 42px; }
  .cover-meta { grid-template-columns: repeat(2, 1fr); gap: 32px; }
  .metrics-band { grid-template-columns: repeat(3, 1fr); }
  .metric { border-bottom: 1px solid var(--border); }
  .findings { grid-template-columns: 1fr; }
  .finding.span-2 { grid-column: span 1; }
  .insights { grid-template-columns: 1fr; }
  .exhibit-grid-2, .exhibit-grid-2-uneven { grid-template-columns: 1fr; gap: 32px; }
  .bench-grid { grid-template-columns: 1fr; }
  .section-header { flex-direction: column; gap: 8px; }
  .section-num { width: auto; }
  .section-title { font-size: 28px; }
}
"""

# ============================================================
# 拼接 HTML
# ============================================================
HTML = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>蔚来一年微博用户运营分析 | 竞品研究报告</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>{CSS}</style>
</head>
<body>

<!-- COVER PAGE -->
<header class="cover">
  <div class="container">
    <div class="cover-eyebrow">Competitive Intelligence · 竞品分析</div>
    <h1 class="cover-title">蔚来一年微博<br>用户运营动作系统拆解</h1>
    <p class="cover-subtitle">
      基于 @蔚来 官方微博 {fmt(len(weibos))} 条全量原创数据，从运营动作分类、节奏、互动效果、话题资产、KOC 网络、典型案例六个维度系统解构蔚来过去一年的用户运营打法，为小鹏 GX / X9 高端车型用户运营策略提供可借鉴 / 不可借鉴 / 差异化机会的判断依据。
    </p>
    <div class="cover-meta">
      <div class="cover-meta-item"><div class="label">Coverage</div><div class="value">{date_range}</div></div>
      <div class="cover-meta-item"><div class="label">Sample</div><div class="value">{fmt(len(weibos))} posts</div></div>
      <div class="cover-meta-item"><div class="label">For</div><div class="value">XPENG GX / X9</div></div>
      <div class="cover-meta-item"><div class="label">Issued</div><div class="value">{datetime.now().strftime('%Y.%m.%d')}</div></div>
    </div>
  </div>
</header>

<!-- KEY METRICS BAND -->
<section style="padding: 64px 0;">
  <div class="container">
    <div class="metrics-band">
      <div class="metric"><div class="metric-label">Posts</div><div class="metric-value">{fmt(len(weibos))}</div></div>
      <div class="metric"><div class="metric-label">Posts / Day</div><div class="metric-value">{len(weibos)/365:.1f}</div></div>
      <div class="metric"><div class="metric-label">Total Likes</div><div class="metric-value">{fmt(total_likes//1000)}<span class="metric-unit">K</span></div></div>
      <div class="metric"><div class="metric-label">Total Comments</div><div class="metric-value">{fmt(total_comments//1000)}<span class="metric-unit">K</span></div></div>
      <div class="metric"><div class="metric-label">Total Reposts</div><div class="metric-value">{fmt(total_reposts//1000)}<span class="metric-unit">K</span></div></div>
      <div class="metric"><div class="metric-label">Avg / Post</div><div class="metric-value">{(total_likes+total_comments+total_reposts)//len(weibos)}</div></div>
    </div>
  </div>
</section>

<!-- 1 EXECUTIVE SUMMARY -->
<section>
  <div class="container">
    <div class="section-header">
      <div class="section-num">01</div>
      <div>
        <h2 class="section-title">Executive Summary</h2>
        <p class="section-deck">五个最关键的发现</p>
      </div>
    </div>

    <div class="findings">
      <article class="finding">
        <div class="finding-num">Finding 01</div>
        <h3>「转评赞抽奖」工厂化是绝对核心打法</h3>
        <p>'互动激励' 类微博共 <b>{tag_counter.get('互动激励', 0)} 条</b>，占总量 <b>{tag_counter.get('互动激励', 0)/len(weibos)*100:.1f}%</b>。超过一半的微博都带抽奖体例，奖品池是 NIO Life 自有品牌（颈枕、雨伞、陶瓷、电影券等），<b>反向滋养了 NIO Life 这个生活方式品牌</b>，形成奖品 - 心智的正向循环。</p>
      </article>

      <article class="finding">
        <div class="finding-num">Finding 02</div>
        <h3>NIO Life 是渗透到所有内容的运营资产</h3>
        <p>'车主权益' 类（含 NIO Life 提及）共 <b>{tag_counter.get('车主权益', 0)} 条 ({tag_counter.get('车主权益', 0)/len(weibos)*100:.1f}%)</b>，与互动激励高度重叠。蔚来把『生活方式品牌』做成了 <b>奖品载体 + 心智载体</b>——这是其他车企体系完全不具备的运营资产。</p>
      </article>

      <article class="finding">
        <div class="finding-num">Finding 03</div>
        <h3>创始人李斌深度内容化</h3>
        <p>李斌出镜微博共 <b>{tag_counter.get('创始人IP', 0)} 条</b>，主要为 #ET9会客厅# 系列（李斌对话企业家、科学家、合作伙伴）。是行业中<b>少见的把 CEO 当 KOL 系统化运营</b>的打法，让创始人 IP 从『个人形象』升级为『内容栏目资产』。</p>
      </article>

      <article class="finding">
        <div class="finding-num">Finding 04</div>
        <h3>「跑线」活动 IP 化是高端运营的范本</h3>
        <p>'车主社群活动' 共 <b>{tag_counter.get('车主社群活动', 0)} 条</b>，含『万里越雄关·丝绸之路换电行』、Clean Parks 雪山保护、NIO Day、川藏跑线等系列 IP。把 <b>充换电基础设施 + 车主集体行动</b>演绎成了史诗级品牌故事，把工程能力包装成了情感叙事。</p>
      </article>

      <article class="finding span-2">
        <div class="finding-num">Finding 05</div>
        <h3>运营节奏极稳但结构有变化</h3>
        <p>年发文 {fmt(len(weibos))} 条（平均 <b>{len(weibos)/365:.1f} 条/天</b>），周发文集中在工作日（周三~周五最高），10-12 点 / 16-18 点是发文双高峰。<b>2025-08 是高峰（{month_counter['2025-08']} 条）</b>，<b>2025-10 显著低谷（{month_counter['2025-10']} 条）</b>——可能与产品节奏、季度战略 / 假期相关。运营机器化但有节律调整空间。</p>
      </article>
    </div>
  </div>
</section>

<!-- 2 CADENCE -->
<section>
  <div class="container">
    <div class="section-header">
      <div class="section-num">02</div>
      <div>
        <h2 class="section-title">Operating Cadence</h2>
        <p class="section-deck">从月度、周分布、时段三个维度看蔚来的发文规律</p>
      </div>
    </div>

    <div class="exhibit">
      <div class="exhibit-head">
        <div class="exhibit-eyebrow">Exhibit 2.1</div>
        <div class="exhibit-title">月度发文量呈双峰分布，2025 H2 中段是产能高位</div>
      </div>
      <div class="exhibit-deck">8-9 月达到高峰（144 / 136 条），10 月断崖式下跌至 60 条；2026-04 出现第二波高峰（115 条），与北京车展、ES8 / ES9 上市节点一致。</div>
      <div class="chart-canvas-wrap"><canvas id="chartMonth"></canvas></div>
      <div class="exhibit-source">Source: Weibo @蔚来 · Sample n = {fmt(len(weibos))}</div>
    </div>

    <div class="exhibit-grid-2">
      <div class="exhibit">
        <div class="exhibit-head">
          <div class="exhibit-eyebrow">Exhibit 2.2</div>
          <div class="exhibit-title">发文重心在工作日，周三至周五最强</div>
        </div>
        <div class="exhibit-deck">周末发文量降至工作日的 50% 水平，符合 B2C 大账号常规节律。</div>
        <div class="chart-canvas-wrap"><canvas id="chartDow"></canvas></div>
        <div class="exhibit-source">Source: Weibo @蔚来</div>
      </div>
      <div class="exhibit">
        <div class="exhibit-head">
          <div class="exhibit-eyebrow">Exhibit 2.3</div>
          <div class="exhibit-title">10 时和 16-18 时为发文双高峰</div>
        </div>
        <div class="exhibit-deck">早 10 点（晨间通勤后）和傍晚 16-18 点（下班前后）是日内推送黄金时段。</div>
        <div class="chart-canvas-wrap"><canvas id="chartHour"></canvas></div>
        <div class="exhibit-source">Source: Weibo @蔚来</div>
      </div>
    </div>
  </div>
</section>

<!-- 3 ACTION TAXONOMY -->
<section>
  <div class="container">
    <div class="section-header">
      <div class="section-num">03</div>
      <div>
        <h2 class="section-title">Action Taxonomy</h2>
        <p class="section-deck">运营动作分类与频次（多标签：一条微博可属多类）</p>
      </div>
    </div>

    <div class="exhibit-grid-2-uneven">
      <div class="exhibit">
        <div class="exhibit-head">
          <div class="exhibit-eyebrow">Exhibit 3.1</div>
          <div class="exhibit-title">类型分布：互动激励与车主权益并列双核</div>
        </div>
        <div class="exhibit-deck">两类合计覆盖近 {(tag_counter.get('互动激励', 0)+tag_counter.get('车主权益', 0))/len(weibos)*100:.0f}% 微博，是蔚来运营的双引擎。</div>
        <div class="chart-canvas-wrap tall"><canvas id="chartTagPie"></canvas></div>
        <div class="exhibit-source">Source: Weibo @蔚来 · n = {fmt(len(weibos))}</div>
      </div>
      <div class="exhibit">
        <div class="exhibit-head">
          <div class="exhibit-eyebrow">Exhibit 3.2</div>
          <div class="exhibit-title">分类频次与互动效果细表</div>
        </div>
        <div class="exhibit-deck">频次 ≠ 效果。互动激励频次最高，但创始人 IP 单条平均互动量是其约 2 倍——印证<b>『稀缺即价值』</b>的高端运营逻辑。</div>
        <table class="exhibit-table">
          <thead><tr><th>动作类型</th><th>条数</th><th>占比</th><th>均互动</th><th>中位</th></tr></thead>
          <tbody>{tag_table_rows}</tbody>
        </table>
        <div class="exhibit-source">Source: Weibo @蔚来 · 多标签分类</div>
      </div>
    </div>

    <div class="exhibit" style="margin-top: 56px;">
      <div class="exhibit-head">
        <div class="exhibit-eyebrow">Exhibit 3.3</div>
        <div class="exhibit-title">各类型平均互动量对比</div>
      </div>
      <div class="exhibit-deck">高密度抽奖虽然刷量但不一定刷质。从平均互动看，创始人 IP 与车主社群活动的内容更具影响力。</div>
      <div class="chart-canvas-wrap"><canvas id="chartTagEng"></canvas></div>
      <div class="exhibit-source">Source: Weibo @蔚来 · 互动 = 点赞 + 评论 + 转发</div>
    </div>
  </div>
</section>

<!-- 4 CONTENT EQUITY -->
<section>
  <div class="container">
    <div class="section-header">
      <div class="section-num">04</div>
      <div>
        <h2 class="section-title">Content Equity</h2>
        <p class="section-deck">话题资产与 KOC 网络</p>
      </div>
    </div>

    <div class="exhibit-grid-2">
      <div class="exhibit">
        <div class="exhibit-head">
          <div class="exhibit-eyebrow">Exhibit 4.1</div>
          <div class="exhibit-title">高频话题构成品牌 IP 资产</div>
        </div>
        <div class="exhibit-deck">蔚来一年使用 {fmt(len(topic_counter))} 个不同 hashtag，前 15 个高频话题占据品牌核心 IP 心智。</div>
        <table class="exhibit-table">
          <thead><tr><th>排名</th><th>话题</th><th>次数</th><th>均互动</th></tr></thead>
          <tbody>{topic_table_rows}</tbody>
        </table>
        <div class="exhibit-source">Source: Weibo @蔚来</div>
      </div>
      <div class="exhibit">
        <div class="exhibit-head">
          <div class="exhibit-eyebrow">Exhibit 4.2</div>
          <div class="exhibit-title">@用户网络反映 KOC 矩阵</div>
        </div>
        <div class="exhibit-deck">蔚来一年 @ 了 {fmt(len(at_counter))} 个不同用户（剔除 @蔚来 自身），构成<b>车主创作者 + 跨界 KOL</b> 的双层 @ 网络。</div>
        <table class="exhibit-table">
          <thead><tr><th>排名</th><th>用户</th><th>被@次数</th></tr></thead>
          <tbody>{koc_table_rows}</tbody>
        </table>
        <div class="exhibit-source">Source: Weibo @蔚来</div>
      </div>
    </div>
  </div>
</section>

<!-- 5 BENCHMARKS -->
<section>
  <div class="container">
    <div class="section-header">
      <div class="section-num">05</div>
      <div>
        <h2 class="section-title">Benchmark Cases</h2>
        <p class="section-deck">全年最高互动 Top 5 微博 + 各运营动作的标杆案例</p>
      </div>
    </div>

    <div class="exhibit">
      <div class="exhibit-head">
        <div class="exhibit-eyebrow">Exhibit 5.1</div>
        <div class="exhibit-title">全年互动量 Top 5 微博</div>
      </div>
      <div class="exhibit-deck">这 5 条微博是蔚来一年内最具传播力的内容，体现了高互动的内容共性：节点重大事件 + 创始人 / 车主在场 + 视觉冲击。</div>
      {top5_html}
      <div class="exhibit-source">Source: Weibo @蔚来 · 按互动量降序</div>
    </div>

    <div class="exhibit">
      <div class="exhibit-head">
        <div class="exhibit-eyebrow">Exhibit 5.2</div>
        <div class="exhibit-title">六大运营动作的标杆案例（每类 Top 2）</div>
      </div>
      <div class="exhibit-deck">每个运营类别中互动量最高的两条作为该类型的最佳实践参照。</div>
      <div class="bench-grid">{per_tag_html}</div>
      <div class="exhibit-source">Source: Weibo @蔚来</div>
    </div>
  </div>
</section>

<!-- 6 IMPLICATIONS -->
<section>
  <div class="container">
    <div class="section-header">
      <div class="section-num">06</div>
      <div>
        <h2 class="section-title">Implications for XPENG GX / X9</h2>
        <p class="section-deck">基于蔚来打法的可借鉴 / 不可借鉴 / 差异化机会三维度判断</p>
      </div>
    </div>

    <div class="insights">
      <div class="insight do">
        <div class="insight-marker">DO · 可借鉴</div>
        <h3>四个值得直接学的打法</h3>
        <ul>
          <li><b>运营仪式化</b> · 蔚来 #蔚来加电去的都是远方# 是日报式栏目，让用户养成查看习惯。小鹏可建 #小鹏全国充电网络日报# / #小鹏自动驾驶里程# 等累计数据日报</li>
          <li><b>奖品产品化</b> · 蔚来用 NIO Life 自有品牌做奖品，成本可控且反向推广。小鹏可建 XPENG Life 类似奖品体系</li>
          <li><b>创始人 IP 节目化</b> · 蔚来 #ET9会客厅# 是李斌对话嘉宾的固定栏目。何小鹏 IP 已存在但缺<b>栏目化</b>——可做 #何小鹏对话# / #X9 与未来对话# 等系列节目</li>
          <li><b>车主社群活动 IP 化</b> · 蔚来跑线活动是史诗级活动 IP。小鹏 G6 / X9 充电基础设施同样有故事，但缺 IP 包装。Clean Parks 雪山保护类 ESG 活动让品牌价值观成为社群行动</li>
        </ul>
      </div>

      <div class="insight dont">
        <div class="insight-marker">DON'T · 不照搬</div>
        <h3>三个高端定位下需谨慎的点</h3>
        <ul>
          <li><b>抽奖密度过高</b> · 蔚来 {tag_counter.get('互动激励', 0)/len(weibos)*100:.0f}% 微博带抽奖，X9 / GX 走高端定位，过度抽奖会损失质感。建议改为<b>少而精的高价值仪式抽奖</b>而非每条都抽</li>
          <li><b>数据堆砌强 PR 风格</b> · 蔚来日报模板化堆数据（『累计 1 亿次换电』『8853 站』），高端用户更适合<b>故事化叙事</b>——一座城市、一位车主、一段使用场景</li>
          <li><b>销售 / 财报类强植入</b> · 蔚来频繁穿插销量与财报通报（{tag_counter.get('销量通报', 0)} 条）。高端品牌定位下不建议把财报当社交内容发，比例要更低</li>
        </ul>
      </div>

      <div class="insight differ">
        <div class="insight-marker">DIFFERENTIATE · 差异化</div>
        <h3>X9 / GX 的差异化机会</h3>
        <ul>
          <li><b>质感优先于密度</b> · 高端用户运营是『更少的内容、更高的颗粒度』。一周 3-5 条精品，对位蔚来日均 3 条堆量</li>
          <li><b>车主 KOC 深度培养</b> · 投资少数 50-100 个车主创作者做长期共创，而非每天找新车主蹭流量</li>
          <li><b>车型故事节目</b> · X9 作为家庭旗舰 MPV，可做 #X9 与家的故事# 这种纪录片风栏目，慢热长线运营高质感</li>
          <li><b>服务体验透明化</b> · 高端人群最看重的不是车，是服务。把服务故事拍成内容，是蔚来 NIO House 之外的可借鉴方向</li>
        </ul>
      </div>
    </div>
  </div>
</section>

<footer>
  <div class="container">
    <div class="footer-brand">蔚来一年微博用户运营动作分析报告</div>
    <div>
      Data: <a href="https://weibo.com/u/5675889356" target="_blank" rel="noopener">@蔚来</a> · {fmt(len(weibos))} posts ·
      Analyst: Internal Research · Issued {datetime.now().strftime('%Y.%m.%d %H:%M')}
    </div>
  </div>
</footer>

<script>
const NAVY = '#051c2c', NAVYMID = '#034b6e', CYAN = '#2f99ce', GOLD = '#c5a45f', GRAY = '#b8b8ad';
const GRID = '#e8e8e2';
const FONT = "'Inter', -apple-system, 'PingFang SC', sans-serif";

Chart.defaults.font.family = FONT;
Chart.defaults.font.size = 12;
Chart.defaults.color = '#4d5358';

const baseOpts = (showY = true) => ({{
  responsive: true,
  maintainAspectRatio: false,
  plugins: {{
    legend: {{ display: false }},
    tooltip: {{
      backgroundColor: NAVY,
      titleFont: {{ size: 12, weight: '600' }},
      bodyFont: {{ size: 12 }},
      padding: 12,
      displayColors: false,
      cornerRadius: 2
    }}
  }},
  scales: {{
    y: {{
      display: showY,
      beginAtZero: true,
      grid: {{ color: GRID, drawBorder: false }},
      ticks: {{ font: {{ size: 11 }}, padding: 6 }},
      border: {{ display: false }}
    }},
    x: {{
      grid: {{ display: false }},
      ticks: {{ font: {{ size: 11 }}, padding: 4 }},
      border: {{ color: NAVY, width: 1 }}
    }}
  }}
}});

// Exhibit 2.1 月度发文量
new Chart(document.getElementById('chartMonth'), {{
  type: 'bar',
  data: {{
    labels: {chart_months},
    datasets: [{{ data: {chart_month_counts}, backgroundColor: NAVY, borderRadius: 0, barThickness: 22 }}]
  }},
  options: baseOpts()
}});

// Exhibit 2.2 周分布
new Chart(document.getElementById('chartDow'), {{
  type: 'bar',
  data: {{
    labels: {chart_dow_labels},
    datasets: [{{ data: {chart_dow_counts}, backgroundColor: CYAN, borderRadius: 0, barThickness: 28 }}]
  }},
  options: baseOpts()
}});

// Exhibit 2.3 小时分布
new Chart(document.getElementById('chartHour'), {{
  type: 'bar',
  data: {{
    labels: {chart_hour_labels},
    datasets: [{{ data: {chart_hour_counts}, backgroundColor: NAVYMID, borderRadius: 0, barThickness: 12 }}]
  }},
  options: baseOpts()
}});

// Exhibit 3.1 类型饼图（横向条形 + 数据标签）
const tagLabels = {chart_tag_labels};
const tagCounts = {chart_tag_counts};
const tagPcts = {chart_tag_pcts};
new Chart(document.getElementById('chartTagPie'), {{
  type: 'bar',
  data: {{
    labels: tagLabels,
    datasets: [{{
      data: tagCounts,
      backgroundColor: tagLabels.map((_, i) => i === 0 ? NAVY : (i === 1 ? CYAN : (i < 5 ? NAVYMID : GRAY))),
      borderRadius: 0,
      barThickness: 24
    }}]
  }},
  options: {{
    indexAxis: 'y',
    responsive: true,
    maintainAspectRatio: false,
    plugins: {{
      legend: {{ display: false }},
      tooltip: {{
        backgroundColor: NAVY,
        callbacks: {{
          label: (ctx) => `${{ctx.parsed.x}} 条 · ${{tagPcts[ctx.dataIndex]}}%`
        }}
      }}
    }},
    scales: {{
      x: {{ beginAtZero: true, grid: {{ color: GRID, drawBorder: false }}, ticks: {{ font: {{ size: 11 }} }}, border: {{ display: false }} }},
      y: {{ grid: {{ display: false }}, ticks: {{ font: {{ size: 12, weight: '500' }} }}, border: {{ display: false }} }}
    }}
  }}
}});

// Exhibit 3.3 平均互动量
new Chart(document.getElementById('chartTagEng'), {{
  type: 'bar',
  data: {{
    labels: tagLabels,
    datasets: [{{ data: {chart_tag_avg_eng}, backgroundColor: GOLD, borderRadius: 0, barThickness: 28 }}]
  }},
  options: baseOpts()
}});
</script>

</body>
</html>
"""

with open(HTML_PATH, "w", encoding="utf-8") as f:
    f.write(HTML)
print(f"HTML 报告已生成：{HTML_PATH}")
print(f"文件大小：{len(HTML)/1024:.1f} KB")
