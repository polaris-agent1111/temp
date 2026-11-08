import json
import numpy as np
from pathlib import Path

results_file = Path('runs/results.jsonl')
tags_to_analyze = [
    'test-anchor-shot2-leak-40x3-36x3',
    'test-anchor-shot2-pert-40x3-37-36-36',
    'test-leak-asym-41x2-40-37-36x2',
    'test-crown-pert-40on2',
    'test-leak-asym-40-40-37-37',
    'test-crown-pert-38on4',
    'test-crown-pert-36on4',
    'test-crown-pert-39on3',
    'test-crown-pert-37on5',
    'test-crown-pert-42on1'
]

data = {t: [] for t in tags_to_analyze}

with open(results_file, 'r', encoding='utf-8') as f:
    for line in f:
        if not line.strip():
            continue
        try:
            d = json.loads(line)
            tag = d.get('tag', '')
            total = d.get('total_seconds')
            valid = d.get('valid', True)
            if not valid or total is None:
                continue
            for prefix in tags_to_analyze:
                if tag.startswith(prefix):
                    data[prefix].append((tag, total))
                    break
        except Exception:
            pass

print("=== STATISTICAL SUMMARY AT 08:00 ===")
for prefix, items in data.items():
    if not items:
        continue
    vals = [x[1] for x in items]
    n = len(vals)
    mean = np.mean(vals)
    std = np.std(vals, ddof=1) if n > 1 else 0.0
    median = np.median(vals)
    vmin = np.min(vals)
    vmax = np.max(vals)
    cv = (std / mean * 100) if mean > 0 else 0.0
    se = std / np.sqrt(n) if n > 1 else 0.0
    ci95_low = mean - 1.96 * se
    ci95_high = mean + 1.96 * se
    print(f"\n[{prefix}] (n={n})")
    print(f"  Runs: {[round(v, 3) for v in vals]}")
    print(f"  Mean: {mean:.3f}s | Median: {median:.3f}s | Min: {vmin:.3f}s | Max: {vmax:.3f}s")
    print(f"  Std: {std:.3f}s | CV: {cv:.1f}% | SE: {se:.3f}s | 95% CI: [{ci95_low:.2f}, {ci95_high:.2f}]s")
