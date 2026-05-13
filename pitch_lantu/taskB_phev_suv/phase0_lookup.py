"""
Phase 0 - 任务 B 中大型 SUV PHEV 比稿
  搜索 4 个新品牌官方蓝 V 账号 + 关键词命中预查
  (岚图账号已知=7351024207 用 query="泰山", 蔚来账号已知=5675889356 用 query="ES8")

输出: phase0_result.json (在脚本同目录)
"""
import json
import os
import random
import re
import sys
import time
from datetime import datetime
from urllib.parse import quote

import requests

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

# 脚本位于 pitch_lantu/taskB_phev_suv/，项目根在上两级
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))


def load_env_local():
    env_path = os.path.join(REPO_ROOT, ".env.local")
    if not os.path.isfile(env_path):
        return
    with open(env_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


load_env_local()
COOKIE = os.environ.get("WEIBO_COOKIE", "")
if not COOKIE:
    print("ERROR: WEIBO_COOKIE 未设置")
    raise SystemExit(1)

cookies = {}
for item in COOKIE.split(";"):
    if "=" not in item: continue
    k, _, v = item.strip().partition("=")
    cookies[k.strip()] = v.strip()

session = requests.Session()
session.cookies.update(cookies)
session.headers.update({
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://m.weibo.cn/",
    "MWeibo-Pwa": "1",
    "X-Requested-With": "XMLHttpRequest",
})

print("预热 session ...", flush=True)
session.get("https://m.weibo.cn", timeout=10)
time.sleep(2)

SEARCH_URL = "https://m.weibo.cn/api/container/getIndex"
WINDOW_START = datetime(2025, 11, 12)
WINDOW_END = datetime(2026, 5, 12, 23, 59, 59)


def parse_created_at(s):
    if not s: return None
    try:
        return datetime.strptime(s, "%a %b %d %H:%M:%S +0800 %Y")
    except Exception: pass
    if "分钟前" in s or "小时前" in s or "今天" in s or "昨天" in s:
        return datetime.now()
    try:
        return datetime.strptime(s, "%Y-%m-%d %H:%M")
    except Exception: pass
    m = re.match(r"^(\d{1,2})-(\d{1,2})", s)
    if m:
        try:
            return datetime(datetime.now().year, int(m.group(1)), int(m.group(2)))
        except Exception: return None
    return None


def search_users(keyword, top_n=8):
    params = {
        "containerid": f"100103type=3&q={quote(keyword)}",
        "page_type": "searchall",
    }
    r = session.get(SEARCH_URL, params=params, timeout=15)
    js = r.json()
    if not js.get("ok"): return []
    cards = js.get("data", {}).get("cards", [])
    users = []
    for card in cards:
        for sub in (card.get("card_group") or []):
            if sub.get("card_type") == 10 and "user" in sub:
                users.append(sub["user"])
        if card.get("card_type") == 10 and "user" in card:
            users.append(card["user"])
    seen = set(); uniq = []
    for u in users:
        if u["id"] in seen: continue
        seen.add(u["id"]); uniq.append(u)
    return uniq[:top_n]


def search_in_user(uid, query, page=1):
    params = {
        "container_ext": f"profile_uid:{uid}",
        "containerid": f"100103type=401&q={quote(query)}",
        "page_type": "searchall",
        "page": page,
    }
    r = session.get(SEARCH_URL, params=params, timeout=15)
    return r.json()


def extract_mblogs(js):
    if not js.get("ok"): return []
    out = []
    for c in js.get("data", {}).get("cards", []):
        for sub in (c.get("card_group") or []):
            mb = sub.get("mblog")
            if mb: out.append(mb)
        mb = c.get("mblog")
        if mb: out.append(mb)
    return out


# 4 个新品牌 + 1 个已知岚图账号 + 1 个已知蔚来账号
# 每个 entry: (品牌搜索词, 关键词, 已知 uid 或 None)
CANDIDATES = [
    {"brand": "岚图汽车",   "uid": "7351024207",  "queries": ["泰山"]},          # 已知 (任务A)
    {"brand": "AITO汽车",  "uid": None,           "queries": ["M8"]},            # 待搜
    {"brand": "理想汽车",   "uid": None,           "queries": ["L8"]},            # 待搜
    {"brand": "小鹏汽车",   "uid": None,           "queries": ["GX"]},            # 待搜 (新车)
    {"brand": "ZEEKR极氪", "uid": None,           "queries": ["8X"]},            # 待搜
    {"brand": "蔚来",       "uid": "5675889356",  "queries": ["ES8"]},          # 已知 (本地切片)
]


print("=" * 70)
print("Phase 0.1 - 任务B 搜索官方账号 (仅未知 uid 的品牌)")
print("=" * 70)

brand_account = {}
for c in CANDIDATES:
    brand = c["brand"]
    if c["uid"]:
        brand_account[brand] = {"id": c["uid"], "screen_name": brand, "_skipped_search": True}
        print(f"\n[{brand}] 跳过搜索 (已知 uid={c['uid']})")
        continue
    print(f"\n[{brand}] 搜索 Top 8：")
    users = search_users(brand, top_n=8)
    if not users:
        print("  未找到")
        continue
    for u in users[:8]:
        verified = "蓝V" if u.get("verified") else "  "
        vt = u.get("verified_type", "")
        vt_ext = u.get("verified_type_ext", "")
        fc = u.get("followers_count", 0)
        desc = (u.get("description") or u.get("verified_reason") or "").replace("\n", " ")[:50]
        print(f"  {verified} uid={u['id']:>12}  @{u['screen_name']:<24}  粉 {fc}  vt={vt}/{vt_ext}  {desc}")
    blue_v = [u for u in users if u.get("verified") and u.get("verified_type", -1) != -1]
    chosen = blue_v[0] if blue_v else users[0]
    brand_account[brand] = chosen
    print(f"  → 选定: @{chosen['screen_name']} (uid={chosen['id']})")
    time.sleep(random.uniform(3, 5))


print("\n\n" + "=" * 70)
print("Phase 0.2 - 关键词命中预查")
print("=" * 70)

hit_summary = {}
for c in CANDIDATES:
    brand = c["brand"]
    if brand not in brand_account:
        print(f"\n[{brand}] 账号未定位，跳过")
        continue
    acc = brand_account[brand]
    uid = acc["id"] if isinstance(acc, dict) and "id" in acc else acc.get("id")
    for q in c["queries"]:
        key = f"{brand}/{q}"
        print(f"\n[{key}] uid={uid}")
        total, in_window = 0, 0
        sample_dates = []
        for page in range(1, 4):
            try:
                js = search_in_user(uid, q, page=page)
            except Exception as e:
                print(f"  page {page} 失败: {e}")
                break
            if not js.get("ok"):
                print(f"  page {page}: API not ok")
                break
            mbs = extract_mblogs(js)
            if not mbs:
                print(f"  page {page}: 空")
                break
            for mb in mbs:
                total += 1
                dt = parse_created_at(mb.get("created_at", ""))
                if dt and WINDOW_START <= dt <= WINDOW_END:
                    in_window += 1
                    if len(sample_dates) < 3:
                        text = (mb.get("raw_text") or mb.get("text") or "")
                        text = re.sub(r"<[^>]+>", "", text).replace("\n", " ")[:80]
                        sample_dates.append({
                            "date": dt.strftime("%Y-%m-%d"),
                            "text": text,
                            "likes": mb.get("attitudes_count", 0),
                        })
            time.sleep(random.uniform(2, 4))
        print(f"  样本 {total} 条，半年内 {in_window} 条")
        for s in sample_dates:
            print(f"    [{s['date']}] 👍{s['likes']}  {s['text']}")
        hit_summary[key] = {
            "uid": str(uid),
            "query": q,
            "sample_total": total,
            "in_window": in_window,
            "sample_dates": sample_dates,
        }
        time.sleep(random.uniform(4, 6))


print("\n\n" + "=" * 70)
print("Phase 0 任务B 汇总")
print("=" * 70)
for brand, acc in brand_account.items():
    if isinstance(acc, dict):
        uid_s = str(acc.get("id", "?"))
        sn = acc.get("screen_name", brand)
        fc = acc.get("followers_count", "?")
        print(f"  {brand:<12}  uid={uid_s:<14}  @{sn:<24} 粉 {fc}")

result = {
    "generated_at": datetime.now().isoformat(),
    "window": {"start": WINDOW_START.isoformat(), "end": WINDOW_END.isoformat()},
    "brand_accounts": {
        b: {
            "uid": str(acc.get("id", "")),
            "screen_name": acc.get("screen_name", b),
            "followers": acc.get("followers_count", ""),
        }
        for b, acc in brand_account.items() if isinstance(acc, dict)
    },
    "hit_summary": hit_summary,
}
result_path = os.path.join(SCRIPT_DIR, "phase0_result.json")
with open(result_path, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)
print(f"\n→ 写入 {result_path}")
