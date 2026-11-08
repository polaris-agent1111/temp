import json
from collections import defaultdict
from pathlib import Path

def main():
    results_path = Path("runs/results.jsonl")
    lines = [json.loads(l) for l in results_path.read_text("utf-8").splitlines() if l.strip()]
    valid_lines = [l for l in lines if l.get("valid")]
    print(f"Total valid runs: {len(valid_lines)}")

    sorted_runs = sorted(valid_lines, key=lambda x: x["total_seconds"])
    print("\n=== TOP 15 FASTEST RUNS OVERALL ===")
    for r in sorted_runs[:15]:
        d = r["downloads"]
        print(f"{r['tag'][:36]:36s} | total: {r['total_seconds']:7.3f}s | 1: {d['1.bin']:5.2f}s, 2: {d['2.bin']:5.2f}s, 3: {d['3.bin']:5.2f}s, 4: {d['4.bin']:5.2f}s, 5: {d['5.bin']:5.2f}s, 6: {d['6.bin']:5.2f}s")

    print("\n=== ABSOLUTE MINIMUM PER FILE ===")
    sum_mins = 0.0
    for fn in ["1.bin", "2.bin", "3.bin", "4.bin", "5.bin", "6.bin"]:
        best = min(valid_lines, key=lambda x: x["downloads"][fn])
        t = best["downloads"][fn]
        sum_mins += t
        print(f"{fn:6s}: {t:6.3f}s in run {best['tag']} (total was {best['total_seconds']:.3f}s)")
    print(f"Absolute Theoretical Lower Bound (Sum of Minima): {sum_mins:.3f}s")

if __name__ == "__main__":
    main()

def show_precise_runs():
    results_path = Path("runs/results.jsonl")
    lines = [json.loads(l) for l in results_path.read_text("utf-8").splitlines() if l.strip()]
    precise_runs = [l for l in lines if "precise" in str(l) and l.get("valid")]
    print(f"\nNumber of valid precise runs: {len(precise_runs)}")
    for r in precise_runs:
        print(f"{r['tag']:38s} | {r['total_seconds']:7.3f}s | {r.get('note', '')}")

if __name__ == "__main__":
    show_precise_runs()
