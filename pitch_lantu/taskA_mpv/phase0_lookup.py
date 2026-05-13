"""
Phase 0 - 5 个 MPV 比稿品牌：
  1) 搜索官方蓝 V 账号，输出 uid
  2) 在每个账号下做关键词命中预查，估算半年内（2025-11-12 ~ 2026-05-12）条数

输出: phase0_result.json
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

# Windows 默认 cp936，强制 UTF-8 输出，避免 emoji / 生僻字编码错误
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

# 脚本位于 pitch_lantu/taskA_mpv/，项目根在上两级
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
    if "=" not in item:
        continue
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

# 预热
print("预热 session ...", flush=True)
session.get("https://m.weibo.cn", timeout=10)
time.sleep(2)

SEARCH_URL = "https://m.weibo.cn/api/container/getIndex"

WINDOW_START = datetime(2025, 11, 12)
WINDOW_END = datetime(2026, 5, 12, 23, 59, 59)


def parse_created_at(s):
    """微博 m API 的 created_at 形如 'Sat Jan 25 19:51:50 +0800 2026' 或近期相对时间。"""
    if not s:
        return None
    try:
        return datetime.strptime(s, "%a %b %d %H:%M:%S +0800 %Y")
    except Exception:
        pass
    # 相对时间："今天 19:51"、"昨天"、"X 分钟前" → 视为最近，落在窗口内
    if "分钟前" in s or "小时前" in s or "今天" in s or "昨天" in s:
        return datetime.now()
    # YYYY-MM-DD HH:MM
    try:
        return datetime.strptime(s, "%Y-%m-%d %H:%M")
    except Exception:
        pass
    # MM-DD HH:MM (当年)
    m = re.match(r"^(\d{1,2})-(\d{1,2})", s)
    if m:
        try:
            return datetime(datetime.now().year, int(m.group(1)), int(m.group(2)))
        except Exception:
            return None
    return None


def search_users(keyword, top_n=5):
    params = {
        "containerid": f"100103type=3&q={quote(keyword)}",
        "page_type": "searchall",
    }
    r = session.get(SEARCH_URL, params=params, timeout=15)
    js = r.json()
    if not js.get("ok"):
        return []
    cards = js.get("data", {}).get("cards", [])
    users = []
    for card in cards:
        # 蓝 V 个人 / 机构通常在 card_type=11 + card_group
        grp = card.get("card_group") or []
        for sub in grp:
            if sub.get("card_type") == 10 and "user" in sub:
                users.append(sub["user"])
        # 也直接采纳顶层 user
        if card.get("card_type") == 10 and "user" in card:
            users.append(card["user"])
    # 去重
    seen = set()
    uniq = []
    for u in users:
        if u["id"] in seen:
            continue
        seen.add(u["id"])
        uniq.append(u)
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
    """从搜索结果中提取微博 list"""
    if not js.get("ok"):
        return []
    cards = js.get("data", {}).get("cards", [])
    out = []
    for c in cards:
        grp = c.get("card_group") or []
        for sub in grp:
            mb = sub.get("mblog")
            if mb:
                out.append(mb)
        # 直接挂在 card 上
        mb = c.get("mblog")
        if mb:
            out.append(mb)
    return out


# 候选品牌名 → 关键词列表
CANDIDATES = [
    ("岚图汽车", ["梦想家"]),
    ("腾势汽车", ["D9"]),
    ("别克", ["GL8"]),
    ("魏牌", ["高山"]),
    ("智界汽车", ["V9"]),
]


print("=" * 70)
print("Phase 0.1 - 搜索官方账号")
print("=" * 70)

brand_account = {}
all_search_dump = {}
for brand, _queries in CANDIDATES:
    print(f"\n[{brand}] 搜索 Top 5：")
    users = search_users(brand, top_n=8)
    all_search_dump[brand] = users
    if not users:
        print("  未找到")
        continue
    for u in users[:8]:
        verified = "蓝V" if u.get("verified") else "  "
        vt = u.get("verified_type", "")
        vt_ext = u.get("verified_type_ext", "")
        followers = u.get("followers_count", 0)
        desc = (u.get("description") or u.get("verified_reason") or "").replace("\n", " ")[:40]
        print(f"  {verified} uid={u['id']:>12}  @{u['screen_name']:<22}  粉{followers:>10}  vt={vt}/{vt_ext}  {desc}")
    # 取第一个蓝 V (verified=True 且 verified_type 非 -1)
    blue_v = [u for u in users if u.get("verified") and u.get("verified_type", -1) != -1]
    if blue_v:
        brand_account[brand] = blue_v[0]
        print(f"  → 选定: @{blue_v[0]['screen_name']} (uid={blue_v[0]['id']})")
    else:
        # 退路：取粉丝最多的
        users.sort(key=lambda x: -(x.get("followers_count", 0)))
        brand_account[brand] = users[0]
        print(f"  → 选定(粉丝最高): @{users[0]['screen_name']} (uid={users[0]['id']})")
    time.sleep(random.uniform(3, 5))


print("\n\n" + "=" * 70)
print("Phase 0.2 - 关键词命中预查 (取前 3 页 ≈ 30 条样本)")
print("=" * 70)

hit_summary = {}
for brand, queries in CANDIDATES:
    if brand not in brand_account:
        continue
    acc = brand_account[brand]
    uid = acc["id"]
    for q in queries:
        key = f"{brand}/{q}"
        print(f"\n[{key}] uid={uid} @{acc['screen_name']}")
        total = 0
        in_window = 0
        sample_dates = []
        for page in range(1, 4):
            try:
                js = search_in_user(uid, q, page=page)
            except Exception as e:
                print(f"  page {page} 请求失败: {e}")
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
                            "comments": mb.get("comments_count", 0),
                            "reposts": mb.get("reposts_count", 0),
                        })
            time.sleep(random.uniform(2, 4))
        print(f"  样本 {total} 条，半年内 {in_window} 条")
        for s in sample_dates:
            print(f"    [{s['date']}] 👍{s['likes']} 💬{s['comments']} 🔁{s['reposts']}  {s['text']}")
        hit_summary[key] = {
            "uid": uid,
            "screen_name": acc["screen_name"],
            "query": q,
            "sample_total": total,
            "in_window": in_window,
            "sample_dates": sample_dates,
        }
        time.sleep(random.uniform(4, 7))


# 最终汇总
print("\n\n" + "=" * 70)
print("Phase 0 汇总 - user_id 表")
print("=" * 70)
for brand, acc in brand_account.items():
    fc = acc.get("followers_count", 0)
    print(f"  {brand:<10}  uid={str(acc['id']):<14}  @{acc['screen_name']:<22} 粉 {fc}")

result = {
    "generated_at": datetime.now().isoformat(),
    "window": {"start": WINDOW_START.isoformat(), "end": WINDOW_END.isoformat()},
    "brand_accounts": {
        b: {
            "uid": str(acc["id"]),
            "screen_name": acc["screen_name"],
            "followers": acc.get("followers_count", 0),
            "verified_reason": acc.get("verified_reason", ""),
        }
        for b, acc in brand_account.items()
    },
    "hit_summary": hit_summary,
}
result_path = os.path.join(SCRIPT_DIR, "phase0_result.json")
with open(result_path, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)
print(f"\n→ 写入 {result_path}")
