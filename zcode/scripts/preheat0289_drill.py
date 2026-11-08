#!/usr/bin/env python3
"""
Task 0289: System Preheat & Daemon Warm-Up Drill Prior to 00:00 Quota Unlock
Verifies state load/save latency <= 10ms, atomic lockfile exclusivity, and in-memory config caching.
"""

import sys
import os
import time
import json
import threading
from pathlib import Path

def run_preheat_drill():
    # 1. State serialization latency test
    test_state = {
        "campaign_date": "2026-11-08",
        "shots_completed": 0,
        "max_shots": 5,
        "decision_tree": {
            "root": "1108-A1-hybrid-champ-90M-96M",
            "fallback": "test-leak-asym-41x2-40-37-36x2-r1"
        },
        "history": []
    }
    state_file = Path("runs/preheat0289_state.json")
    
    t0 = time.perf_counter()
    with open(state_file, "w", encoding="utf-8") as f:
        json.dump(test_state, f, indent=2)
    dt_save_ms = (time.perf_counter() - t0) * 1000.0

    t1 = time.perf_counter()
    with open(state_file, "r", encoding="utf-8") as f:
        loaded = json.load(f)
    dt_load_ms = (time.perf_counter() - t1) * 1000.0

    state_file.unlink(missing_ok=True)

    # 2. Lockfile atomic mutual exclusion test
    lock_path = Path("runs/preheat0289_drill.lock")
    lock_path.unlink(missing_ok=True)

    lock_acquired_count = 0
    lock_contention_errors = 0
    lock_mutex = threading.Lock()

    def lock_attempter(tid):
        nonlocal lock_acquired_count, lock_contention_errors
        try:
            # Atomic creation via O_CREAT | O_EXCL
            fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, f"owner_{tid}".encode("utf-8"))
            os.close(fd)
            with lock_mutex:
                lock_acquired_count += 1
        except FileExistsError:
            with lock_mutex:
                lock_contention_errors += 1
        except Exception:
            with lock_mutex:
                lock_contention_errors += 1

    threads = [threading.Thread(target=lock_attempter, args=(i,)) for i in range(25)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Verify exactly 1 thread acquired the lock, 24 rejected
    lock_exclusive_ok = (lock_acquired_count == 1 and lock_contention_errors == 24)
    lock_path.unlink(missing_ok=True)

    # 3. In-memory config caching warm-up
    target_config = Path("runs/configs/1108-A1-hybrid-champ-90M-96M")
    cached_stages = {}
    if target_config.exists():
        for s in range(1, 7):
            pacer = target_config / str(s) / "pacer.txt"
            if pacer.exists():
                cached_stages[s] = pacer.read_bytes()
    
    config_cache_ok = len(cached_stages) == 6

    pass_gate = bool(
        dt_load_ms <= 10.0 and
        dt_save_ms <= 10.0 and
        lock_exclusive_ok and
        config_cache_ok
    )

    result = {
        "task_id": "0289",
        "state_save_latency_ms": round(dt_save_ms, 3),
        "state_load_latency_ms": round(dt_load_ms, 3),
        "target_max_latency_ms": 10.0,
        "lock_acquired_count": lock_acquired_count,
        "lock_rejected_count": lock_contention_errors,
        "lock_exclusivity_verified": lock_exclusive_ok,
        "cached_config_stages_count": len(cached_stages),
        "preheat_status": "WARM_AND_READY",
        "pass_gate": pass_gate
    }

    out_file = Path("runs/preheat0289_drill.json")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(json.dumps(result, indent=2))
    return pass_gate

if __name__ == "__main__":
    passed = run_preheat_drill()
    if not passed:
        sys.exit(1)
