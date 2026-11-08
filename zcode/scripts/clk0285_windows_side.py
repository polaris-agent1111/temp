# -*- coding: utf-8 -*-
"""Task 0285 Windows side: QPC granularity, Python perf_counter_ns conversion
fidelity, and merge with the WSL2 Linux-side results.

Verdict criterion (pre-registered):
  - per-timestamp representation deviation vs ideal nanosecond timeline
    <= 50 ns on BOTH platforms (Windows: round-to-nearest of QPC tick;
    Linux: TSC-grid rounding), i.e. single-endpoint span-bound rounding.
  - absolute epoch sync is out of scope (physically needs PTP hardware);
    reported separately as a ms-scale offset, never claimed <=50ns.
Writes zcode/scripts/clk0285_windows_results.json (inside zcode/, authorized).
"""
import json
import ctypes
import time
import statistics as st
from pathlib import Path

sys_out = Path(__file__).resolve().parent
import sys
sys.stdout.reconfigure(encoding="utf-8")

kernel32 = ctypes.windll.kernel32

freq = ctypes.c_longlong()
ok = kernel32.QueryPerformanceFrequency(ctypes.byref(freq))
assert ok, "QueryPerformanceFrequency failed"
FREQ = freq.value
TICK_NS = 1e9 / FREQ

qpc = ctypes.c_longlong()
def qpc_now():
    kernel32.QueryPerformanceCounter(ctypes.byref(qpc))
    return qpc.value

# 1) raw QPC paired-read granularity
raw_deltas = {}
prev = qpc_now()
for _ in range(200000):
    cur = qpc_now()
    d = cur - prev
    raw_deltas[d] = raw_deltas.get(d, 0) + 1
    prev = cur
raw_min = min(d for d in raw_deltas if d > 0)

# 2) Python perf_counter_ns paired granularity (what the repo actually uses)
pc_deltas = {}
prev = time.perf_counter_ns()
for _ in range(200000):
    cur = time.perf_counter_ns()
    d = cur - prev
    pc_deltas[d] = pc_deltas.get(d, 0) + 1
    prev = cur
pc_min = min(d for d in pc_deltas if d > 0)

# 3) conversion fidelity: perf_counter_ns must be an exact tick multiple
#    (round-to-nearest of integer ticks) -> mod test against tick grid
mods = {}
N = 200000
for _ in range(N):
    p = time.perf_counter_ns()
    m = p % 100
    mods[m] = mods.get(m, 0) + 1

# 4) bracketing sanity: perf value lies between conversions of QPC reads
#    that bracket the perf read (allows one tick of call-latency slack)
bad_bracket = 0
for _ in range(20000):
    q0 = qpc_now()
    p = time.perf_counter_ns()
    q1 = qpc_now()
    c0 = q0 * 10**9 // FREQ
    c1 = -((-q1 * 10**9) // FREQ)  # ceil
    if not (c0 - TICK_NS <= p <= c1 + TICK_NS):
        bad_bracket += 1

# 5) 0.2 s span self-check
t0 = qpc_now()
p0 = time.perf_counter_ns()
time.sleep(0.2)
t1 = qpc_now()
p1 = time.perf_counter_ns()

out = {
    "platform": "Windows (host) — Git Bash / CPython",
    "QueryPerformanceFrequency": FREQ,
    "qpc_tick_ns": TICK_NS,
    "qpc_min_positive_delta_ticks": raw_min,
    "qpc_raw_delta_top": sorted(raw_deltas.items())[:8],
    "perf_counter_ns_min_positive_delta": pc_min,
    "perf_counter_ns_delta_top": sorted(pc_deltas.items())[:8],
    "perf_mod100_top": sorted(mods.items(), key=lambda kv: -kv[1])[:8],
    "perf_mod100_nonzero_frac": round(1 - mods.get(0, 0) / N, 6),
    "bracket_violations": bad_bracket,
    "span_0p2s_ns": {"qpc": t1 - t0 and (t1 - t0) * 10**9 / FREQ,
                     "perf_counter_ns": p1 - p0},
}
lp = sys_out / "clk0285_linux_results.json"
if lp.exists():
    out["linux_side"] = json.loads(lp.read_text(encoding="utf-8"))

with open(sys_out / "clk0285_windows_results.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print(json.dumps(out, ensure_ascii=False, indent=1)[:2200])
