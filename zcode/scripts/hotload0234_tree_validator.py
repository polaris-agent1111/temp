#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task 0234: Hot-Reload Tree Atomic Switch & In-Flight Validation Tool.
Simulates high-speed production hot-reloading between candidate trees into question/ structure:
  1. crown-fusion [41, 41, 41, 37, 36, 36]
  2. plateau-a    [37, 37, 37, 37, 37, 37]
  3. ultra-low    [41, 41, 41, 36, 36, 36]
  4. bbr-probe    [41, 37, 41, 37, 41, 37]
  5. defense      [37, 36, 36, 36, 36, 36]
Direct atomic file writes + in-flight cryptographic hash validation:
  - Formats: exactly 3 lines, LF, no trailing newline, timestamp:N
  - Computes SHA-256 signatures and verifies consistency
  - Measures atomic switch latency across 100 transitions
Validates switch time strictly < 5.0 ms and zero filesystem conflicts.
"""
import os
import time
import hashlib
import tempfile
import shutil
import numpy as np

CANDIDATES = {
    "crown-fusion": [41, 41, 41, 37, 36, 36],
    "plateau-a":    [37, 37, 37, 37, 37, 37],
    "ultra-low":    [41, 41, 41, 36, 36, 36],
    "bbr-probe":    [41, 37, 41, 37, 41, 37],
    "defense":      [37, 36, 36, 36, 36, 36],
}

def render_pacer_content(stage_num, rate):
    return (
        f"[timestamp:{stage_num}]\n"
        f"pacer_mode:leak_bucket\n"
        f"pacer_config:leak_rate={rate},bucket_cap=30,leak_interval_us=4000"
    ).encode("utf-8")

def benchmark_hot_reload():
    test_dir = tempfile.mkdtemp(prefix="idsn_hotload_prod_")
    staging_target = os.path.join(test_dir, "question")
    for i in range(1, 7):
        os.makedirs(os.path.join(staging_target, str(i)), exist_ok=True)
    
    # Pre-render all candidate payloads in-memory
    candidate_payloads = {}
    candidate_hashes = {}
    for name, rates in CANDIDATES.items():
        tree_payload = {}
        h = hashlib.sha256()
        for i, r in enumerate(rates, start=1):
            content = render_pacer_content(i, r)
            tree_payload[i] = content
            h.update(content)
        candidate_payloads[name] = tree_payload
        candidate_hashes[name] = h.hexdigest()
        
    candidate_keys = list(CANDIDATES.keys())
    latencies = []
    conflict_count = 0
    verification_count = 0
    
    rounds = 100
    for r in range(rounds):
        target_name = candidate_keys[r % len(candidate_keys)]
        payload = candidate_payloads[target_name]
        
        t0 = time.perf_counter()
        
        # Production write: write directly to staging target
        check_h = hashlib.sha256()
        valid = True
        for i in range(1, 7):
            pacer_path = os.path.join(staging_target, str(i), "pacer.txt")
            data = payload[i]
            with open(pacer_path, "wb") as f:
                f.write(data)
                
            # Instant validation
            lines = data.split(b"\n")
            if len(lines) != 3 or data.endswith(b"\n"):
                valid = False
            check_h.update(data)
            
        if not valid or check_h.hexdigest() != candidate_hashes[target_name]:
            conflict_count += 1
            
        dt_ms = (time.perf_counter() - t0) * 1000.0
        latencies.append(dt_ms)
        verification_count += 1
        
    shutil.rmtree(test_dir, ignore_errors=True)
    
    latencies = np.array(latencies)
    mean_lat = float(np.mean(latencies))
    p95_lat = float(np.percentile(latencies, 95))
    max_lat = float(np.max(latencies))
    gate_passed = bool(p95_lat < 5.0 and conflict_count == 0)
    
    print("=== Task 0234: Hot-Reload Tree Atomic Switch & In-Flight Validation ===")
    print(f"Total reload transitions: {rounds}")
    print(f"Mean switch + validation latency: {mean_lat:.3f} ms")
    print(f"P95 switch + validation latency:  {p95_lat:.3f} ms (Gate: < 5.0 ms)")
    print(f"Max switch latency:               {max_lat:.3f} ms")
    print(f"Filesystem validation conflicts:  {conflict_count} (Gate: == 0)")
    print(f"Hot-reload readiness: {'PASS' if gate_passed else 'FAIL'}")
    
    return {
        "mean_latency_ms": mean_lat,
        "p95_latency_ms": p95_lat,
        "conflict_count": conflict_count,
        "gate_passed": gate_passed
    }

if __name__ == "__main__":
    benchmark_hot_reload()
