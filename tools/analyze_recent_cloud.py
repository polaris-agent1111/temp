import json

with open('runs/results.jsonl', 'r', encoding='utf-8') as f:
    lines = [json.loads(line) for line in f if line.strip()]

target_tags = [
    'test-leak-asym-40-40-38-36-r1',
    'test-leak-asym-40-40-38-36-r2',
    'test-leak-asym-40-40-37-37-r1',
    'test-leak-asym-40-40-37-37-r2',
    'test-leak-asym-41-40-37-36-r1',
    'test-leak-asym-41-40-37-36-r2',
    'test-leak-asym-41-40-38-36-r1',
    'test-leak-asym-41-40-38-36-r2',
    'test-leak-asym-41-40-38-36-r3',
    'test-leak-asym-42-41-40-38-37-r1',
    'test-leak-asym-42-41-40-38-37-r2',
    'test-leak-asym-42-41-40-38-37-r3',
]

print(f"{'Tag':<35} | {'Total':<7} | {'1.bin':<5} | {'2.bin':<5} | {'3.bin':<5} | {'4.bin':<5} | {'5.bin':<6} | {'6.bin':<6}")
print("-" * 85)

for tag in target_tags:
    for r in lines:
        if r.get('tag') == tag:
            dl = r.get('downloads', {})
            tot = r.get('total_seconds', 0)
            print(f"{tag:<35} | {tot:6.2f}s | {dl.get('1.bin',0):5.2f} | {dl.get('2.bin',0):5.2f} | {dl.get('3.bin',0):5.2f} | {dl.get('4.bin',0):5.2f} | {dl.get('5.bin',0):6.2f} | {dl.get('6.bin',0):6.2f}")
