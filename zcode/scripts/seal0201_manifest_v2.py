#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task 0201: Cryptographic SHA-256 sealed manifest v2 for all 5 shot candidate trees.
Scans all 30 pacer.txt files across candidate configs, computes SHA-256, verifies format compliance,
and seals the immutable manifest at runs/sha256_sealed_manifest_v2.json.
"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNS_CONFIGS = ROOT / "runs" / "configs"
MANIFEST_FILE = ROOT / "runs" / "sha256_sealed_manifest_v2.json"
VALIDATOR = ROOT / "tools" / "validate_pacer.py"

def compute_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def seal_manifest():
    configs = [
        "1108-A1-hybrid-champ-90M-96M",
        "1108-A2-hybrid-champ-96M-both",
        "test-leak-asym-41x2-40-37-36x2-r1",
        "test-leak-asym-40x3-37-37-36-r1",
        "leakc-36-40-4000"
    ]
    
    manifest = {
        "title": "11/08 Campaign Cryptographic Configuration Seal Manifest v2",
        "generated_at": "2026-11-07 14:28:00",
        "total_configs": len(configs),
        "total_files": len(configs) * 6,
        "configs": {}
    }
    
    all_valid = True
    for cfg in configs:
        cfg_dir = RUNS_CONFIGS / cfg
        if not cfg_dir.exists():
            print(f"Error: Directory {cfg_dir} not found!")
            all_valid = False
            continue
            
        # Validate format with tools/validate_pacer.py
        proc = subprocess.run([sys.executable, str(VALIDATOR), str(cfg_dir)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        is_valid = (proc.returncode == 0)
        if not is_valid:
            print(f"Validation FAILED for {cfg}:\n{proc.stdout}")
            all_valid = False
            
        cfg_info = {
            "valid": is_valid,
            "bins": {}
        }
        
        for b in range(1, 7):
            pacer_path = cfg_dir / str(b) / "pacer.txt"
            with open(pacer_path, "rb") as f:
                content = f.read()
            h = compute_sha256(content)
            cfg_info["bins"][str(b)] = {
                "sha256": h,
                "bytes": len(content),
                "preview": content.decode("utf-8").split("\n")
            }
            
        manifest["configs"][cfg] = cfg_info
        
    manifest["all_verified_valid"] = all_valid
    
    with open(MANIFEST_FILE, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
        
    print("=== Task 0201: Cryptographic Manifest v2 Generated ===")
    print(f"manifest_path: {MANIFEST_FILE}")
    print(f"configs_sealed: {len(configs)}")
    print(f"total_pacer_files: {len(configs) * 6}")
    print(f"all_verified_valid: {all_valid}")
    
    return manifest

if __name__ == "__main__":
    seal_manifest()
