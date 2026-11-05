#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""只把配置上传到云主机的 question/ 目录（不跑评测），用于提交前设置状态。

用法：
  python harness/upload_config.py --tag submit-v1 --mode leak_bucket --params "leak_rate=8,bucket_cap=30,leak_interval_us=1000"
  python harness/upload_config.py --tag submit-v1 --configs-file cfg.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "harness"))
sys.path.insert(0, str(ROOT / "client"))

from run_experiment import (  # noqa: E402
    VM_QUESTION, VM_TMP, build_tree, connect_vm, make_tar, parse_uniform,
)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", required=True)
    ap.add_argument("--mode")
    ap.add_argument("--params", nargs="*", default=[])
    ap.add_argument("--configs-file")
    args = ap.parse_args(argv)

    if args.configs_file:
        raw = json.loads(Path(args.configs_file).read_text("utf-8"))
        per_dir = {int(k): (v[0], v[1] if len(v) > 1 and v[1] else {}) for k, v in raw.items()}
    elif args.mode:
        per_dir = {n: (args.mode, parse_uniform(args.params)) for n in range(1, 7)}
    else:
        raise SystemExit("需要 --mode 或 --configs-file")

    tree = build_tree(args.tag, per_dir)
    tar_path = make_tar(tree, args.tag)
    vm = connect_vm()
    try:
        vm.push_file(tar_path, f"{VM_TMP}/cfg_{args.tag}.tar.gz")
        code, out = vm.run(
            f"cd {VM_QUESTION} && find . -name pacer.txt -delete && "
            f"tar xzf {VM_TMP}/cfg_{args.tag}.tar.gz -C {VM_QUESTION} && "
            f"for f in */pacer.txt; do echo \"== $f\"; cat $f; echo; done", timeout=120)
        print(out)
        code, out = vm.run("cd /home/openlab/Desktop && ./format_check_client 2>&1 | tail -8",
                           timeout=120)
        print(out)
        if "检查结果: 通过" not in out:
            print("[FAIL] 格式检查未通过")
            return 1
        print("[OK] 配置已就位，格式检查通过")
    finally:
        vm.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
