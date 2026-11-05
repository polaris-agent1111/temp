#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从云主机把某个已完成评测的结果拉回来并写入 runs/results.jsonl（用于补录）。"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "client"))
from vmssh import VmShell  # noqa: E402

RESULTS = ROOT / "runs" / "results.jsonl"
EVALS = ROOT / "runs" / "evals"


def main() -> int:
    if len(sys.argv) < 2:
        print("用法: python harness/import_vm_result.py <vm_tag> [note]")
        return 2
    tag = sys.argv[1]
    note = sys.argv[2] if len(sys.argv) > 2 else ""
    EVALS.mkdir(parents=True, exist_ok=True)
    vm = VmShell()
    vm.connect()
    try:
        local = EVALS / f"{tag}.json"
        vm.pull_file(f"/home/openlab/evals/{tag}/result.json", local)
        vm.pull_file(f"/home/openlab/evals/{tag}/run.log", EVALS / f"{tag}.log")
    finally:
        vm.close()
    data = json.loads(local.read_text("utf-8"))
    q = data["question"][0]
    rec = {
        "at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "tag": tag,
        "note": note,
        "config": {},
        "total_seconds": q["total_seconds"],
        "downloads": {d["filename"]: d["seconds"] for d in q["downloads"]},
    }
    RESULTS.parent.mkdir(parents=True, exist_ok=True)
    with RESULTS.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"[OK] {tag}: {q['total_seconds']:.3f}s {rec['downloads']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
