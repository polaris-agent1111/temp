#!/usr/bin/env python3
"""
Task 0265: Official 6-Stage Directory Hot-Swap Atomicity Extreme Concurrency Stress Test
Verifies 0 partial reads, 0 unhandled file lock crashes, and 0 empty reads across 1,000+ concurrent reads during hot reloads.
Incorporates client-side transparent read-retry and writer-side atomic replace backoff.
"""

import sys
import os
import time
import json
import random
import threading
from pathlib import Path

def atomic_replace_with_backoff(src, dst, max_retries=15):
    """Resilient atomic file replacement for Windows NTFS and POSIX."""
    for attempt in range(max_retries):
        try:
            os.replace(src, dst)
            return True
        except PermissionError:
            time.sleep(0.0005 * (attempt + 1))
    os.replace(src, dst)
    return True

def resilient_read_bytes(path, max_attempts=10):
    """Client reader with microsecond backoff against NTFS lock transient collisions."""
    for attempt in range(max_attempts):
        try:
            return path.read_bytes()
        except PermissionError:
            time.sleep(0.0005 * (attempt + 1))
    return path.read_bytes()

def test_hotswap_concurrency():
    test_root = Path("runs/stress0265_tree/question")
    # Setup test tree
    for stage in range(1, 7):
        s_dir = test_root / str(stage)
        s_dir.mkdir(parents=True, exist_ok=True)
        initial_content = f"leak_rate=40,bucket_cap=30,leak_interval_us=1000\nmode=leak_bucket\n[timestamp:{stage}]"
        (s_dir / "pacer.txt").write_bytes(initial_content.encode("utf-8"))

    stop_event = threading.Event()
    read_stats = {
        "total_reads": 0,
        "valid_reads": 0,
        "empty_reads": 0,
        "partial_reads": 0,
        "unhandled_lock_errors": 0,
        "format_errors": 0
    }
    stats_lock = threading.Lock()

    def reader_worker(worker_id):
        while not stop_event.is_set():
            stage = random.randint(1, 6)
            pacer_path = test_root / str(stage) / "pacer.txt"
            try:
                content = resilient_read_bytes(pacer_path)
                with stats_lock:
                    read_stats["total_reads"] += 1
                if len(content) == 0:
                    with stats_lock:
                        read_stats["empty_reads"] += 1
                    continue
                
                # Verify structure
                lines = content.split(b"\n")
                if len(lines) != 3:
                    with stats_lock:
                        read_stats["partial_reads"] += 1
                    continue
                
                if not lines[0].startswith(b"leak_rate=") or not lines[2].startswith(b"[timestamp:"):
                    with stats_lock:
                        read_stats["format_errors"] += 1
                    continue

                with stats_lock:
                    read_stats["valid_reads"] += 1

            except PermissionError:
                with stats_lock:
                    read_stats["unhandled_lock_errors"] += 1
            except FileNotFoundError:
                with stats_lock:
                    read_stats["partial_reads"] += 1
            except Exception:
                with stats_lock:
                    read_stats["format_errors"] += 1

            time.sleep(0.0005) # 500us interval

    # Start 8 reader threads
    threads = []
    for i in range(8):
        t = threading.Thread(target=reader_worker, args=(i,))
        t.daemon = True
        threads.append(t)
        t.start()

    # Writer: perform 60 hot-swaps across all 6 stages
    switch_latencies = []
    n_switches = 60
    candidates = [
        {"r": 41, "c": 30},
        {"r": 40, "c": 28},
        {"r": 38, "c": 32},
        {"r": 37, "c": 30}
    ]

    for sw in range(n_switches):
        cfg = candidates[sw % len(candidates)]
        t0 = time.perf_counter()
        # Atomic switch across 6 stages using temp file + resilient atomic replace
        for stage in range(1, 7):
            s_dir = test_root / str(stage)
            target_path = s_dir / "pacer.txt"
            tmp_path = s_dir / f"pacer.txt.tmp_{sw}_{stage}"
            content = f"leak_rate={cfg['r']},bucket_cap={cfg['c']},leak_interval_us=1000\nmode=leak_bucket\n[timestamp:{stage}]".encode("utf-8")
            
            # Write temp file and atomic replace with backoff
            tmp_path.write_bytes(content)
            atomic_replace_with_backoff(tmp_path, target_path)

        dt_ms = (time.perf_counter() - t0) * 1000.0
        switch_latencies.append(dt_ms)
        time.sleep(0.005) # 5ms between switches

    # Wait until total reads exceed 1,000
    while True:
        with stats_lock:
            if read_stats["total_reads"] >= 1000:
                break
        time.sleep(0.01)

    stop_event.set()
    for t in threads:
        t.join(timeout=1.0)

    mean_latency = float(sum(switch_latencies) / len(switch_latencies))
    p95_latency = float(sorted(switch_latencies)[int(len(switch_latencies) * 0.95)])

    pass_gate = bool(
        read_stats["total_reads"] >= 1000 and
        read_stats["empty_reads"] == 0 and
        read_stats["partial_reads"] == 0 and
        read_stats["unhandled_lock_errors"] == 0 and
        read_stats["format_errors"] == 0 and
        mean_latency <= 5.0
    )

    result = {
        "task_id": "0265",
        "concurrency_readers": 8,
        "total_reads_completed": read_stats["total_reads"],
        "valid_reads": read_stats["valid_reads"],
        "empty_reads": read_stats["empty_reads"],
        "partial_reads": read_stats["partial_reads"],
        "unhandled_lock_errors": read_stats["unhandled_lock_errors"],
        "format_errors": read_stats["format_errors"],
        "hot_switches_completed": n_switches,
        "mean_switch_latency_ms": round(mean_latency, 3),
        "p95_switch_latency_ms": round(p95_latency, 3),
        "target_max_latency_ms": 5.0,
        "pass_gate": pass_gate
    }

    out_file = Path("runs/stress0265_hotswap_concurrency.json")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(json.dumps(result, indent=2))
    return pass_gate

if __name__ == "__main__":
    passed = test_hotswap_concurrency()
    if not passed:
        sys.exit(1)
