#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""非对称多梯级平滑漏桶极限科研控制器 (Asymmetric Leak Bucket Overnight Researcher).

核心背景：
- 11/07 实盘 Shot 2 (fallback-leak-fast: 1-3 leak 40/40@4k + 4-6 leak 36/36@4k) 官方斩获 124.3683s (全国第 6 名)！
- 彻底破解官方 Containernet 容器环境物理法则：大突发 (Burst>=40) 必死，平滑单包泄漏 (leak_bucket) 零丢包零排队称王！
- 本脚本接管云端算力，在云主机 Containernet 真实网络拓扑上针对非对称平滑漏桶开展深度参数网格寻优，
  重点突破 4.bin 从 36 提至 40、5.bin 从 36 提至 37~38、6.bin 在 36~37 精确控速，
  目标在明早 09:00 前将模型实测均值压进 115s~116s，为明日 5 发直夺全国第一锁定必胜构型！
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
LOG_FILE = ROOT / "runs" / "asym_leak_research.log"
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


def make_leak_config(r1: int, r2: int, r3: int, r4: int, r5: int, r6: int, interval_us: int = 4000) -> dict:
    rates = [r1, r2, r3, r4, r5, r6]
    cfg = {}
    for i, r in enumerate(rates, start=1):
        cfg[str(i)] = [
            "leak_bucket",
            {
                "leak_rate": r,
                "bucket_cap": r,
                "leak_interval_us": interval_us
            }
        ]
    return cfg


RESEARCH_QUEUE = [
    # 1. 隔离对照组：4.bin 提速至 40（1-4 全 40/40，5-6 全 36/36）
    {
        "tag": "test-leak-asym-40-all4-36-both-r1",
        "note": "1-4 leak 40/40@4k + 5-6 leak 36/36@4k (消灭4.bin让步) r1",
        "configs": make_leak_config(40, 40, 40, 40, 36, 36)
    },
    {
        "tag": "test-leak-asym-40-all4-36-both-r2",
        "note": "1-4 leak 40/40@4k + 5-6 leak 36/36@4k r2",
        "configs": make_leak_config(40, 40, 40, 40, 36, 36)
    },

    # 2. 5.bin 微提速至 37（1-4 全 40/40，5 leak 37/37，6 leak 36/36）
    {
        "tag": "test-leak-asym-40-40-37-36-r1",
        "note": "1-4 leak 40/40 + 5 leak 37/37 + 6 leak 36/36 (5.bin提速至88.8M) r1",
        "configs": make_leak_config(40, 40, 40, 40, 37, 36)
    },
    {
        "tag": "test-leak-asym-40-40-37-36-r2",
        "note": "1-4 leak 40/40 + 5 leak 37/37 + 6 leak 36/36 r2",
        "configs": make_leak_config(40, 40, 40, 40, 37, 36)
    },

    # 3. 5.bin 提速至 38（1-4 全 40/40，5 leak 38/38，6 leak 36/36）
    {
        "tag": "test-leak-asym-40-40-38-36-r1",
        "note": "1-4 leak 40/40 + 5 leak 38/38 (91.2M) + 6 leak 36/36 (86.4M) r1",
        "configs": make_leak_config(40, 40, 40, 40, 38, 36)
    },
    {
        "tag": "test-leak-asym-40-40-38-36-r2",
        "note": "1-4 leak 40/40 + 5 leak 38/38 + 6 leak 36/36 r2",
        "configs": make_leak_config(40, 40, 40, 40, 38, 36)
    },

    # 4. 前程压榨 41（1-3 leak 41/41，4 leak 40/40，5 leak 37/37，6 leak 36/36）
    {
        "tag": "test-leak-asym-41-40-37-36-r1",
        "note": "1-3 leak 41/41 (98.4M) + 4 leak 40/40 (96M) + 5 leak 37/37 + 6 leak 36/36 r1",
        "configs": make_leak_config(41, 41, 41, 40, 37, 36)
    },
    {
        "tag": "test-leak-asym-41-40-37-36-r2",
        "note": "1-3 leak 41/41 + 4 leak 40/40 + 5 leak 37/37 + 6 leak 36/36 r2",
        "configs": make_leak_config(41, 41, 41, 40, 37, 36)
    },

    # 5. 双长文件提速（1-4 全 40/40，5-6 全 37/37）
    {
        "tag": "test-leak-asym-40-40-37-37-r1",
        "note": "1-4 leak 40/40 + 5-6 leak 37/37 (双长文件88.8M) r1",
        "configs": make_leak_config(40, 40, 40, 40, 37, 37)
    },
    {
        "tag": "test-leak-asym-40-40-37-37-r2",
        "note": "1-4 leak 40/40 + 5-6 leak 37/37 r2",
        "configs": make_leak_config(40, 40, 40, 40, 37, 37)
    },

    # 6. 极致阶梯：42 -> 41 -> 40 -> 38 -> 37
    {
        "tag": "test-leak-asym-42-41-40-38-37-r1",
        "note": "1-2 leak 42 + 3-4 leak 41/40 + 5 leak 38 + 6 leak 37 (极限冲冠梯级) r1",
        "configs": make_leak_config(42, 42, 41, 40, 38, 37)
    },
    {
        "tag": "test-leak-asym-42-41-40-38-37-r2",
        "note": "1-2 leak 42 + 3-4 leak 41/40 + 5 leak 38 + 6 leak 37 r2",
        "configs": make_leak_config(42, 42, 41, 40, 38, 37)
    },
    {
        "tag": "test-leak-asym-42-41-40-38-37-r3",
        "note": "1-2 leak 42 + 3-4 leak 41/40 + 5 leak 38 + 6 leak 37 r3 (置信度复测)",
        "configs": make_leak_config(42, 42, 41, 40, 38, 37)
    },

    # 7. 稳健冠军组合：41 -> 40 -> 38 -> 36.5 (87.6M，微调4000us/36.5 -> 8000us/73)
    {
        "tag": "test-leak-asym-41-40-38-36-r1",
        "note": "1-3 leak 41/41 + 4 leak 40/40 + 5 leak 38/38 + 6 leak 36/36 r1",
        "configs": make_leak_config(41, 41, 41, 40, 38, 36)
    },
    {
        "tag": "test-leak-asym-41-40-38-36-r2",
        "note": "1-3 leak 41/41 + 4 leak 40/40 + 5 leak 38/38 + 6 leak 36/36 r2",
        "configs": make_leak_config(41, 41, 41, 40, 38, 36)
    },
    {
        "tag": "test-leak-asym-41-40-38-36-r3",
        "note": "1-3 leak 41/41 + 4 leak 40/40 + 5 leak 38/38 + 6 leak 36/36 r3",
        "configs": make_leak_config(41, 41, 41, 40, 38, 36)
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

    # 自动重新生成统计汇总
    try:
        sum_cmd = [PY, str(ROOT / "tools" / "summarize_hybrid_stats.py")]
        subprocess.run(sum_cmd, capture_output=True, text=True, check=True)
    except Exception as e:
        log(f"汇总统计更新异常: {e}")

    return p.returncode


def main() -> int:
    log("=== 非对称平滑漏桶极限科研控制器启动 ===")
    log(f"总计划实验数: {len(RESEARCH_QUEUE)} 项")

    for idx, item in enumerate(RESEARCH_QUEUE, start=1):
        tag = item["tag"]
        now = dt.datetime.now()

        # 凌晨 08:30 自动收工，预留足够时间让环境完全清空
        if now.hour == 8 and now.minute >= 30:
            log("当前时间已达 08:30，科研调度器安全收尾退出。")
            break

        if is_already_tested(tag):
            log(f"跳过已测实验 [{idx}/{len(RESEARCH_QUEUE)}]: {tag}")
            continue

        log(f"\n>>> 准备执行第 [{idx}/{len(RESEARCH_QUEUE)}] 项科研实验: {tag}")
        rc = run_experiment(item)
        if rc != 0:
            log(f"警告：实验 {tag} 返回码非零 ({rc})，休眠 10 秒后继续下一项...")
            time.sleep(10)
        else:
            time.sleep(5)

    log("=== 非对称平滑漏桶极限科研任务队列执行完毕，平稳退出 ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
