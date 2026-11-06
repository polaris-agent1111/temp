#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批量提交：按清单依次「上传配置 → 格式检查 → 官方提交」。

用途：官方评测对同一配置近似确定（固定随机种子），所以每天 5 次额度应作为
5 次「配置探测」。本脚本把一个清单里的配置逐个投出去。

用法：
  python tools/submit_batch.py --plan runs/submit_plan_1106.json            # 预检（dry-run）
  python tools/submit_batch.py --plan runs/submit_plan_1106.json --yes      # 真提交

清单格式（数组，每项一个提交）：
[
  {"tag": "s6-leak-24-50", "note": "leak 24/50/4000 本地 122.1",
   "all": ["leak_bucket", {"leak_rate": 24, "bucket_cap": 50, "leak_interval_us": 4000}]},
  {"tag": "s7-mix", "note": "分文件",
   "configs": {"1": ["leak_bucket", {"leak_rate": 36, "bucket_cap": 50, "leak_interval_us": 4000}],
               "2": ["leak_bucket", {"leak_rate": 24, "bucket_cap": 50, "leak_interval_us": 4000}]}}
]
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable
LIMIT = 5


def run(cmd: list[str]) -> int:
    print(f"\n$ {' '.join(cmd)}", flush=True)
    return subprocess.call(cmd, cwd=str(ROOT))


def norm_params(params: dict) -> list[str]:
    return [f"{k}={v}" for k, v in (params or {}).items()]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", required=True)
    ap.add_argument("--yes", action="store_true")
    ap.add_argument("--rehearse", action="store_true", help="只做上传+格式检查，不提交（演练）")
    args = ap.parse_args(argv)

    plan = json.loads(Path(args.plan).read_text("utf-8"))
    print(f"[plan] {len(plan)} 个提交：")
    for i, item in enumerate(plan, 1):
        print(f"  {i}. {item['tag']}: {item.get('note','')}")

    if not args.yes and not args.rehearse:
        print("\n[dry-run] 加 --yes 才会真的提交（加 --rehearse 可只做上传+格式检查）")
        return 0

    for i, item in enumerate(plan, 1):
        tag = item["tag"]
        print(f"\n===== ({i}/{len(plan)}) {tag} =====")
        if "all" in item:
            mode, params = item["all"][0], (item["all"][1] if len(item["all"]) > 1 else {})
            cmd = [PY, "harness/upload_config.py", "--tag", tag, "--mode", mode,
                   "--params", *norm_params(params)]
        else:
            cfg_file = ROOT / "runs" / f"{tag}.configs.json"
            cfg_file.write_text(json.dumps(item["configs"], ensure_ascii=False), "utf-8")
            cmd = [PY, "harness/upload_config.py", "--tag", tag, "--configs-file", str(cfg_file)]
        if run(cmd) != 0:
            print(f"[ERR] {tag} 上传/格式检查失败，停止")
            return 2
        if args.rehearse:
            print(f"[rehearse] {tag} 格式检查通过（未提交）")
            continue
        if run([PY, "client/submit_vm.py", "--yes",
                "--note", f"{tag} | {item.get('note', tag)}"]) != 0:
            print(f"[ERR] {tag} 提交失败（可能是额度用尽），停止")
            return 3
    print("\n[OK] 全部提交完成" if not args.rehearse else "\n[OK] 演练完成（全部格式检查通过）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
