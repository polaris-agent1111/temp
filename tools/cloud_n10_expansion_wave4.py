#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""云端第四波大样本收敛与微步精调验证器 (Cloud Expansion Wave 4).

核心科学目标：
1. 将最优微扰构型 test-anchor-shot2-pert-40x3-37-36-36 冲刺至 n=10 终极门槛 (补跑 r7 ~ r10)；
2. 将全库方差最低 (CV 2.7%) 的防守平台点 test-leak-asym-40-40-37-37 扩增至 n=8 (补跑 r6 ~ r8)；
3. 验证 5.bin 半步精调 (37.5 pkts/4ms -> rate=75, cap=75, interval=8000us) 的防拥塞增益；
4. 验证 Shot 2 前程双包微提速构型 (1-2@41, 3-4@40, 5-6@36) 的均值下移能力。
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
LOG_FILE = ROOT / "runs" / "cloud_wave4.log"
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
    # rates: list of (rate, interval_us)
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
    # 1. 扩充 40x3-37-36-36 至 n=10 (补 r7 ~ r10)
    {
        "tag": "test-anchor-shot2-pert-40x3-37-36-36-r7",
        "note": "Shot 2 微扰 +1 冲刺 n=10 (1-3@40, 4@37, 5-6@36) r7",
        "configs": make_leak_config([(40, 4000), (40, 4000), (40, 4000), (37, 4000), (36, 4000), (36, 4000)])
    },
    {
        "tag": "test-anchor-shot2-pert-40x3-37-36-36-r8",
        "note": "Shot 2 微扰 +1 冲刺 n=10 r8",
        "configs": make_leak_config([(40, 4000), (40, 4000), (40, 4000), (37, 4000), (36, 4000), (36, 4000)])
    },
    {
        "tag": "test-anchor-shot2-pert-40x3-37-36-36-r9",
        "note": "Shot 2 微扰 +1 冲刺 n=10 r9",
        "configs": make_leak_config([(40, 4000), (40, 4000), (40, 4000), (37, 4000), (36, 4000), (36, 4000)])
    },
    {
        "tag": "test-anchor-shot2-pert-40x3-37-36-36-r10",
        "note": "Shot 2 微扰 +1 冲刺 n=10 r10",
        "configs": make_leak_config([(40, 4000), (40, 4000), (40, 4000), (37, 4000), (36, 4000), (36, 4000)])
    },

    # 2. 扩充超平稳平台点 40-40-37-37 至 n=8 (补 r6 ~ r8)
    {
        "tag": "test-leak-asym-40-40-37-37-r6",
        "note": "超低方差平台点扩增至 n=8 (1-4@40, 5-6@37) r6",
        "configs": make_leak_config([(40, 4000), (40, 4000), (40, 4000), (40, 4000), (37, 4000), (37, 4000)])
    },
    {
        "tag": "test-leak-asym-40-40-37-37-r7",
        "note": "超低方差平台点扩增至 n=8 r7",
        "configs": make_leak_config([(40, 4000), (40, 4000), (40, 4000), (40, 4000), (37, 4000), (37, 4000)])
    },
    {
        "tag": "test-leak-asym-40-40-37-37-r8",
        "note": "超低方差平台点扩增至 n=8 r8",
        "configs": make_leak_config([(40, 4000), (40, 4000), (40, 4000), (40, 4000), (37, 4000), (37, 4000)])
    },

    # 3. 5.bin 半步精调 (37.5 pkts/4ms -> 75 pkts/8ms)
    {
        "tag": "test-leak-asym-40x3-37-37p5-36-r1",
        "note": "5.bin 半步精调测试 (1-3@40, 4@37, 5@75/8ms, 6@36) r1",
        "configs": make_leak_config([(40, 4000), (40, 4000), (40, 4000), (37, 4000), (75, 8000), (36, 4000)])
    },
    {
        "tag": "test-leak-asym-40x3-37-37p5-36-r2",
        "note": "5.bin 半步精调测试 r2",
        "configs": make_leak_config([(40, 4000), (40, 4000), (40, 4000), (37, 4000), (75, 8000), (36, 4000)])
    },
    {
        "tag": "test-leak-asym-40x3-37-37p5-36-r3",
        "note": "5.bin 半步精调测试 r3",
        "configs": make_leak_config([(40, 4000), (40, 4000), (40, 4000), (37, 4000), (75, 8000), (36, 4000)])
    },

    # 4. Shot 2 前程双包微提速 (1-2@41, 3-4@40, 5-6@36)
    {
        "tag": "test-leak-asym-41x2-40x2-36x2-r1",
        "note": "Shot 2 前程微加速测试 (1-2@41, 3-4@40, 5-6@36) r1",
        "configs": make_leak_config([(41, 4000), (41, 4000), (40, 4000), (40, 4000), (36, 4000), (36, 4000)])
    },
    {
        "tag": "test-leak-asym-41x2-40x2-36x2-r2",
        "note": "Shot 2 前程微加速测试 r2",
        "configs": make_leak_config([(41, 4000), (41, 4000), (40, 4000), (40, 4000), (36, 4000), (36, 4000)])
    },
    {
        "tag": "test-leak-asym-41x2-40x2-36x2-r3",
        "note": "Shot 2 前程微加速测试 r3",
        "configs": make_leak_config([(41, 4000), (41, 4000), (40, 4000), (40, 4000), (36, 4000), (36, 4000)])
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
    log("=== 云端第四波大样本收敛与微步精调验证器启动 ===")
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

    log("=== 第四波实验队列执行完毕，平稳退出 ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
