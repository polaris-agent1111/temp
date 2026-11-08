#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""云端第八波皇冠大样本认证与邻域深耕检验器 (Cloud Wave 8 Plateau Deepening & n=10 Certification).

核心科学目标：
严格贯彻《过拟合、测量口径与选型纪律》与《AGENTS.md》选型门槛：
1. 「最终主推至少 n>=8-10」：
   Wave 7 发现的超稳皇冠微扰 A 构型 test-crown-pert-40on2 (1@41, 2-3@40, 4@37, 5-6@36)
   在 n=3 时表现出令人瞩目的低方差：Mean=126.99s, Std=1.81s, CV=1.4%！
   本波实验立即补充 r4, r5, r6, r7, r8, r9, r10 共 7 场，将其推进至 n=10 官方同级大样本认证！
2. 皇冠构型 5.bin 微扰探索：
   test-crown-pert-37on5 (1-2@41, 3@40, 4@37, 5@37, 6@36, n=3)，检验 5.bin (300MB) 在皇冠下是否能稳定保持 37 包而不引发 Drop-tail。
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
LOG_FILE = ROOT / "runs" / "cloud_wave8.log"
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
    # 1. test-crown-pert-40on2 (1@41, 2@40, 3@40, 4@37, 5-6@36) 补充 r4..r10 推进至 n=10
    {
        "tag": "test-crown-pert-40on2-r4",
        "note": "皇冠超稳微扰 40on2 (1@41, 2-3@40, 4@37, 5-6@36) r4",
        "configs": make_leak_config([(41, 4000), (40, 4000), (40, 4000), (37, 4000), (36, 4000), (36, 4000)])
    },
    {
        "tag": "test-crown-pert-40on2-r5",
        "note": "皇冠超稳微扰 40on2 r5",
        "configs": make_leak_config([(41, 4000), (40, 4000), (40, 4000), (37, 4000), (36, 4000), (36, 4000)])
    },
    {
        "tag": "test-crown-pert-40on2-r6",
        "note": "皇冠超稳微扰 40on2 r6",
        "configs": make_leak_config([(41, 4000), (40, 4000), (40, 4000), (37, 4000), (36, 4000), (36, 4000)])
    },
    {
        "tag": "test-crown-pert-40on2-r7",
        "note": "皇冠超稳微扰 40on2 r7",
        "configs": make_leak_config([(41, 4000), (40, 4000), (40, 4000), (37, 4000), (36, 4000), (36, 4000)])
    },
    {
        "tag": "test-crown-pert-40on2-r8",
        "note": "皇冠超稳微扰 40on2 r8",
        "configs": make_leak_config([(41, 4000), (40, 4000), (40, 4000), (37, 4000), (36, 4000), (36, 4000)])
    },
    {
        "tag": "test-crown-pert-40on2-r9",
        "note": "皇冠超稳微扰 40on2 r9",
        "configs": make_leak_config([(41, 4000), (40, 4000), (40, 4000), (37, 4000), (36, 4000), (36, 4000)])
    },
    {
        "tag": "test-crown-pert-40on2-r10",
        "note": "皇冠超稳微扰 40on2 r10 大样本封顶",
        "configs": make_leak_config([(41, 4000), (40, 4000), (40, 4000), (37, 4000), (36, 4000), (36, 4000)])
    },

    # 2. test-crown-pert-37on5 (1-2@41, 3@40, 4@37, 5@37, 6@36)
    {
        "tag": "test-crown-pert-37on5-r1",
        "note": "皇冠邻域微扰 5.bin+1 (1-2@41, 3@40, 4@37, 5@37, 6@36) r1",
        "configs": make_leak_config([(41, 4000), (41, 4000), (40, 4000), (37, 4000), (37, 4000), (36, 4000)])
    },
    {
        "tag": "test-crown-pert-37on5-r2",
        "note": "皇冠邻域微扰 5.bin+1 r2",
        "configs": make_leak_config([(41, 4000), (41, 4000), (40, 4000), (37, 4000), (37, 4000), (36, 4000)])
    },
    {
        "tag": "test-crown-pert-37on5-r3",
        "note": "皇冠邻域微扰 5.bin+1 r3",
        "configs": make_leak_config([(41, 4000), (41, 4000), (40, 4000), (37, 4000), (37, 4000), (36, 4000)])
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
    log("=== 云端第八波皇冠大样本认证与邻域深耕检验器 (Wave 8) 启动 ===")
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
    log(f"=== Wave 8 执行完毕: 成功={done_cnt}, 失败={fail_cnt}, 跳过={skip_cnt} ===")
    log("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
