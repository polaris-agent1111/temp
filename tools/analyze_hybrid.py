#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import sys
from pathlib import Path

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "runs" / "results.jsonl"

def main():
    with open(RESULTS, "r", encoding="utf-8") as f:
        lines = [json.loads(line) for line in f if line.strip()]

    print(f"Total runs: {len(lines)}")
    print(f"{'TAG':<35} | {'TOTAL':>7} | {'1-4.bin':>7} | {'5.bin':>7} | {'6.bin':>7} | {'NOTE'}")
    print("-" * 90)

    # Filter for hybrid or recent interesting runs
    for r in lines[-15:]:
        tag = r.get("tag", "")
        tot = r.get("total_seconds")
        tot_str = f"{tot:.3f}s" if tot else "N/A"
        dl = r.get("downloads", {})
        if dl:
            s1_4 = sum(dl.get(f"{i}.bin", 0) for i in range(1, 5))
            s5 = dl.get("5.bin", 0)
            s6 = dl.get("6.bin", 0)
            s1_4_str = f"{s1_4:.3f}s"
            s5_str = f"{s5:.3f}s"
            s6_str = f"{s6:.3f}s"
        else:
            s1_4_str = s5_str = s6_str = "N/A"
        note = r.get("note", "")[:25]
        print(f"{tag:<35} | {tot_str:>7} | {s1_4_str:>7} | {s5_str:>7} | {s6_str:>7} | {note}")

if __name__ == "__main__":
    main()
