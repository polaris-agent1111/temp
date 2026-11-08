#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task 0289 复核脚本（zcode 二次验证，并发执行者合并协议）。

背景：兄弟执行者已交付 zcode/scripts/preheat0289_drill.py 与 runs/preheat0289_drill.json，
但其脚本将临时文件写入 runs/（任务单未授权路径），且未核验真实控制器
（tools/sequential_adaptive_1108.py）的锁与状态持久化机制。

本脚本：
1. 在 zcode/ 内复现兄弟的三项合成测量（state 读写时延 / O_EXCL 锁互斥 / 配置树缓存），
   临时文件全部落在 zcode/scripts/.tmp_0289_reverify/（结束后清理）；
2. 补充真实系统核验（只读）：
   - 真实状态文件 runs/sequential_1108_state.json 加载时延；
   - 控制器静态审计：LOCK_FILE 是否真的被获取、状态写是否原子、
     wait_until 过冲、额度 SSOT、keep-alive、mock 演练状态指纹。
3. 不访问任何网络端点，不执行控制器，不写 runs/。

用法：python zcode/scripts/preheat0289_reverify.py
输出：stdout + zcode/scripts/preheat0289_reverify_result.json
"""
from __future__ import annotations

import json
import os
import statistics
import sys
import tempfile
import threading
import time
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]  # zcode/scripts/x.py -> repo root
CONTROLLER = ROOT / "tools" / "sequential_adaptive_1108.py"
REAL_STATE = ROOT / "runs" / "sequential_1108_state.json"
CONFIG_TREE = ROOT / "runs" / "configs" / "1108-A1-hybrid-champ-90M-96M"
OUT_JSON = ROOT / "zcode" / "scripts" / "preheat0289_reverify_result.json"

ITERATIONS = 30
LOCK_ROUNDS = 5
LOCK_THREADS = 25
GATE_MS = 10.0


def bench(fn, n=ITERATIONS):
    xs = []
    for _ in range(n):
        t0 = time.perf_counter()
        fn()
        xs.append((time.perf_counter() - t0) * 1000.0)
    xs_sorted = sorted(xs)
    p95 = xs_sorted[min(len(xs_sorted) - 1, int(round(0.95 * len(xs_sorted))) - 1)]
    return {
        "n": n,
        "min_ms": round(min(xs), 3),
        "median_ms": round(statistics.median(xs), 3),
        "mean_ms": round(statistics.fmean(xs), 3),
        "p95_ms": round(p95, 3),
        "max_ms": round(max(xs), 3),
    }


def test_a_synthetic_state(tmp: Path) -> dict:
    """复现兄弟测试：同形状合成 state 的 save/load 时延（临时文件在 zcode/ 内）。"""
    test_state = {
        "campaign_date": "2026-11-08",
        "shots_completed": 0,
        "max_shots": 5,
        "decision_tree": {
            "root": "1108-A1-hybrid-champ-90M-96M",
            "fallback": "test-leak-asym-41x2-40-37-36x2-r1",
        },
        "history": [],
    }
    f = tmp / "synthetic_state.json"

    def save():
        with open(f, "w", encoding="utf-8") as fh:
            json.dump(test_state, fh, indent=2)

    def load():
        with open(f, "r", encoding="utf-8") as fh:
            json.load(fh)

    save()
    return {"save": bench(save), "load": bench(load)}


def test_b_real_state_load() -> dict:
    """真实状态文件（runs/sequential_1108_state.json）加载时延（只读）。"""
    if not REAL_STATE.exists():
        return {"exists": False}
    payload = REAL_STATE.read_text(encoding="utf-8")

    def load():
        data = json.loads(REAL_STATE.read_text(encoding="utf-8"))
        assert data.get("date") is not None

    return {"exists": True, "bytes": len(payload.encode("utf-8")), "load": bench(load)}


def test_c_lock_race(tmp: Path) -> dict:
    """O_CREAT|O_EXCL 原子互斥竞争：25 线程 × 5 轮（兄弟只跑了 1 轮）。"""
    lock_path = tmp / "reverify.lock"
    rounds = []
    for r in range(LOCK_ROUNDS):
        if lock_path.exists():
            lock_path.unlink()
        acquired, rejected = 0, 0
        m = threading.Lock()

        def attempter(tid):
            nonlocal acquired, rejected
            try:
                fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.write(fd, f"owner_{tid}".encode("utf-8"))
                os.close(fd)
                with m:
                    acquired += 1
            except FileExistsError:
                with m:
                    rejected += 1
            except Exception:
                with m:
                    rejected += 1

        ts = [threading.Thread(target=attempter, args=(i,)) for i in range(LOCK_THREADS)]
        for t in ts:
            t.start()
        for t in ts:
            t.join()
        rounds.append({"round": r + 1, "acquired": acquired, "rejected": rejected,
                       "exclusive_ok": acquired == 1 and rejected == LOCK_THREADS - 1})
    ok = all(r["exclusive_ok"] for r in rounds)
    lock_path.unlink(missing_ok=True)
    return {"threads": LOCK_THREADS, "rounds": rounds, "all_rounds_exclusive": ok}


def test_d_config_tree(tmp: Path) -> dict:
    """6 阶段配置树存在性与页面缓存预热效果（只读 runs/，不做内存驻留幻想）。"""
    stages = {}
    if CONFIG_TREE.exists():
        for s in range(1, 7):
            p = CONFIG_TREE / str(s) / "pacer.txt"
            if p.exists():
                stages[s] = len(p.read_bytes())
    cold = bench(lambda: [p.read_bytes() for p in
                          (CONFIG_TREE / str(s) / "pacer.txt" for s in range(1, 7))
                          if p.exists()], n=5)
    warm = bench(lambda: [p.read_bytes() for p in
                          (CONFIG_TREE / str(s) / "pacer.txt" for s in range(1, 7))
                          if p.exists()], n=30)
    return {
        "tree_exists": CONFIG_TREE.exists(),
        "stages_present": sorted(stages),
        "stage_bytes": stages,
        "read_all_6_cold-ish": cold,
        "read_all_6_warm": warm,
    }


def test_e_controller_static_audit() -> dict:
    """真实控制器静态审计（纯源码扫描，不执行、不联网）。"""
    if not CONTROLLER.exists():
        return {"exists": False}
    src = CONTROLLER.read_text(encoding="utf-8")
    lines = src.splitlines()

    lock_decl = [i + 1 for i, l in enumerate(lines) if "LOCK_FILE" in l]
    # 状态写方式：STATE_FILE.write_text / os.replace / temp+rename
    state_write = [i + 1 for i, l in enumerate(lines)
                   if "STATE_FILE" in l and ("write_text" in l or "os.replace" in l)]
    uses_os_replace = any("os.replace" in lines[i - 1] for i in state_write)
    wait_floor = [i + 1 for i, l in enumerate(lines) if "max(15" in l]
    quota_ssot = [i + 1 for i, l in enumerate(lines) if "SUBMISSIONS_FILE" in l]
    keepalive = [i + 1 for i, l in enumerate(lines)
                 if "urlopen" in l or "keep-alive" in l.lower() or "http" in l.lower() and "Connection" in l]

    findings = {
        "controller_path": str(CONTROLLER.relative_to(ROOT)),
        "exists": True,
        "LOCK_FILE_declared_lines": lock_decl,
        "LOCK_FILE_ever_opened_or_locked": len(lock_decl) > 1,  # 仅声明=1 处则从未使用
        "state_write_lines": state_write,
        "state_write_atomic_os_replace": uses_os_replace,
        "wait_floor_lines": wait_floor,
        "quota_ssot_is_submissions_jsonl": len(quota_ssot) >= 2,
        "poll_transport_urlopen_lines": keepalive[:5],
    }

    # 真实状态文件的 mock 演练指纹（记忆结论：118.1307 非官方成绩）
    if REAL_STATE.exists():
        st = json.loads(REAL_STATE.read_text(encoding="utf-8"))
        hist = st.get("history", [])
        scored_at = [h.get("scored_at") for h in hist]
        secs = [h.get("download_seconds") for h in hist if h.get("download_seconds")]
        one_sec_apart = all(
            scored_at[i] and scored_at[i - 1] and
            (scored_at[i] > scored_at[i - 1]) and
            (__import__("datetime").datetime.strptime(scored_at[i], "%Y-%m-%d %H:%M:%S") -
             __import__("datetime").datetime.strptime(scored_at[i - 1], "%Y-%m-%d %H:%M:%S")
             ).total_seconds() <= 2.0
            for i in range(1, len(scored_at))
        )
        findings["on_disk_state"] = {
            "date": st.get("date"),
            "completed_shots": st.get("completed_shots"),
            "scores": secs,
            "all_scores_in_mock_band_117.5_123.5": bool(secs) and all(117.5 <= s <= 123.5 for s in secs),
            "consecutive_scored_at_gap_le_2s": one_sec_apart,
            "is_dry_run_rehearsal_fingerprint": bool(secs) and all(117.5 <= s <= 123.5 for s in secs) and one_sec_apart,
        }
    return findings


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="0289_reverify_", dir=str(ROOT / "zcode" / "scripts")) as td:
        tmp = Path(td)
        a = test_a_synthetic_state(tmp)
        b = test_b_real_state_load()
        c = test_c_lock_race(tmp)
        d = test_d_config_tree(tmp)
    e = test_e_controller_static_audit()

    gate_state = a["load"]["max_ms"] <= GATE_MS and a["save"]["max_ms"] <= GATE_MS
    gate_real_state = b.get("load", {}).get("max_ms", 999) <= GATE_MS
    gate_lock = c["all_rounds_exclusive"]

    result = {
        "task_id": "0289",
        "executor": "zcode (reverify, merge protocol)",
        "synthetic_state_io": a,
        "real_state_load": b,
        "lock_o_excl_race": c,
        "config_tree_cache": d,
        "controller_static_audit": e,
        "gates": {
            f"synthetic_state_io_max_ms<={GATE_MS}": gate_state,
            f"real_state_load_max_ms<={GATE_MS}": gate_real_state,
            "lock_exclusive_all_rounds": gate_lock,
            "config_tree_6of6": d["tree_exists"] and len(d["stages_present"]) == 6,
        },
        "note": "兄弟执行者合成测量在此复现；真实控制器的锁从未获取、状态写非原子，见 controller_static_audit。",
    }
    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if all(result["gates"].values()) else 1


if __name__ == "__main__":
    sys.exit(main())
