#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""云端第十波主力梯队 n=15/n=10 终极大样本认证强化器 (Cloud Wave 10 Dual Super-Certification).

核心科学目标：
严格贯彻《过拟合、测量口径与选型纪律》关于大样本认证与置信区间的最高要求：
1. 稳健主力 test-anchor-shot2-pert-40x3-37-36-36 (1-3@40, 4@37, 5-6@36)
   目前已达成 n=10（均值 132.64s，中位数 133.47s，方差降 38.7%，上界严控 145s）。
   本波继续压测 r11..r15 共 5 场，将其推进至与皇冠原点同级的 n=15 超大样本黄金认证！
2. 防守堡垒 test-leak-asym-40-40-37-37 (1-4@40, 5-6@37)
   目前处于 n=8（CV 仅 3.6%，标准差 4.90s）。
   本波补充 r9、r10 两场，将其推进至 n=10 满额大样本认证，构筑官方复测最坚实的防波堤！
"""
from __future__ import annotations

import datetime as dt
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable
LOG_FILE = ROOT / "runs" / "cloud_wave10.log"
RESULTS_FILE = ROOT / "runs" / "results.jsonl"

try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def log(msg: str):
    now_str = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"[{now_str}] {msg}"
    try:
        print(formatted, flush=True)
    except Exception:
        try:
            print(formatted.encode("ascii", errors="replace").decode("ascii"), flush=True)
        except Exception:
            pass
    try:
        with open(LOG_FILE, "a", encoding="utf-8", errors="replace") as f:
            f.write(formatted + "\n")
    except Exception:
        pass


def make_leak_config(rates: list[tuple[int, int]]) -> dict:
    cfg = {}
    for i, (r, interval) in enumerate(rates, start=1):
        cfg[str(i)] = [
            "leak_bucket",
            {
                "leak_rate": r,
                "bucket_cap": r,
                "leak_interval_us": interval
            }
        ]
    return cfg


RESEARCH_QUEUE = [
    # 1. 稳健主力 40x3-37-36-36 扩充至 n=15
    {
        "tag": "test-anchor-shot2-pert-40x3-37-36-36-r11",
        "note": "稳健主力 (1-3@40, 4@37, 5-6@36) r11",
        "configs": make_leak_config([(40, 4000), (40, 4000), (40, 4000), (37, 4000), (36, 4000), (36, 4000)])
    },
    {
        "tag": "test-anchor-shot2-pert-40x3-37-36-36-r12",
        "note": "稳健主力 r12",
        "configs": make_leak_config([(40, 4000), (40, 4000), (40, 4000), (37, 4000), (36, 4000), (36, 4000)])
    },
    {
        "tag": "test-anchor-shot2-pert-40x3-37-36-36-r13",
        "note": "稳健主力 r13",
        "configs": make_leak_config([(40, 4000), (40, 4000), (40, 4000), (37, 4000), (36, 4000), (36, 4000)])
    },
    {
        "tag": "test-anchor-shot2-pert-40x3-37-36-36-r14",
        "note": "稳健主力 r14",
        "configs": make_leak_config([(40, 4000), (40, 4000), (40, 4000), (37, 4000), (36, 4000), (36, 4000)])
    },
    {
        "tag": "test-anchor-shot2-pert-40x3-37-36-36-r15",
        "note": "稳健主力 r15 达成 n=15 终极大样本认证",
        "configs": make_leak_config([(40, 4000), (40, 4000), (40, 4000), (37, 4000), (36, 4000), (36, 4000)])
    },

    # 2. 防守堡垒 40-40-37-37 扩充至 n=10 满额认证
    {
        "tag": "test-leak-asym-40-40-37-37-r9",
        "note": "防守堡垒 (1-4@40, 5-6@37) r9",
        "configs": make_leak_config([(40, 4000), (40, 4000), (40, 4000), (40, 4000), (37, 4000), (37, 4000)])
    },
    {
        "tag": "test-leak-asym-40-40-37-37-r10",
        "note": "防守堡垒 r10 达成 n=10 满额认证",
        "configs": make_leak_config([(40, 4000), (40, 4000), (40, 4000), (40, 4000), (37, 4000), (37, 4000)])
    }
]


def is_already_tested(tag: str) -> bool:
    if not RESULTS_FILE.exists():
        return False
    with open(RESULTS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                d = json.loads(line)
                if d.get("tag") == tag:
                    return True
            except Exception:
                pass
    return False


def run_experiment(item: dict) -> int:
    tag = item["tag"]
    note = item["note"]
    configs = item["configs"]

    tmp_configs_file = ROOT / "runs" / f"{tag}.configs.json"
    with open(tmp_configs_file, "w", encoding="utf-8") as f:
        json.dump(configs, f, indent=2)

    cmd = [
        PY,
        str(ROOT / "harness" / "run_experiment.py"),
        "--tag", tag,
        "--configs-file", str(tmp_configs_file),
        "--note", note,
        "--timeout", "360",
        "--poll", "15"
    ]

    log(f"启动实验: {tag} | {note}")
    start_t = time.time()
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")

    for line in iter(p.stdout.readline, ""):
        line_s = line.strip()
        if line_s:
            if any(k in line_s for k in ["[start]", "[poll]", "[result]", "[WARN]", "[ERR]", "ERROR", "Exception"]):
                log(f"  {line_s}")

    p.wait()
    dur = time.time() - start_t
    log(f"实验结束: {tag} (Exit Code {p.returncode}, 耗时 {dur:.1f}s)")

    try:
        tmp_configs_file.unlink(missing_ok=True)
    except Exception:
        pass

    try:
        sum_cmd = [PY, str(ROOT / "tools" / "summarize_hybrid_stats.py")]
        subprocess.run(sum_cmd, capture_output=True, text=True)
    except Exception:
        pass

    return p.returncode


def main() -> int:
    log("=" * 70)
    log("=== 云端第十波主力梯队 n=15/n=10 终极大样本认证强化器 (Wave 10) 启动 ===")
    log(f"总计划队列实验数: {len(RESEARCH_QUEUE)} 场")
    log("=" * 70)

    done_cnt = 0
    fail_cnt = 0
    skip_cnt = 0

    for idx, item in enumerate(RESEARCH_QUEUE, start=1):
        tag = item["tag"]
        log(f"\n--- [{idx}/{len(RESEARCH_QUEUE)}] 准备运行: {tag} ---")

        if is_already_tested(tag):
            log(f"跳过已存在实验: {tag}")
            skip_cnt += 1
            continue

        rc = run_experiment(item)
        if rc == 0:
            done_cnt += 1
        else:
            fail_cnt += 1
            log(f"[WARN] 实验 {tag} 返回非零 exit code: {rc}")

        time.sleep(10)

    log("\n" + "=" * 70)
    log(f"=== Wave 10 执行完毕: 成功={done_cnt}, 失败={fail_cnt}, 跳过={skip_cnt} ===")
    log("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
