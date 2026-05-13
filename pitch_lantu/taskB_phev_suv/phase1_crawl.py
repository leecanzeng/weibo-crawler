"""
Phase 1 - 任务 B：中大型 SUV PHEV 比稿数据抓取

抓取组合 (5 轮):
  岚图汽车/泰山        uid=7351024207  (与任务A 同账号, 数据将合并到同 JSON)
  AITO汽车/M8         uid=7711487956
  理想汽车/L8          uid=6001272153
  小鹏汽车/GX          uid=5710264970
  极氪Zeekr/8X        uid=7576049404

蔚来/ES8 跳过 (复用已有 5675889356.json 数据)
"""
import json
import json5
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

# 脚本位于 pitch_lantu/taskB_phev_suv/，项目根在上两级
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
CONFIG_PATH = os.path.join(REPO_ROOT, "config.json")
BACKUP_PATH = os.path.join(SCRIPT_DIR, "config.backup.json")

COMBOS = [
    {"uid": "7351024207", "query": "泰山", "label": "岚图_泰山"},
    {"uid": "7711487956", "query": "M8",   "label": "AITO_M8"},
    {"uid": "6001272153", "query": "L8",   "label": "理想_L8"},
    {"uid": "5710264970", "query": "GX",   "label": "小鹏_GX"},
    {"uid": "7576049404", "query": "8X",   "label": "极氪_8X"},
]

SINCE = "2025-11-12"
END = "2026-05-12"


def load_config():
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return json5.loads(f.read())


def write_config(cfg):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


def main():
    if not os.path.isfile(BACKUP_PATH):
        shutil.copy2(CONFIG_PATH, BACKUP_PATH)
        print(f"备份原 config.json -> {BACKUP_PATH}")

    base = load_config()
    base["since_date"] = SINCE
    base["end_date"] = END
    base["only_crawl_original"] = 1
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
            print(f"短暂休息 30 秒...")
            time.sleep(30)

    if os.path.isfile(BACKUP_PATH):
        shutil.copy2(BACKUP_PATH, CONFIG_PATH)
        print(f"\n已恢复原 config.json")

    total_elapsed = time.time() - overall_start
    print(f"\n{'='*70}")
    print(f"Phase 1 任务B 完成,总耗时 {int(total_elapsed//60)} 分 {int(total_elapsed%60)} 秒")
    print(f"{'='*70}")
    for s in summary:
        flag = "OK" if s["ok"] else "FAIL"
        print(f"  [{flag}] {s['label']:<15}  uid={s['uid']:<12}  query={s['query']:<6}  {s['elapsed_sec']}s")

    summary_path = os.path.join(SCRIPT_DIR, "phase1_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump({
            "task": "B - 中大型SUV PHEV 比稿",
            "window": {"start": SINCE, "end": END},
            "combos": summary,
            "total_elapsed_sec": int(total_elapsed),
            "finished_at": datetime.now().isoformat(),
        }, f, ensure_ascii=False, indent=2)
    print(f"\n汇总写入 {summary_path}")


if __name__ == "__main__":
    main()
