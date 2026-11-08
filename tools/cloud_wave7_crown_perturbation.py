#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""云端第七波皇冠构型 ±1 包邻域微扰稳定性检验器 (Cloud Crown Perturbation Wave 7).

核心科学目标：
严格贯彻《过拟合、测量口径与选型纪律》选型门槛：
- 要求邻域稳定：对皇冠构型关键参数做 ±1 包微扰，性能不应显著变差，证明坐落在平坦的「平台点」，而非孤立的「尖点」！

微扰实验设计 (共 9 项):
1. 3.bin -1 包微扰 (3.bin 40 -> 39):
   - test-crown-pert-39on3 (1-2@41, 3@39, 4@37, 5-6@36, n=3)
2. 4.bin +1 包微扰 (4.bin 37 -> 38):
   - test-crown-pert-38on4 (1-2@41, 3@40, 4@38, 5-6@36, n=3)
3. 2.bin -1 包微扰 (2.bin 41 -> 40):
   - test-crown-pert-40on2 (1@41, 2@40, 3@40, 4@37, 5-6@36, n=3)
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
LOG_FILE = ROOT / "runs" / "cloud_wave7.log"
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
    # 1. 3.bin -1 包微扰: 1-2@41, 3@39, 4@37, 5-6@36
    {
        "tag": "test-crown-pert-39on3-r1",
        "note": "皇冠邻域微扰 3.bin-1 (1-2@41, 3@39, 4@37, 5-6@36) r1",
        "configs": make_leak_config([(41, 4000), (41, 4000), (39, 4000), (37, 4000), (36, 4000), (36, 4000)])
    },
    {
        "tag": "test-crown-pert-39on3-r2",
        "note": "皇冠邻域微扰 3.bin-1 r2",
        "configs": make_leak_config([(41, 4000), (41, 4000), (39, 4000), (37, 4000), (36, 4000), (36, 4000)])
    },
    {
        "tag": "test-crown-pert-39on3-r3",
        "note": "皇冠邻域微扰 3.bin-1 r3",
        "configs": make_leak_config([(41, 4000), (41, 4000), (39, 4000), (37, 4000), (36, 4000), (36, 4000)])
    },

    # 2. 4.bin +1 包微扰: 1-2@41, 3@40, 4@38, 5-6@36
    {
        "tag": "test-crown-pert-38on4-r1",
        "note": "皇冠邻域微扰 4.bin+1 (1-2@41, 3@40, 4@38, 5-6@36) r1",
        "configs": make_leak_config([(41, 4000), (41, 4000), (40, 4000), (38, 4000), (36, 4000), (36, 4000)])
    },
    {
        "tag": "test-crown-pert-38on4-r2",
        "note": "皇冠邻域微扰 4.bin+1 r2",
        "configs": make_leak_config([(41, 4000), (41, 4000), (40, 4000), (38, 4000), (36, 4000), (36, 4000)])
    },
    {
        "tag": "test-crown-pert-38on4-r3",
        "note": "皇冠邻域微扰 4.bin+1 r3",
        "configs": make_leak_config([(41, 4000), (41, 4000), (40, 4000), (38, 4000), (36, 4000), (36, 4000)])
    },

    # 3. 2.bin -1 包微扰: 1@41, 2@40, 3@40, 4@37, 5-6@36
    {
        "tag": "test-crown-pert-40on2-r1",
        "note": "皇冠邻域微扰 2.bin-1 (1@41, 2@40, 3@40, 4@37, 5-6@36) r1",
        "configs": make_leak_config([(41, 4000), (40, 4000), (40, 4000), (37, 4000), (36, 4000), (36, 4000)])
    },
    {
        "tag": "test-crown-pert-40on2-r2",
        "note": "皇冠邻域微扰 2.bin-1 r2",
        "configs": make_leak_config([(41, 4000), (40, 4000), (40, 4000), (37, 4000), (36, 4000), (36, 4000)])
    },
    {
        "tag": "test-crown-pert-40on2-r3",
        "note": "皇冠邻域微扰 2.bin-1 r3",
        "configs": make_leak_config([(41, 4000), (40, 4000), (40, 4000), (37, 4000), (36, 4000), (36, 4000)])
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
        subprocess.run(sum_cmd, capture_output=True, text=True, check=True)
    except Exception as e:
        log(f"汇总统计更新异常: {e}")

    return p.returncode


def main() -> int:
    log("=== 云端第七波皇冠构型 ±1 包邻域微扰稳定性检验器启动 ===")
    log(f"总计划实验数: {len(RESEARCH_QUEUE)} 项")

    for idx, item in enumerate(RESEARCH_QUEUE, start=1):
        tag = item["tag"]
        now = dt.datetime.now()

        if now.hour == 8 and now.minute >= 45:
            log("当前时间已达 08:45，实验调度器安全收尾退出。")
            break

        if is_already_tested(tag):
            log(f"跳过已测实验 [{idx}/{len(RESEARCH_QUEUE)}]: {tag}")
            continue

        log(f"\n>>> 准备执行第 [{idx}/{len(RESEARCH_QUEUE)}] 项实验: {tag}")
        rc = run_experiment(item)
        if rc != 0:
            log(f"警告：实验 {tag} 返回码非零 ({rc})，休眠 10 秒后继续下一项...")
            time.sleep(10)
        else:
            time.sleep(5)

    log("=== 第七波实验队列执行完毕，平稳退出 ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
