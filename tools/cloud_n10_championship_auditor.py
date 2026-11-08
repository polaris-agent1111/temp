#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""云端冲冠构型 n=10 深度审计与收敛校验器 (Cloud Championship n=10 Auditor).

核心目标：
严格落实《过拟合、测量口径与选型纪律》主推门槛：
- 主推阶段必须满足 n >= 8~10！
- 消除单场极值偏见，以稳健均值、标准差与 95% 置信区间锁定明日冲冠第 1 主力。

实验阵列 (共 16 项):
1. 主推候选 test-leak-asym-41-40-37-36 补齐至 n=10:
   - 补跑 r6, r7, r8, r9, r10 (共 5 轮)
2. 稳健微扰构型 test-anchor-shot2-pert-40x3-37-36-36 扩充至 n=6:
   - 初测均值 127.25s (比基准快 7.28s)，补跑 r3, r4, r5, r6 (共 4 轮)
3. 交叉融合构型 test-leak-asym-41-40-37-37 (前程41 + 稳健双37):
   - 测试 r1, r2, r3, r4 (共 4 轮)
4. 极限探索构型 test-leak-asym-40x3-38-37-36 补测方差:
   - 初测出现 109.47s 极值但 std=17s，补跑 r4, r5, r6 (共 3 轮)
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
LOG_FILE = ROOT / "runs" / "cloud_n10_auditor.log"
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
    # 1. 主推候选 41-40-37-36 冲刺 n=10 (补 r6 ~ r10)
    {
        "tag": "test-leak-asym-41-40-37-36-r6",
        "note": "冲冠主推 n=10 扩充 (1-3@41, 4@40, 5@37, 6@36) r6",
        "configs": make_leak_config(41, 41, 41, 40, 37, 36)
    },
    {
        "tag": "test-leak-asym-41-40-37-36-r7",
        "note": "冲冠主推 n=10 扩充 r7",
        "configs": make_leak_config(41, 41, 41, 40, 37, 36)
    },
    {
        "tag": "test-leak-asym-41-40-37-36-r8",
        "note": "冲冠主推 n=10 扩充 r8",
        "configs": make_leak_config(41, 41, 41, 40, 37, 36)
    },
    {
        "tag": "test-leak-asym-41-40-37-36-r9",
        "note": "冲冠主推 n=10 扩充 r9",
        "configs": make_leak_config(41, 41, 41, 40, 37, 36)
    },
    {
        "tag": "test-leak-asym-41-40-37-36-r10",
        "note": "冲冠主推 n=10 扩充 r10",
        "configs": make_leak_config(41, 41, 41, 40, 37, 36)
    },

    # 2. 稳健微扰构型 40x3-37-36-36 扩充至 n=6 (补 r3 ~ r6)
    {
        "tag": "test-anchor-shot2-pert-40x3-37-36-36-r3",
        "note": "Shot 2 微扰 +1 样本扩增 (1-3@40, 4@37, 5-6@36) r3",
        "configs": make_leak_config(40, 40, 40, 37, 36, 36)
    },
    {
        "tag": "test-anchor-shot2-pert-40x3-37-36-36-r4",
        "note": "Shot 2 微扰 +1 样本扩增 r4",
        "configs": make_leak_config(40, 40, 40, 37, 36, 36)
    },
    {
        "tag": "test-anchor-shot2-pert-40x3-37-36-36-r5",
        "note": "Shot 2 微扰 +1 样本扩增 r5",
        "configs": make_leak_config(40, 40, 40, 37, 36, 36)
    },
    {
        "tag": "test-anchor-shot2-pert-40x3-37-36-36-r6",
        "note": "Shot 2 微扰 +1 样本扩增 r6",
        "configs": make_leak_config(40, 40, 40, 37, 36, 36)
    },

    # 3. 交叉融合构型 41-40-37-37 (前程41 + 稳健双37) r1 ~ r4
    {
        "tag": "test-leak-asym-41-40-37-37-r1",
        "note": "交叉融合测试 (1-3@41, 4@40, 5-6@37) r1",
        "configs": make_leak_config(41, 41, 41, 40, 37, 37)
    },
    {
        "tag": "test-leak-asym-41-40-37-37-r2",
        "note": "交叉融合测试 r2",
        "configs": make_leak_config(41, 41, 41, 40, 37, 37)
    },
    {
        "tag": "test-leak-asym-41-40-37-37-r3",
        "note": "交叉融合测试 r3",
        "configs": make_leak_config(41, 41, 41, 40, 37, 37)
    },
    {
        "tag": "test-leak-asym-41-40-37-37-r4",
        "note": "交叉融合测试 r4",
        "configs": make_leak_config(41, 41, 41, 40, 37, 37)
    },

    # 4. 极限探索 40x3-38-37-36 补测方差 (补 r4 ~ r6)
    {
        "tag": "test-leak-asym-40x3-38-37-36-r4",
        "note": "过渡平滑阶梯方差校验 (1-3@40, 4@38, 5@37, 6@36) r4",
        "configs": make_leak_config(40, 40, 40, 38, 37, 36)
    },
    {
        "tag": "test-leak-asym-40x3-38-37-36-r5",
        "note": "过渡平滑阶梯方差校验 r5",
        "configs": make_leak_config(40, 40, 40, 38, 37, 36)
    },
    {
        "tag": "test-leak-asym-40x3-38-37-36-r6",
        "note": "过渡平滑阶梯方差校验 r6",
        "configs": make_leak_config(40, 40, 40, 38, 37, 36)
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
    log("=== 云端冲冠构型 n=10 深度审计与收敛校验器启动 ===")
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

    log("=== 所有冲冠验证队列执行完毕，平稳退出 ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
