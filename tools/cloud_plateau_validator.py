#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""云端平滑漏桶平台点与真机锚点扩展校验器 (Cloud Plateau & Official Anchor Validator).

核心任务与科学目标：
1. 建立真机基准锚点（Official Ground-Truth Anchor）：
   - 将 11/07 斩获官方 124.3683s (全国第 6) 的实盘构型 (shot2: 1-3 leak 40/40@4k + 4-6 leak 36/36@4k)
     在云端 Containernet 真实网络拓扑上连跑 5 次 (r1~r5)，测出其本地基准均值与方差，锁定官方与本地的真实偏移量 Δ！
2. 扩展低方差平台点样本量 (n -> 5)：
   - 对初步表现出极佳平稳性的构型补齐至 n=5：
     - test-leak-asym-40-40-37-37 (初测 CV=0.5%) 补 r3, r4, r5
     - test-leak-asym-41-40-37-36 (初测 CV=0.1%) 补 r3, r4, r5
3. 邻域微扰与缓冲过渡阶梯验证 (Neighborhood Perturbation & Graduated Step)：
   - 验证 4.bin 从 40 降至 38/37 的防拥塞收益：
     - 40x3-38-37-36 (1-3@40, 4@38, 5@37, 6@36, n=3)
     - 40x3-37-37-36 (1-3@40, 4@37, 5@37, 6@36, n=3)
   - 官方 Shot 2 的 ±1 包邻域微扰稳定性检验：
     - 40x3-37-36-36 (4.bin +1包)
     - 39x3-36x3 (1-3.bin -1包)
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
LOG_FILE = ROOT / "runs" / "cloud_plateau_validator.log"
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
    # ==========================================
    # 1. 官方实盘 124.3683s 构型真机基线校准 (Anchor Shot 2, 5 次连测)
    # 构型: 1-3 leak 40/40@4k + 4-6 leak 36/36@4k
    # ==========================================
    {
        "tag": "test-anchor-shot2-leak-40x3-36x3-r1",
        "note": "官方124.3683s实盘构型基准对齐 (1-3@40, 4-6@36) r1",
        "configs": make_leak_config(40, 40, 40, 36, 36, 36)
    },
    {
        "tag": "test-anchor-shot2-leak-40x3-36x3-r2",
        "note": "官方124.3683s实盘构型基准对齐 r2",
        "configs": make_leak_config(40, 40, 40, 36, 36, 36)
    },
    {
        "tag": "test-anchor-shot2-leak-40x3-36x3-r3",
        "note": "官方124.3683s实盘构型基准对齐 r3",
        "configs": make_leak_config(40, 40, 40, 36, 36, 36)
    },
    {
        "tag": "test-anchor-shot2-leak-40x3-36x3-r4",
        "note": "官方124.3683s实盘构型基准对齐 r4",
        "configs": make_leak_config(40, 40, 40, 36, 36, 36)
    },
    {
        "tag": "test-anchor-shot2-leak-40x3-36x3-r5",
        "note": "官方124.3683s实盘构型基准对齐 r5",
        "configs": make_leak_config(40, 40, 40, 36, 36, 36)
    },

    # ==========================================
    # 2. 低方差平台点样本补齐至 n=5 (Plateau Expansion)
    # ==========================================
    # 40-40-37-37: 补 r3, r4, r5
    {
        "tag": "test-leak-asym-40-40-37-37-r3",
        "note": "超低方差平台点扩增 (1-4@40, 5-6@37) r3",
        "configs": make_leak_config(40, 40, 40, 40, 37, 37)
    },
    {
        "tag": "test-leak-asym-40-40-37-37-r4",
        "note": "超低方差平台点扩增 r4",
        "configs": make_leak_config(40, 40, 40, 40, 37, 37)
    },
    {
        "tag": "test-leak-asym-40-40-37-37-r5",
        "note": "超低方差平台点扩增 r5",
        "configs": make_leak_config(40, 40, 40, 40, 37, 37)
    },

    # 41-40-37-36: 补 r3, r4, r5
    {
        "tag": "test-leak-asym-41-40-37-36-r3",
        "note": "前程41平稳点扩增 (1-3@41, 4@40, 5@37, 6@36) r3",
        "configs": make_leak_config(41, 41, 41, 40, 37, 36)
    },
    {
        "tag": "test-leak-asym-41-40-37-36-r4",
        "note": "前程41平稳点扩增 r4",
        "configs": make_leak_config(41, 41, 41, 40, 37, 36)
    },
    {
        "tag": "test-leak-asym-41-40-37-36-r5",
        "note": "前程41平稳点扩增 r5",
        "configs": make_leak_config(41, 41, 41, 40, 37, 36)
    },

    # ==========================================
    # 3. 4.bin 降速过渡阶梯验证 (防拥塞平滑阶梯)
    # ==========================================
    # 40x3-38-37-36: 1-3@40, 4@38, 5@37, 6@36 (n=3)
    {
        "tag": "test-leak-asym-40x3-38-37-36-r1",
        "note": "过渡平滑阶梯 (1-3@40, 4@38, 5@37, 6@36) r1",
        "configs": make_leak_config(40, 40, 40, 38, 37, 36)
    },
    {
        "tag": "test-leak-asym-40x3-38-37-36-r2",
        "note": "过渡平滑阶梯 r2",
        "configs": make_leak_config(40, 40, 40, 38, 37, 36)
    },
    {
        "tag": "test-leak-asym-40x3-38-37-36-r3",
        "note": "过渡平滑阶梯 r3",
        "configs": make_leak_config(40, 40, 40, 38, 37, 36)
    },

    # 40x3-37-37-36: 1-3@40, 4@37, 5@37, 6@36 (n=3)
    {
        "tag": "test-leak-asym-40x3-37-37-36-r1",
        "note": "深度平稳阶梯 (1-3@40, 4@37, 5@37, 6@36) r1",
        "configs": make_leak_config(40, 40, 40, 37, 37, 36)
    },
    {
        "tag": "test-leak-asym-40x3-37-37-36-r2",
        "note": "深度平稳阶梯 r2",
        "configs": make_leak_config(40, 40, 40, 37, 37, 36)
    },
    {
        "tag": "test-leak-asym-40x3-37-37-36-r3",
        "note": "深度平稳阶梯 r3",
        "configs": make_leak_config(40, 40, 40, 37, 37, 36)
    },

    # ==========================================
    # 4. 官方实盘 Shot 2 的 ±1 包邻域稳定性扰动验证
    # ==========================================
    # 4.bin +1 包微扰: 40x3-37-36-36 (1-3@40, 4@37, 5-6@36)
    {
        "tag": "test-anchor-shot2-pert-40x3-37-36-36-r1",
        "note": "Shot 2 邻域微扰验证 (4.bin从36升至37) r1",
        "configs": make_leak_config(40, 40, 40, 37, 36, 36)
    },
    {
        "tag": "test-anchor-shot2-pert-40x3-37-36-36-r2",
        "note": "Shot 2 邻域微扰验证 (4.bin从36升至37) r2",
        "configs": make_leak_config(40, 40, 40, 37, 36, 36)
    },

    # 1-3.bin -1 包保守微扰: 39x3-36x3 (1-3@39, 4-6@36)
    {
        "tag": "test-anchor-shot2-pert-39x3-36x3-r1",
        "note": "Shot 2 邻域微扰验证 (1-3.bin从40降至39) r1",
        "configs": make_leak_config(39, 39, 39, 36, 36, 36)
    },
    {
        "tag": "test-anchor-shot2-pert-39x3-36x3-r2",
        "note": "Shot 2 邻域微扰验证 (1-3.bin从40降至39) r2",
        "configs": make_leak_config(39, 39, 39, 36, 36, 36)
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
    log("=== 云端平滑漏桶平台点与真机锚点扩展校验器启动 ===")
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

    log("=== 所有实验队列执行完毕，平稳退出 ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
