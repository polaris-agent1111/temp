import json
import numpy as np

with open('runs/results.jsonl', 'r', encoding='utf-8') as f:
    lines = [json.loads(line) for line in f if line.strip()]

groups = [
    ('test-anchor-shot2-leak-40x3-36x3', 'Shot 2 基准锚点 (1-3@40, 4-6@36)'),
    ('test-anchor-shot2-pert-40x3-37-36-36', 'Shot 2 邻域微扰 +1 (4.bin 36->37)'),
    ('test-anchor-shot2-pert-39x3-36x3', 'Shot 2 邻域微扰 -1 (1-3.bin 40->39)'),
    ('test-leak-asym-41x2-40-37-36x2', '终极融合构型 (1-2@41, 3@40, 4@37, 5-6@36)'),
    ('test-leak-asym-41x2-40x2-36x2', 'Shot 2 前程微加速 (1-2@41, 3-4@40, 5-6@36)'),
    ('test-leak-asym-40-40-37-37', '超平稳双长文件 (1-4@40, 5-6@37)'),
    ('test-leak-asym-40x2-39x2-37x2', '稳态防守平台点 (1-2@40, 3-4@39, 5-6@37)'),
    ('test-leak-asym-40x3-37-37p5-36', '5.bin 半步精调 (4@37, 5@75/8ms, 6@36)'),
    ('test-leak-asym-41-40-37-36', '前程提速冲榜 (1-3@41, 4@40, 5@37, 6@36)'),
    ('test-leak-asym-41-40-37-37', '交叉融合 (1-3@41, 4@40, 5-6@37)'),
    ('test-leak-asym-40x3-38-37-36', '平滑过渡阶梯 (1-3@40, 4@38, 5@37, 6@36)'),
]

print("=" * 115)
print(f"{'构型 Tag':<36} | {'说明':<22} | {'n':<2} | {'Min':<6} | {'Mean':<6} | {'Median':<6} | {'Max':<6} | {'Std':<5} | {'CV%':<5} | {'95% CI':<15}")
print("=" * 115)

for prefix, desc in groups:
    matches = [r for r in lines if r.get('tag', '').startswith(prefix)]
    valid_runs = [r for r in matches if r.get('valid', True) and 'total_seconds' in r]
    if not valid_runs:
        continue
    totals = [r['total_seconds'] for r in valid_runs]
    n = len(totals)
    t_min = min(totals)
    t_max = max(totals)
    t_mean = float(np.mean(totals))
    t_med = float(np.median(totals))
    t_std = float(np.std(totals, ddof=1)) if n > 1 else 0.0
    cv = (t_std / t_mean) * 100 if t_mean > 0 else 0.0
    se = t_std / (n**0.5) if n > 1 else 0.0
    ci_low = t_mean - 1.96 * se
    ci_high = t_mean + 1.96 * se
    ci_str = f"[{ci_low:5.1f}, {ci_high:5.1f}]"
    print(f"{prefix:<36} | {desc:<22} | {n:<2} | {t_min:6.2f} | {t_mean:6.2f} | {t_med:6.2f} | {t_max:6.2f} | {t_std:5.2f} | {cv:4.1f}% | {ci_str:<15}")

print("=" * 115)

print("\n--- 终极融合构型全量明细: test-leak-asym-41x2-40-37-36x2 ---")
matches = [r for r in lines if r.get('tag', '').startswith('test-leak-asym-41x2-40-37-36x2')]
valid_runs = [r for r in matches if r.get('valid', True) and 'total_seconds' in r]
for r in valid_runs:
    dl = r.get('downloads', {})
    t14 = dl.get('1.bin',0) + dl.get('2.bin',0) + dl.get('3.bin',0) + dl.get('4.bin',0)
    print(f"   {r['tag']:<38} : {r['total_seconds']:6.2f}s | 1-4: {t14:5.2f}s | 5: {dl.get('5.bin',0):5.2f}s | 6: {dl.get('6.bin',0):5.2f}s")
