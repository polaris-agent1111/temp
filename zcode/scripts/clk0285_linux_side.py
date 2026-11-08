# -*- coding: utf-8 -*-
"""Task 0285 Linux side (run inside WSL2 Debian python3).

Measures CLOCK_MONOTONIC_RAW / CLOCK_MONOTONIC:
  - clock_getres nominal resolution
  - paired-read granularity histogram (min positive delta)
  - bracketing consistency: consecutive reads non-decreasing, delta in tick grid
Writes zcode/scripts/clk0285_linux_results.json (inside zcode/, authorized).
"""
import json
import ctypes
import time

CLOCK_MONOTONIC_RAW = 4
CLOCK_MONOTONIC = 1

class timespec(ctypes.Structure):
    _fields_ = [("tv_sec", ctypes.c_long), ("tv_nsec", ctypes.c_long)]

lib = ctypes.CDLL(None, use_errno=True)

def clock_gettime(clk):
    ts = timespec()
    if lib.clock_gettime(clk, ctypes.byref(ts)) != 0:
        raise OSError(ctypes.get_errno())
    return ts.tv_sec * 10**9 + ts.tv_nsec

def clock_getres(clk):
    ts = timespec()
    if lib.clock_getres(clk, ctypes.byref(ts)) != 0:
        raise OSError(ctypes.get_errno())
    return ts.tv_sec * 10**9 + ts.tv_nsec

def granularity(clk, n=200000):
    deltas = {}
    prev = clock_gettime(clk)
    for _ in range(n):
        cur = clock_gettime(clk)
        d = cur - prev
        if d < 0:
            deltas["NEGATIVE"] = deltas.get("NEGATIVE", 0) + 1
        else:
            deltas[d] = deltas.get(d, 0) + 1
        prev = cur
    return deltas

res_raw = clock_getres(CLOCK_MONOTONIC_RAW)
res_mono = clock_getres(CLOCK_MONOTONIC)
g_raw = granularity(CLOCK_MONOTONIC_RAW, 100000)
g_mono = granularity(CLOCK_MONOTONIC, 100000)

# span self-check: measure a ~0.2 s span twice, both clocks; report both values
t0 = clock_gettime(CLOCK_MONOTONIC_RAW)
m0 = clock_gettime(CLOCK_MONOTONIC)
time.sleep(0.2)
t1 = clock_gettime(CLOCK_MONOTONIC_RAW)
m1 = clock_gettime(CLOCK_MONOTONIC)

out = {
    "platform": "WSL2-Debian (kernel 6.18.33.2-microsoft-standard-WSL2)",
    "clock_getres_ns": {"CLOCK_MONOTONIC_RAW": res_raw, "CLOCK_MONOTONIC": res_mono},
    "granularity_top_raw": sorted((d, c) for d, c in g_raw.items()
                                  if isinstance(d, int))[:8],
    "granularity_top_mono": sorted((d, c) for d, c in g_mono.items()
                                   if isinstance(d, int))[:8],
    "negative_deltas": {"raw": g_raw.get("NEGATIVE", 0),
                        "mono": g_mono.get("NEGATIVE", 0)},
    "span_0p2s_ns": {"raw": t1 - t0, "mono": m1 - m0},
}
with open("zcode/scripts/clk0285_linux_results.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print(json.dumps(out, ensure_ascii=False, indent=1))
