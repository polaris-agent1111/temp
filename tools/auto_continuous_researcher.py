#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""自动不间断科研评测控制器 (Auto Continuous Researcher).

核心目标：
- 绝不闲置云主机计算资源！
- 持续在云主机 Containernet 真实网络拓扑上自动串行执行高价值物理实验；
- 自动化探索非对称突发、微粒度时钟、中间速率网格、多轮方差收敛；
- 自动更新统计总览，并在 23:45 准时平稳收工，为 00:05 官方打榜守护进程留出完全干净的环境。
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
LOG_FILE = ROOT / "runs" / "continuous_research.log"
RESULTS_FILE = ROOT / "runs" / "results.jsonl"

# 高价值科研实验矩阵（按优先级排列）
RESEARCH_QUEUE = [
    # 1. 终极融合构型：fast14 (r40/r38) + 非对称突发 (40/60) + precise 5(100M) 6(96M)
    {
        "tag": "test-hybrid-tb4-fast14-asym40-60-champ-r1",
        "note": "fast14 tb 1-3(40/60/r40) 4(40/60/r38) + precise 5(100M) 6(96M) r1",
        "configs": {
            "1": ["token_bucket", {"tokens": 40, "burst": 60, "token_refill_rate": 40, "token_refill_interval_us": 4000, "enable_n_in_flight": 1}],
            "2": ["token_bucket", {"tokens": 40, "burst": 60, "token_refill_rate": 40, "token_refill_interval_us": 4000, "enable_n_in_flight": 1}],
            "3": ["token_bucket", {"tokens": 40, "burst": 60, "token_refill_rate": 40, "token_refill_interval_us": 4000, "enable_n_in_flight": 1}],
            "4": ["token_bucket", {"tokens": 40, "burst": 60, "token_refill_rate": 38, "token_refill_interval_us": 4000, "enable_n_in_flight": 1}],
            "5": ["precise_rate_based", {"max_pacing_rate": 12500000, "clock_granularity": 1000, "enable_n_in_flight": 1}],
            "6": ["precise_rate_based", {"max_pacing_rate": 12000000, "clock_granularity": 1000, "enable_n_in_flight": 1}]
        }
    },
    # 2. 非对称突发 (40/60) + 98M 超稳组合
    {
        "tag": "test-hybrid-tb4-asym40-60-p98M-champ-r1",
        "note": "asym tb 40/60 on 1-4 + precise 5(98M) 6(96M)",
        "configs": {
            "1": ["token_bucket", {"tokens": 40, "burst": 60, "token_refill_rate": 40, "token_refill_interval_us": 4000, "enable_n_in_flight": 1}],
            "2": ["token_bucket", {"tokens": 40, "burst": 60, "token_refill_rate": 40, "token_refill_interval_us": 4000, "enable_n_in_flight": 1}],
            "3": ["token_bucket", {"tokens": 40, "burst": 60, "token_refill_rate": 40, "token_refill_interval_us": 4000, "enable_n_in_flight": 1}],
            "4": ["token_bucket", {"tokens": 40, "burst": 60, "token_refill_rate": 38, "token_refill_interval_us": 4000, "enable_n_in_flight": 1}],
            "5": ["precise_rate_based", {"max_pacing_rate": 12250000, "clock_granularity": 1000, "enable_n_in_flight": 1}],
            "6": ["precise_rate_based", {"max_pacing_rate": 12000000, "clock_granularity": 1000, "enable_n_in_flight": 1}]
        }
    },
    # 3. 突发边界物理探索：tokens=40, burst=70 (测试是否击穿 40-pkt 队列)
    {
        "tag": "test-hybrid-tb4-asym40-70-champ-r1",
        "note": "asym tb 40/70 on 1-4 + precise 5(100M) 6(96M) burst-boundary test",
        "configs": {
            "1": ["token_bucket", {"tokens": 40, "burst": 70, "token_refill_rate": 40, "token_refill_interval_us": 4000, "enable_n_in_flight": 1}],
            "2": ["token_bucket", {"tokens": 40, "burst": 70, "token_refill_rate": 40, "token_refill_interval_us": 4000, "enable_n_in_flight": 1}],
            "3": ["token_bucket", {"tokens": 40, "burst": 70, "token_refill_rate": 40, "token_refill_interval_us": 4000, "enable_n_in_flight": 1}],
            "4": ["token_bucket", {"tokens": 40, "burst": 70, "token_refill_rate": 38, "token_refill_interval_us": 4000, "enable_n_in_flight": 1}],
            "5": ["precise_rate_based", {"max_pacing_rate": 12500000, "clock_granularity": 1000, "enable_n_in_flight": 1}],
            "6": ["precise_rate_based", {"max_pacing_rate": 12000000, "clock_granularity": 1000, "enable_n_in_flight": 1}]
        }
    },
    # 4. 微调时钟粒度 950µs
    {
        "tag": "test-hybrid-tb4-p100M-p96M-g950-r1",
        "note": "tb 1-4 + precise 5(100M/g950) 6(96M/g950)",
        "configs": {
            "1": ["token_bucket", {"tokens": 40, "burst": 40, "token_refill_rate": 40, "token_refill_interval_us": 4000, "enable_n_in_flight": 1}],
            "2": ["token_bucket", {"tokens": 40, "burst": 40, "token_refill_rate": 40, "token_refill_interval_us": 4000, "enable_n_in_flight": 1}],
            "3": ["token_bucket", {"tokens": 40, "burst": 40, "token_refill_rate": 38, "token_refill_interval_us": 4000, "enable_n_in_flight": 1}],
            "4": ["token_bucket", {"tokens": 40, "burst": 40, "token_refill_rate": 36, "token_refill_interval_us": 4000, "enable_n_in_flight": 1}],
            "5": ["precise_rate_based", {"max_pacing_rate": 12500000, "clock_granularity": 950, "enable_n_in_flight": 1}],
            "6": ["precise_rate_based", {"max_pacing_rate": 12000000, "clock_granularity": 950, "enable_n_in_flight": 1}]
        }
    },
    # 5. 微调时钟粒度 1050µs
    {
        "tag": "test-hybrid-tb4-p100M-p96M-g1050-r1",
        "note": "tb 1-4 + precise 5(100M/g1050) 6(96M/g1050)",
        "configs": {
            "1": ["token_bucket", {"tokens": 40, "burst": 40, "token_refill_rate": 40, "token_refill_interval_us": 4000, "enable_n_in_flight": 1}],
            "2": ["token_bucket", {"tokens": 40, "burst": 40, "token_refill_rate": 40, "token_refill_interval_us": 4000, "enable_n_in_flight": 1}],
            "3": ["token_bucket", {"tokens": 40, "burst": 40, "token_refill_rate": 38, "token_refill_interval_us": 4000, "enable_n_in_flight": 1}],
            "4": ["token_bucket", {"tokens": 40, "burst": 40, "token_refill_rate": 36, "token_refill_interval_us": 4000, "enable_n_in_flight": 1}],
            "5": ["precise_rate_based", {"max_pacing_rate": 12500000, "clock_granularity": 1050, "enable_n_in_flight": 1}],
            "6": ["precise_rate_based", {"max_pacing_rate": 12000000, "clock_granularity": 1050, "enable_n_in_flight": 1}]
        }
    },
    # 6. 非对称突发 (40/60) 复测 r2
    {
        "tag": "test-hybrid-tb-asym40-60-champ-r2",
        "note": "asym tb 40/60 on 1-4 + precise 5(100M) 6(96M) r2",
        "configs": {
            "1": ["token_bucket", {"tokens": 40, "burst": 60, "token_refill_rate": 40, "token_refill_interval_us": 4000, "enable_n_in_flight": 1}],
            "2": ["token_bucket", {"tokens": 40, "burst": 60, "token_refill_rate": 40, "token_refill_interval_us": 4000, "enable_n_in_flight": 1}],
            "3": ["token_bucket", {"tokens": 40, "burst": 60, "token_refill_rate": 40, "token_refill_interval_us": 4000, "enable_n_in_flight": 1}],
            "4": ["token_bucket", {"tokens": 40, "burst": 60, "token_refill_rate": 38, "token_refill_interval_us": 4000, "enable_n_in_flight": 1}],
            "5": ["precise_rate_based", {"max_pacing_rate": 12500000, "clock_granularity": 1000, "enable_n_in_flight": 1}],
            "6": ["precise_rate_based", {"max_pacing_rate": 12000000, "clock_granularity": 1000, "enable_n_in_flight": 1}]
        }
    },
    # 7. 复测 fast14 破纪录构型 (r3) 捕捉超低方差
    {
        "tag": "test-hybrid-tb4-fast14-champ-r3",
        "note": "fast14 tb 40/40/r40/r38 + precise 100M/96M r3",
        "configs": {
            "1": ["token_bucket", {"tokens": 40, "burst": 40, "token_refill_rate": 40, "token_refill_interval_us": 4000, "enable_n_in_flight": 1}],
            "2": ["token_bucket", {"tokens": 40, "burst": 40, "token_refill_rate": 40, "token_refill_interval_us": 4000, "enable_n_in_flight": 1}],
            "3": ["token_bucket", {"tokens": 40, "burst": 40, "token_refill_rate": 40, "token_refill_interval_us": 4000, "enable_n_in_flight": 1}],
            "4": ["token_bucket", {"tokens": 40, "burst": 40, "token_refill_rate": 38, "token_refill_interval_us": 4000, "enable_n_in_flight": 1}],
            "5": ["precise_rate_based", {"max_pacing_rate": 12500000, "clock_granularity": 1000, "enable_n_in_flight": 1}],
            "6": ["precise_rate_based", {"max_pacing_rate": 12000000, "clock_granularity": 1000, "enable_n_in_flight": 1}]
        }
    },
    # 8. 稳健亚军 92M-96M 复测 r3
    {
        "tag": "test-hybrid-tb4-p92M-p96M-r3",
        "note": "tb 1-4 + precise 5(92M/g1k) 6(96M/g1k) r3",
        "configs": {
            "1": ["token_bucket", {"tokens": 40, "burst": 40, "token_refill_rate": 40, "token_refill_interval_us": 4000, "enable_n_in_flight": 1}],
            "2": ["token_bucket", {"tokens": 40, "burst": 40, "token_refill_rate": 40, "token_refill_interval_us": 4000, "enable_n_in_flight": 1}],
            "3": ["token_bucket", {"tokens": 40, "burst": 40, "token_refill_rate": 38, "token_refill_interval_us": 4000, "enable_n_in_flight": 1}],
            "4": ["token_bucket", {"tokens": 40, "burst": 40, "token_refill_rate": 36, "token_refill_interval_us": 4000, "enable_n_in_flight": 1}],
            "5": ["precise_rate_based", {"max_pacing_rate": 11500000, "clock_granularity": 1000, "enable_n_in_flight": 1}],
            "6": ["precise_rate_based", {"max_pacing_rate": 12000000, "clock_granularity": 1000, "enable_n_in_flight": 1}]
        }
    },
    # 9. 经典冠军 100M-96M 复测 r4
    {
        "tag": "test-hybrid-tb4-p100M-p96M-r4",
        "note": "tb 1-4 + precise 5(100M/g1k) 6(96M/g1k) r4",
        "configs": {
            "1": ["token_bucket", {"tokens": 40, "burst": 40, "token_refill_rate": 40, "token_refill_interval_us": 4000, "enable_n_in_flight": 1}],
            "2": ["token_bucket", {"tokens": 40, "burst": 40, "token_refill_rate": 40, "token_refill_interval_us": 4000, "enable_n_in_flight": 1}],
            "3": ["token_bucket", {"tokens": 40, "burst": 40, "token_refill_rate": 38, "token_refill_interval_us": 4000, "enable_n_in_flight": 1}],
            "4": ["token_bucket", {"tokens": 40, "burst": 40, "token_refill_rate": 36, "token_refill_interval_us": 4000, "enable_n_in_flight": 1}],
            "5": ["precise_rate_based", {"max_pacing_rate": 12500000, "clock_granularity": 1000, "enable_n_in_flight": 1}],
            "6": ["precise_rate_based", {"max_pacing_rate": 12000000, "clock_granularity": 1000, "enable_n_in_flight": 1}]
        }
    }
]


def log(msg: str) -> None:
    now_str = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{now_str}] {msg}"
    print(line, flush=True)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def get_completed_tags() -> set[str]:
    tags = set()
    if not RESULTS_FILE.exists():
        return tags
    for line in RESULTS_FILE.read_text("utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
            if rec.get("valid") and rec.get("tag"):
                tags.add(rec["tag"])
        except Exception:
            continue
    return tags


def is_near_midnight() -> bool:
    """如果距离 00:00 还有不到 15 分钟（即 23:45 以后），自动停止，避免干扰打榜控制器。"""
    now = dt.datetime.now()
    if now.hour == 23 and now.minute >= 45:
        return True
    return False


def run_experiment_item(item: dict) -> int:
    tag = item["tag"]
    note = item["note"]
    configs = item["configs"]

    cfg_file = ROOT / "runs" / f"{tag}.configs.json"
    cfg_file.write_text(json.dumps(configs, ensure_ascii=False, indent=2), encoding="utf-8")

    cmd = [
        PY,
        str(ROOT / "harness" / "run_experiment.py"),
        "--tag", tag,
        "--configs-file", str(cfg_file),
        "--note", note
    ]
    log(f"启动实验: {tag} | {note}")
    proc = subprocess.run(cmd, cwd=str(ROOT))
    if proc.returncode == 0:
        log(f"实验完成: {tag} (Exit Code 0)")
        # 自动刷新统计报告
        subprocess.run([PY, str(ROOT / "tools" / "summarize_hybrid_stats.py")], cwd=str(ROOT))
    else:
        log(f"[WARN] 实验异常: {tag} (Exit Code {proc.returncode})")
    return proc.returncode


def main() -> int:
    log("=== 自动不间断科研评测控制器启动 ===")
    
    idx = 0
    while True:
        if is_near_midnight():
            log("当前时间已达 23:45，为保证 00:05 官方打榜环境绝对稳定，自动暂停后台科研评测循环。")
            break

        completed = get_completed_tags()

        if idx < len(RESEARCH_QUEUE):
            item = RESEARCH_QUEUE[idx]
            idx += 1
            if item["tag"] in completed:
                log(f"跳过已完成实验: {item['tag']}")
                continue
        else:
            # 循环轮测 5 大核心速率阶梯：92M, 94M, 96M, 98M, 100M，压低标准误并寻找绝对最优解
            GRID_CANDIDATES = [
                ("p92M-p96M", 11500000, 12000000, "92M on 5.bin, 96M on 6.bin (超稳防守)"),
                ("p94M-p96M", 11750000, 12000000, "94M on 5.bin, 96M on 6.bin (精细网格)"),
                ("p96M-both", 12000000, 12000000, "96M on 5.bin, 96M on 6.bin (对称平滑)"),
                ("p98M-p96M", 12250000, 12000000, "98M on 5.bin, 96M on 6.bin (稳健亚军)"),
                ("p100M-p96M", 12500000, 12000000, "100M on 5.bin, 96M on 6.bin (极速冠军)")
            ]
            cycle_idx = (idx - len(RESEARCH_QUEUE)) % len(GRID_CANDIDATES)
            cand_key, r5, r6, cand_desc = GRID_CANDIDATES[cycle_idx]
            
            # 使用经过门禁检验的 fast14 冲锋参数 (1-3 tb40/r40, 4 tb40/r38)
            cand_configs = {
                "1": ["token_bucket", {"tokens": 40, "burst": 40, "token_refill_rate": 40, "token_refill_interval_us": 4000, "enable_n_in_flight": 1}],
                "2": ["token_bucket", {"tokens": 40, "burst": 40, "token_refill_rate": 40, "token_refill_interval_us": 4000, "enable_n_in_flight": 1}],
                "3": ["token_bucket", {"tokens": 40, "burst": 40, "token_refill_rate": 40, "token_refill_interval_us": 4000, "enable_n_in_flight": 1}],
                "4": ["token_bucket", {"tokens": 40, "burst": 40, "token_refill_rate": 38, "token_refill_interval_us": 4000, "enable_n_in_flight": 1}],
                "5": ["precise_rate_based", {"max_pacing_rate": r5, "clock_granularity": 1000, "enable_n_in_flight": 1}],
                "6": ["precise_rate_based", {"max_pacing_rate": r6, "clock_granularity": 1000, "enable_n_in_flight": 1}]
            }
            # 计算该 tag 的下一个运行编号
            rep = 1
            while f"test-grid-{cand_key}-r{rep}" in completed:
                rep += 1
            
            item = {
                "tag": f"test-grid-{cand_key}-r{rep}",
                "note": f"Grid sweep {cand_desc} round {rep}",
                "configs": cand_configs
            }
            idx += 1
            if item["tag"] in completed:
                continue

        run_experiment_item(item)
        time.sleep(5)  # 短暂停顿后立即进入下一场

    log("=== 自动不间断科研评测控制器平稳退出 ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
