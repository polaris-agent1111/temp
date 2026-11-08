#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""0166: Full Configuration Tree SHA-256 Integrity Verification and Seal.
Audits all 11/08 candidate submission trees against format rules (3 lines, LF, no trailing newline)
and computes cryptographic SHA-256 manifests to prevent tampering.
"""
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

CANDIDATES = [
    {
        "plan_id": "1108-shot-steady-40x3-37-36-36",
        "rates": [40, 40, 40, 37, 36, 36]
    },
    {
        "plan_id": "1108-shot-crown-41x2-40-37-36x2",
        "rates": [41, 41, 40, 37, 36, 36]
    },
    {
        "plan_id": "1108-shot-crown-pert-40on2",
        "rates": [41, 40, 40, 37, 36, 36]
    },
    {
        "plan_id": "1108-shot-fortress-40x4-37x2",
        "rates": [40, 40, 40, 40, 37, 37]
    }
]

def render_pacer_content(step: int, rate: int, cap: int = 40, interval: int = 4000) -> bytes:
    lines = [
        f"[timestamp:{step}]",
        "pacer_mode:leak_bucket",
        f"pacer_config:leak_rate={rate},bucket_cap={cap},leak_interval_us={interval}"
    ]
    return "\n".join(lines).encode("utf-8")

def verify_and_seal_candidates():
    seal_manifest = {}
    validation_results = {}
    
    configs_root = ROOT / "runs" / "sealed_1108_configs"
    configs_root.mkdir(parents=True, exist_ok=True)
    
    for cand in CANDIDATES:
        p_id = cand["plan_id"]
        cand_dir = configs_root / p_id
        cand_dir.mkdir(parents=True, exist_ok=True)
        
        file_hashes = {}
        for step in range(1, 7):
            step_dir = cand_dir / str(step)
            step_dir.mkdir(parents=True, exist_ok=True)
            pacer_path = step_dir / "pacer.txt"
            
            rate = cand["rates"][step - 1]
            cap = max(40, rate)
            raw_bytes = render_pacer_content(step, rate, cap=cap)
            with open(pacer_path, "wb") as f:
                f.write(raw_bytes)
                
            # Compute SHA-256
            h = hashlib.sha256(raw_bytes).hexdigest()
            file_hashes[f"{step}/pacer.txt"] = h
            
            # Format verification: exactly 3 lines, LF, no trailing newline
            lines = raw_bytes.split(b"\n")
            assert len(lines) == 3, f"Must have 3 lines, got {len(lines)}"
            assert not raw_bytes.endswith(b"\n"), "Must not have trailing newline"
            assert b"\r" not in raw_bytes, "Must not contain CR"
            assert lines[0] == f"[timestamp:{step}]".encode("utf-8")
            
        seal_manifest[p_id] = file_hashes
        
        # Run tools/validate_pacer.py on the tree
        val_cmd = [sys.executable, str(ROOT / "tools" / "validate_pacer.py"), str(cand_dir)]
        proc = subprocess.run(val_cmd, capture_output=True, text=True)
        validation_results[p_id] = {
            "exit_code": proc.returncode,
            "stdout": proc.stdout.strip(),
            "valid": proc.returncode == 0
        }
        
    manifest_file = ROOT / "runs" / "sealed_1108_manifest.json"
    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump(seal_manifest, f, indent=2)
        
    all_valid = all(v["valid"] for v in validation_results.values())
    
    results = {
        "manifest_path": str(manifest_file.relative_to(ROOT)),
        "sealed_candidates_count": len(CANDIDATES),
        "all_trees_validated": all_valid,
        "validation_summary": {k: v["valid"] for k, v in validation_results.items()}
    }
    return results

if __name__ == "__main__":
    res = verify_and_seal_candidates()
    print("=== Configuration Tree SHA-256 Sealing Results ===")
    for k, v in res.items():
        print(f"{k}: {v}")
