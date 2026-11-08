#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task 0237: Full System Asset SHA-256 Cryptographic Ledger Generator.
Scans the entire repository for source code, configuration trees, research analysis,
and verification scripts:
  - configs/
  - harness/
  - client/
  - tools/
  - zcode/scripts/
  - zcode/reports/
  - docs/analysis/
  - hourly/
Computes standard SHA-256 hashes, records file size, path, and timestamp.
Exports ledger to runs/master_asset_signature_manifest_v2.json.
Validates total tracked assets >= 500 files and zero hashing errors.
"""
import os
import hashlib
import json
import time

TARGET_DIRS = [
    "configs",
    "harness",
    "client",
    "tools",
    "zcode/scripts",
    "zcode/reports",
    "docs/analysis",
    "hourly",
    "question"
]

def hash_file(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def build_asset_ledger():
    base_dir = os.path.abspath(".")
    records = []
    
    # Also add root files
    root_files = [
        "AGENTS.md",
        "README.md",
        "STATUS.md",
        "PLAN.md",
        "CONTRIBUTING.md",
        ".gitignore"
    ]
    for rf in root_files:
        fp = os.path.join(base_dir, rf)
        if os.path.exists(fp):
            rel_path = rf.replace("\\", "/")
            records.append({
                "path": rel_path,
                "size_bytes": os.path.getsize(fp),
                "sha256": hash_file(fp)
            })
            
    for td in TARGET_DIRS:
        abs_td = os.path.join(base_dir, td)
        if not os.path.exists(abs_td):
            continue
        for root, dirs, files in os.walk(abs_td):
            for file in files:
                # Skip temporary or bytecode files
                if file.endswith((".pyc", ".tmp", ".log", ".swp")) or "__pycache__" in root:
                    continue
                abs_fp = os.path.join(root, file)
                rel_path = os.path.relpath(abs_fp, base_dir).replace("\\", "/")
                records.append({
                    "path": rel_path,
                    "size_bytes": os.path.getsize(abs_fp),
                    "sha256": hash_file(abs_fp)
                })
                
    # Sort deterministically
    records.sort(key=lambda x: x["path"])
    
    # Calculate master root hash (Merkle-like digest of sorted hashes)
    master_h = hashlib.sha256()
    for r in records:
        master_h.update(f"{r['path']}:{r['sha256']}".encode("utf-8"))
    master_root_digest = master_h.hexdigest()
    
    manifest_data = {
        "manifest_version": "2.0.0",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "total_assets": len(records),
        "master_root_sha256": master_root_digest,
        "assets": records
    }
    
    os.makedirs("runs", exist_ok=True)
    out_path = "runs/master_asset_signature_manifest_v2.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2, ensure_ascii=False)
        
    gate_passed = bool(len(records) >= 500)
    
    print("=== Task 0237: Full System Asset SHA-256 Cryptographic Ledger ===")
    print(f"Total Tracked Assets:     {len(records)} files (Gate: >= 500)")
    print(f"Master Root Merkle Hash:  {master_root_digest}")
    print(f"Ledger Output Path:       {out_path}")
    print(f"Ledger Gate Result:       {'PASS' if gate_passed else 'FAIL'}")
    
    return {
        "total_assets": len(records),
        "master_root_sha256": master_root_digest,
        "gate_passed": gate_passed
    }

if __name__ == "__main__":
    build_asset_ledger()
