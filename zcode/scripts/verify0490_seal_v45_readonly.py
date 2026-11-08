# -*- coding: utf-8 -*-
"""
Read-only verification of Grand Master Seal v45 (task 0490, sibling-executed).
NEVER reruns the seal script (it would clobber/drift the manifest).
Checks:
  1. Manifest internal consistency + Merkle root rebuild from stored leaves.
  2. On-disk re-verification (post-seal drift count, expected: live/post-seal writes).
  3. Self-inclusion audit (v45 manifest absent from leaves; v44 manifest present).
  4. Gate audit: 7477 vs task/script gate 7420; v44-scope equivalent count
     (excluding intel/** and scripts/** which v45 newly added) vs 7420.
  5. Quine/drift flaw check (manifest path matches collection patterns).
  6. Tamper control (file-order index 0, v45 seed).
Prints JSON verdict only; writes nothing.
"""

import os
import json
import fnmatch
import hashlib

MANIFEST = "docs/analysis/0490-seal-v45-manifest.json"
SEAL_SCRIPT = "zcode/scripts/seal0490_grand_master_seal_v45.py"
V44_PATTERNS = [
    "configs/**/*", "harness/**/*", "client/**/*", "tools/**/*", "docs/**/*",
    "hourly/**/*", "report/**/*", "question/**/*", "runs/**/*", "zcode/**/*",
    "STATUS.md", "README.md", "PLAN.md", "CONTRIBUTING.md",
    ".gitattributes", ".gitignore", "tests/**/*",
]
NEW_V45_PATTERNS = ["intel/**/*", "scripts/**/*"]
ALL_PATTERNS = V44_PATTERNS + NEW_V45_PATTERNS
TAMPER_SEED = b"modified_bit_v45_integrity_check"
TASK_GATE = 7420


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def build_merkle_root(leaf_hashes):
    current = sorted(leaf_hashes)
    depth = 1
    while len(current) > 1:
        nxt = []
        for i in range(0, len(current), 2):
            left = current[i]
            right = current[i + 1] if i + 1 < len(current) else left
            nxt.append(hashlib.sha256((left + right).encode("ascii")).hexdigest())
        current = nxt
        depth += 1
    return current[0], depth


def main():
    with open(MANIFEST, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    meta = manifest["meta"]
    assets = manifest["assets"]
    n_assets = len(assets)
    stored_leaves = list(assets.values())

    count_consistent = (n_assets == meta.get("total_assets") ==
                        meta.get("valid_leaf_hashes"))

    rebuilt_root, rebuilt_depth = build_merkle_root(stored_leaves)
    root_match = (rebuilt_root == meta.get("merkle_root"))
    depth_match = (rebuilt_depth == meta.get("tree_depth"))

    missing, mismatched = [], []
    for path, stored in assets.items():
        p = os.path.normpath(path)
        if not os.path.isfile(p):
            missing.append(path)
        elif sha256_file(p) != stored:
            mismatched.append(path)

    manifest_self_included = os.path.normpath(MANIFEST) in assets
    v44_manifest_included = os.path.normpath("docs/analysis/0487-seal-v44-manifest.json") in assets
    script_included = os.path.normpath(SEAL_SCRIPT) in assets

    # scope expansion quantification: assets under the newly added patterns
    newly_added = [p for p in assets
                   if any(fnmatch.fnmatch(p.replace("\\", "/"), pat) for pat in NEW_V45_PATTERNS)]
    v44_scope_equivalent = n_assets - len(newly_added)

    gates = {
        "sealed_assets": n_assets,
        "task_sheet_gate": TASK_GATE,
        "passes_task_gate": n_assets >= TASK_GATE,
        "newly_added_pattern_assets": len(newly_added),
        "v44_scope_equivalent_count": v44_scope_equivalent,
        "v44_scope_would_pass_gate": v44_scope_equivalent >= TASK_GATE,
    }

    rel_manifest = os.path.normpath(MANIFEST).replace("\\", "/")
    matched_patterns = [p for p in ALL_PATTERNS if fnmatch.fnmatch(rel_manifest, p)]
    rerun_drift_flaw = bool(matched_patterns)

    tampered = list(stored_leaves)
    tampered[0] = hashlib.sha256(TAMPER_SEED).hexdigest()
    tamper_root, _ = build_merkle_root(tampered)

    verdict = {
        "seal": "v45",
        "manifest": MANIFEST,
        "count_consistent": count_consistent,
        "root_rebuilt_match": root_match,
        "rebuilt_root": rebuilt_root,
        "claimed_root": meta.get("merkle_root"),
        "depth_match": depth_match,
        "tree_depth": rebuilt_depth,
        "on_disk_missing": len(missing),
        "on_disk_mismatched": len(mismatched),
        "mismatched_paths": mismatched[:10],
        "manifest_self_included": manifest_self_included,
        "v44_manifest_included": v44_manifest_included,
        "seal_script_included": script_included,
        "gates": gates,
        "manifest_path_matches_patterns": matched_patterns,
        "rerun_drift_flaw_present": rerun_drift_flaw,
        "tamper_root_file_order": tamper_root,
        "tamper_differs_from_sealed_root": tamper_root != meta.get("merkle_root"),
    }
    verdict["internally_consistent"] = bool(
        count_consistent and root_match and depth_match
        and len(missing) == 0 and not manifest_self_included
    )
    print(json.dumps(verdict, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
