"""自适应逐发提交：投一发 -> 等官方出分 -> 按结果决定下一发。

用法：
  python tools/adaptive_submit.py --dry
  python tools/adaptive_submit.py --yes --start-at "2026-11-06 00:05"
  python tools/adaptive_submit.py --yes --max-slots 5

实测官方出分延迟 ~10 分钟（15:25:37 投 -> 15:35:50 已见），因此逐发自适应完全可行。
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable
BOARD = "http://47.120.64.152:5000/api/leaderboard"
TEAM = "赛博coder"
SUBS = ROOT / "runs" / "submissions.jsonl"
LOG = ROOT / "runs" / "adaptive_log.jsonl"
WAIT_MIN = 45
POLL_SEC = 90


def cfg(rate, cap, iv):
    return {"leak_rate": rate, "bucket_cap": cap, "leak_interval_us": iv}


def tag_of(c):
    return f"leak-{c['leak_rate']}-{c['bucket_cap']}-{c['leak_interval_us']}"


SLOT1 = cfg(30, 50, 5000)      # 本地最优 121.83（5ms，6000 包/s）
SLOT2 = cfg(24, 60, 4000)      # 同包速率 4ms 版 123.13 -> 两发钉死间隔维度

POOL_5MS = [cfg(30, 60, 5000), cfg(34, 50, 5000), cfg(28, 50, 5000), cfg(36, 60, 5000), cfg(30, 40, 5000)]
POOL_4MS = [cfg(28, 60, 4000), cfg(22, 60, 4000), cfg(32, 60, 4000), cfg(36, 60, 4000), cfg(24, 80, 4000)]
POOL_HIGH = [cfg(40, 60, 4000), cfg(44, 60, 4000), cfg(40, 60, 5000), cfg(36, 50, 6000)]
POOL_LOW = [cfg(20, 60, 4000), cfg(22, 50, 5000), cfg(18, 60, 4000)]
POOL_MID = [cfg(26, 60, 4000), cfg(33, 50, 5000), cfg(30, 60, 6000), cfg(26, 60, 5000)]

# 本地均值最好的配置清单（去掉首发两个），按本地均值升序：
#   30/60/5000 = 123.8(n=2) | 22/60/4000 = 124.5(n=2) | 36/60/5000 = 125.4(n=1) | 40/60/4000 = 126.75(n=1)
GOOD_LOCAL = [cfg(30, 60, 5000), cfg(22, 60, 4000), cfg(36, 60, 5000), cfg(40, 60, 4000)]


def neighbors(c):
    r, cap, iv = c["leak_rate"], c["bucket_cap"], c["leak_interval_us"]
    out = []
    for nr in (r + 3, r - 3, r + 6, r - 6):
        if 18 <= nr <= 48:
            out.append(cfg(nr, max(cap, nr), iv))
    for nv in (iv + 1000, iv - 1000):
        if 4000 <= nv <= 8000:
            out.append(cfg(r, cap, nv))
    for nc in (cap + 20, cap - 20):
        if nc >= r:
            out.append(cfg(r, nc, iv))
    return out


def _tried_high(tags):
    for t in tags:
        try:
            if int(t.split("-")[1]) >= 36:
                return True
        except Exception:
            pass
    return False


def pick_next(results, used_tags, slot_no=3):
    """返回 (config, reason)。results 为空也必须有兜底，避免 API 故障时浪费额度。"""
    if tag_of(SLOT1) not in used_tags:
        return SLOT1, "首发：本地最优配置（5ms）"
    if tag_of(SLOT2) not in used_tags:
        return SLOT2, "次发：同包速率 4ms 对照，钉死间隔维度"
    if slot_no >= 5 and not _tried_high(used_tags):
        for c in POOL_HIGH:
            if tag_of(c) not in used_tags:
                return c, "末发强制高速探针（本轮未测过 rate>=36）"
    if not results:
        for c in POOL_5MS + POOL_4MS + POOL_HIGH:
            if tag_of(c) not in used_tags:
                return c, "无出分数据（API 异常？）——按默认池继续，不浪费额度"
        return None, "候选池已空"
    best_cfg, best_s = min(results, key=lambda t: t[1])
    is5 = best_cfg["leak_interval_us"] >= 5000
    fam = POOL_5MS if is5 else POOL_4MS
    if best_s > 130.0:
        pool, why = POOL_HIGH + POOL_LOW, f"最好 {best_s:.1f}>130，假设不成立，改打高速翼+低速翼"
    elif best_s <= 128.0:
        # 已经接近目标：优先把我们本地最好的其余配置都打出去（而不是在最优点的邻域做小步挪动，
        # 因为本地最优点附近全是更差的点），打完之后才考虑邻域扰动。
        pool = GOOD_LOCAL + neighbors(best_cfg) + fam
        why = f"最好 {best_s:.1f}<=128，先把本地最好的其余配置打出去"
    else:
        pool, why = fam + GOOD_LOCAL + neighbors(best_cfg), f"最好 {best_s:.1f} 在 128-130，家族内扫 + 本地最优清单"
    for c in pool:
        if tag_of(c) not in used_tags:
            return c, why
    for c in POOL_5MS + POOL_4MS + POOL_HIGH + POOL_LOW + POOL_MID:
        if tag_of(c) not in used_tags:
            return c, "兜底池"
    return None, "候选池已空"


def log(rec):
    LOG.parent.mkdir(parents=True, exist_ok=True)
    rec = {"ts": dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), **rec}
    with LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(json.dumps(rec, ensure_ascii=False), flush=True)


def my_attempts(retries=3):
    last = None
    for _ in range(retries):
        try:
            d = requests.get(BOARD, timeout=30).json()
            for p in d["leaderboard"]["problems"]:
                for s in p.get("submissions") or []:
                    if s["team"] == TEAM:
                        return list(s.get("attempts") or [])
            return []
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(20)
    raise last


def today_count():
    if not SUBS.exists():
        return 0
    today = dt.datetime.now().astimezone().date()
    n = 0
    for line in SUBS.read_text("utf-8").splitlines():
        try:
            r = json.loads(line)
        except Exception:
            continue
        if r.get("status") == "submitted" and dt.date.fromisoformat(r["date"]) == today:
            n += 1
    return n


def submit(c):
    t0 = dt.datetime.now()
    t = tag_of(c)
    cmd1 = [PY, "harness/upload_config.py", "--tag", t, "--mode", "leak_bucket",
            "--params", f"leak_rate={c['leak_rate']}", f"bucket_cap={c['bucket_cap']}",
            f"leak_interval_us={c['leak_interval_us']}"]
    if subprocess.run(cmd1, cwd=ROOT).returncode != 0:
        log({"event": "upload_fail", "tag": t, "cfg": c})
        return False
    r = subprocess.run([PY, "client/submit_vm.py", "--yes", "--note",
                        f"ADP-{t} | 自适应逐发 {c['leak_rate']}/{c['bucket_cap']}/{c['leak_interval_us']}"], cwd=ROOT)
    ok = r.returncode == 0
    log({"event": "submit", "tag": t, "cfg": c, "ok": ok,
         "at": t0.strftime("%Y-%m-%d %H:%M:%S")})
    return ok, t0.strftime("%Y-%m-%d %H:%M:%S")


def wait_new_result(t_submit, deadline, tol_sec=180):
    """按 submitted_at 精确匹配本次提交的那条 attempt，避免把上一发的迟到成绩记到这一发。"""
    t0 = dt.datetime.strptime(t_submit, "%Y-%m-%d %H:%M:%S")
    while dt.datetime.now() < deadline:
        try:
            atts = my_attempts(retries=1)
        except Exception:
            atts = None
        if atts:
            best = None
            for a in atts:
                try:
                    ta = dt.datetime.strptime(a["submitted_at"], "%Y-%m-%d %H:%M:%S")
                except Exception:
                    continue
                gap = abs((ta - t0).total_seconds())
                if gap <= tol_sec and (best is None or gap < best[0]):
                    best = (gap, a)
            if best is not None:
                return best[1]
        time.sleep(POLL_SEC)
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--yes", action="store_true")
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--start-at", default=None)
    ap.add_argument("--max-slots", type=int, default=5)
    args = ap.parse_args()

    if args.start_at:
        target = dt.datetime.strptime(args.start_at, "%Y-%m-%d %H:%M")
        while dt.datetime.now() < target:
            left = int((target - dt.datetime.now()).total_seconds())
            if left % 600 < 31:
                print(f"[wait] 距 {args.start_at} 还有 {left}s", flush=True)
            time.sleep(min(300, max(10, left)))

    used = today_count()
    budget = min(max(0, 5 - used), args.max_slots)
    print(f"[start] 今日已用 {used}/5，本次计划 {budget} 发", flush=True)

    if args.dry:
        res, tags = [], set()
        for slot in range(1, budget + 1):
            c, why = pick_next(res, tags, slot)
            if c is None:
                break
            print(f"  slot{slot}: {tag_of(c)}  <- {why}")
            tags.add(tag_of(c))
            res.append((c, 120.0 + slot))
        return 0
    if not args.yes:
        print("[dry-run] 加 --yes 才会真的提交")
        return 0

    try:
        before = my_attempts()
    except Exception:
        before = None
        log({"event": "start_api_down"})
    results, tags = [], set()
    baseline = None if before is None else len(before)

    for slot in range(1, budget + 1):
        c, why = pick_next(results, tags, slot)
        if c is None:
            break
        t = tag_of(c)
        tags.add(t)
        print(f"\n===== slot {slot}/{budget} -> {t}  ({why}) =====", flush=True)
        log({"event": "pick", "slot": slot, "tag": t, "cfg": c, "reason": why})
        ok, t_submit = submit(c)
        if not ok:
            log({"event": "abort", "slot": slot, "reason": "submit_failed"})
            break
        deadline = dt.datetime.now() + dt.timedelta(minutes=WAIT_MIN)
        att = wait_new_result(t_submit, deadline)
        if att is None:
            log({"event": "timeout", "slot": slot, "tag": t, "submitted_at": t_submit})
            continue
        score = float(att["download_seconds"])
        results.append((c, score))
        try:
            baseline = len(my_attempts())
        except Exception:
            baseline = None
        log({"event": "scored", "slot": slot, "tag": t, "cfg": c, "score": score,
             "best_so_far": min(s for _, s in results)})

    print("\n[ALL DONE]", flush=True)
    for c, s in results:
        print(f"  {tag_of(c):22s} {s:9.3f}", flush=True)
    if results:
        bc, bs = min(results, key=lambda x: x[1])
        print(f"  本轮最好: {tag_of(bc)} = {bs:.3f}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())

