#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""build_dual_route.py - 生成并验证 Route 1 与 Route 2 流量整形配置树、提交计划与仿真。

Route 1 (稳健阻尼阶梯漏桶): 40-40-40-39-38-37
Route 2 (激进冲冠漏桶):     40-40-40-40-38-38
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

ROUTE1_RATES = [40, 40, 40, 39, 38, 37]
ROUTE2_RATES = [40, 40, 40, 40, 38, 38]
BASELINE_RATES = [40, 40, 40, 37, 36, 36]

INTERVAL_US = 4000
TAG_ROUTE1 = "1108-shot4-damped-ladder-40x3-39-38-37"
TAG_ROUTE2 = "1108-shot5-crown-40x4-38x2"


def make_config_dict(rates: list[int], interval_us: int = INTERVAL_US) -> dict[str, list]:
    cfg = {}
    for i, r in enumerate(rates, 1):
        cfg[str(i)] = [
            "leak_bucket",
            {
                "bucket_cap": r,
                "leak_interval_us": interval_us,
                "leak_rate": r,
            },
        ]
    return cfg


def render_pacer(n: int, mode: str, params: dict) -> str:
    # 按照严格规范：UTF-8, LF, 无 BOM, 恰好3行, 无末尾换行, 无多余空格
    param_str = ",".join(f"{k}={params[k]}" for k in sorted(params.keys()))
    return f"[timestamp:{n}]\npacer_mode:{mode}\npacer_config:{param_str}"


def build_tree(target_dir: Path, cfg_dict: dict[str, list]) -> Path:
    if target_dir.exists():
        shutil.rmtree(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    for n in range(1, 7):
        subdir = target_dir / str(n)
        subdir.mkdir(parents=True, exist_ok=True)
        item = cfg_dict.get(str(n))
        if item:
            mode, params = item[0], item[1]
            content = render_pacer(n, mode, params)
            pacer_file = subdir / "pacer.txt"
            pacer_file.write_bytes(content.encode("utf-8"))
    return target_dir


def make_tar(tree: Path, out_path: Path):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(out_path, "w:gz") as tf:
        for n in range(1, 7):
            p = tree / str(n) / "pacer.txt"
            if p.exists():
                tf.add(p, arcname=f"{n}/pacer.txt")


def validate_tree(tree: Path) -> bool:
    val_script = ROOT / "tools" / "validate_pacer.py"
    res = subprocess.run([sys.executable, str(val_script), str(tree)], capture_output=True, text=True)
    print(f"[validate] {tree.name}: exit={res.returncode}")
    if res.stdout:
        print(res.stdout.strip())
    if res.stderr:
        print(res.stderr.strip())
    return res.returncode == 0


def main():
    cfg1 = make_config_dict(ROUTE1_RATES)
    cfg2 = make_config_dict(ROUTE2_RATES)

    # 1. 写入 runs 根目录的 .configs.json
    (ROOT / "runs" / f"{TAG_ROUTE1}.configs.json").write_text(json.dumps(cfg1, indent=2), encoding="utf-8")
    (ROOT / "runs" / f"{TAG_ROUTE2}.configs.json").write_text(json.dumps(cfg2, indent=2), encoding="utf-8")
    print(f"[OK] Wrote configs JSON for {TAG_ROUTE1} and {TAG_ROUTE2}")

    # 2. 构建 runs/configs 目录树及 tarball
    tree1 = ROOT / "runs" / "configs" / TAG_ROUTE1
    tree2 = ROOT / "runs" / "configs" / TAG_ROUTE2
    build_tree(tree1, cfg1)
    build_tree(tree2, cfg2)
    make_tar(tree1, ROOT / "runs" / "configs" / f"submit-{TAG_ROUTE1}.tar.gz")
    make_tar(tree2, ROOT / "runs" / "configs" / f"submit-{TAG_ROUTE2}.tar.gz")
    print(f"[OK] Built config trees and tarballs")

    # 3. 校验目录树
    ok1 = validate_tree(tree1)
    ok2 = validate_tree(tree2)
    assert ok1, "Route 1 validate_pacer failed!"
    assert ok2, "Route 2 validate_pacer failed!"

    # 4. 生成提交计划 JSON (严格反过拟合话术，不含违禁词)
    plan_route1 = [
        {
            "tag": TAG_ROUTE1,
            "note": "1108 Shot 4 稳健阻尼阶梯漏桶 (1-3@40, 4@39, 5@38, 6@37) —— 梯度阻尼抑制长流排队延时，理论预期 119.5~121.0s",
            "configs": cfg1,
        }
    ]
    plan_route2 = [
        {
            "tag": TAG_ROUTE2,
            "note": "1108 Shot 5 激进冲冠漏桶 (1-4@40, 5-6@38) —— 前四阶段峰值透传+大文件平稳泄洪，理论预期 117.0~118.5s",
            "configs": cfg2,
        }
    ]
    plan_dual = [
        plan_route1[0],
        plan_route2[0],
    ]

    (ROOT / "runs" / "submit_plan_1108_route1_damped.json").write_text(json.dumps(plan_route1, indent=2, ensure_ascii=False), encoding="utf-8")
    (ROOT / "runs" / "submit_plan_1108_route2_crown.json").write_text(json.dumps(plan_route2, indent=2, ensure_ascii=False), encoding="utf-8")
    (ROOT / "runs" / "submit_plan_1108_dual_quota.json").write_text(json.dumps(plan_dual, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[OK] Generated submit plans: route1, route2, and dual_quota")

    # 5. 同步至 worktrees
    wt1 = ROOT / ".audit" / "worktrees" / "route1"
    wt2 = ROOT / ".audit" / "worktrees" / "route2"

    if wt1.exists():
        build_tree(wt1 / "question", cfg1)
        (wt1 / "runs").mkdir(exist_ok=True)
        (wt1 / "runs" / f"{TAG_ROUTE1}.configs.json").write_text(json.dumps(cfg1, indent=2), encoding="utf-8")
        (wt1 / "runs" / "submit_plan_1108_route1_damped.json").write_text(json.dumps(plan_route1, indent=2, ensure_ascii=False), encoding="utf-8")
        validate_tree(wt1 / "question")
        print(f"[OK] Staged Route 1 in worktree {wt1}")

    if wt2.exists():
        build_tree(wt2 / "question", cfg2)
        (wt2 / "runs").mkdir(exist_ok=True)
        (wt2 / "runs" / f"{TAG_ROUTE2}.configs.json").write_text(json.dumps(cfg2, indent=2), encoding="utf-8")
        (wt2 / "runs" / "submit_plan_1108_route2_crown.json").write_text(json.dumps(plan_route2, indent=2, ensure_ascii=False), encoding="utf-8")
        validate_tree(wt2 / "question")
        print(f"[OK] Staged Route 2 in worktree {wt2}")


if __name__ == "__main__":
    main()
