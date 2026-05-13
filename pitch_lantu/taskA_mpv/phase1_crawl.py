"""
Phase 1 - 任务 A：MPV 比稿 5 车型微博数据抓取

工作流：
  对每个 (uid, query)：
    1. 备份原 config.json
    2. 覆写 config.json：单 user_id + 单 query + 半年窗口
    3. 调用 python weibo.py
    4. 跑完恢复 config.json

数据落地: weibo_data/<screen_name>/<uid>.json + 按月归档 markdown
"""
import json
import json5
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime

# Windows UTF-8 输出
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

# 脚本位于 pitch_lantu/taskA_mpv/，项目根在上两级
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
CONFIG_PATH = os.path.join(REPO_ROOT, "config.json")
BACKUP_PATH = os.path.join(SCRIPT_DIR, "config.backup.json")

# 抓取组合 (智界V9 已在 smoke test 中完成，本 driver 跑剩余 4 个)
COMBOS = [
    {"uid": "7351024207", "query": "梦想家", "label": "岚图_梦想家"},
    {"uid": "2664689831", "query": "D9",     "label": "腾势_D9"},
    {"uid": "1667553532", "query": "GL8",    "label": "别克_GL8"},
    {"uid": "6055831093", "query": "高山",    "label": "魏牌_高山"},
]

SINCE = "2025-11-12"
END = "2026-05-12"


def load_config():
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return json5.loads(f.read())


def write_config(cfg):
    """写 config.json (不保留注释)"""
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


def main():
    # 备份原 config
    if not os.path.isfile(BACKUP_PATH):
        shutil.copy2(CONFIG_PATH, BACKUP_PATH)
        print(f"备份原 config.json -> {BACKUP_PATH}")

    base = load_config()
    # 共用字段
    base["since_date"] = SINCE
    base["end_date"] = END
    base["only_crawl_original"] = 1     # 只爬原创(营销分析够用)
    base["original_pic_download"] = 0
    base["retweet_pic_download"] = 0
    base["original_video_download"] = 0
    base["retweet_video_download"] = 0
    base["download_comment"] = 0
    base["download_repost"] = 0
    base["write_mode"] = ["json", "csv", "markdown"]
    base["markdown_split_by"] = "day_by_month"

    overall_start = time.time()
    summary = []

    for i, c in enumerate(COMBOS, 1):
        print(f"\n{'='*70}")
        print(f"[{i}/{len(COMBOS)}] {c['label']}  uid={c['uid']}  query=\"{c['query']}\"")
        print(f"{'='*70}\n", flush=True)

        cfg = dict(base)
        cfg["user_id_list"] = [c["uid"]]
        cfg["query_list"] = [c["query"]]
        write_config(cfg)

        t0 = time.time()
        try:
            subprocess.run(
                [sys.executable, "weibo.py"],
                cwd=REPO_ROOT,
                check=False,
                env={**os.environ, "PYTHONIOENCODING": "utf-8"},
            )
            ok = True
        except Exception as e:
            print(f"ERROR: {e}")
            ok = False
        elapsed = time.time() - t0
        summary.append({
            "label": c["label"], "uid": c["uid"], "query": c["query"],
            "ok": ok, "elapsed_sec": int(elapsed),
        })
        print(f"\n→ [{c['label']}] 用时 {int(elapsed)} 秒\n")

        if i < len(COMBOS):
            print(f"短暂休息 30 秒避免连续请求...")
            time.sleep(30)

    # 恢复原 config
    if os.path.isfile(BACKUP_PATH):
        shutil.copy2(BACKUP_PATH, CONFIG_PATH)
        print(f"\n已恢复原 config.json")

    total_elapsed = time.time() - overall_start
    print(f"\n{'='*70}")
    print(f"Phase 1 全部完成,总耗时 {int(total_elapsed//60)} 分 {int(total_elapsed%60)} 秒")
    print(f"{'='*70}")
    for s in summary:
        flag = "OK" if s["ok"] else "FAIL"
        print(f"  [{flag}] {s['label']:<15}  uid={s['uid']:<12}  query={s['query']:<6}  {s['elapsed_sec']}s")

    # 落 summary
    summary_path = os.path.join(SCRIPT_DIR, "phase1_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump({
            "task": "A - MPV 比稿",
            "window": {"start": SINCE, "end": END},
            "combos": summary,
            "total_elapsed_sec": int(total_elapsed),
            "finished_at": datetime.now().isoformat(),
        }, f, ensure_ascii=False, indent=2)
    print(f"\n汇总写入 {summary_path}")


if __name__ == "__main__":
    main()
