# -*- coding: utf-8 -*-
"""
Read-only verification of Grand Master Seal v44 (task 0487, sibling-executed).
NEVER reruns the seal script (it would clobber/drift the manifest).
Checks, purely read-only:
  1. Manifest internal consistency (asset count, field presence).
  2. Merkle root rebuilds from the manifest's stored leaf hashes.
  3. Current on-disk file hashes vs stored leaf hashes (post-seal drift count).
  4. Self-inclusion audit: manifest not in leaves; seal script in leaves (benign).
  5. Gate audit: sibling script gate >=7390 vs task sheet gate >=7400 vs sealed N.
  6. Quine/drift flaw check: manifest path matches collection patterns (rerun drift).
  7. Tamper control: reproduce the audit's claimed tampered root (file-order index 0).
Prints JSON verdict only; writes nothing.
"""

import os
import json
import fnmatch
import hashlib

MANIFEST = "docs/analysis/0487-seal-v44-manifest.json"
SEAL_SCRIPT = "zcode/scripts/seal0487_grand_master_seal_v44.py"
COLLECT_PATTERNS = [
    "configs/**/*", "harness/**/*", "client/**/*", "tools/**/*", "docs/**/*",
    "hourly/**/*", "report/**/*", "question/**/*", "runs/**/*", "zcode/**/*",
    "STATUS.md", "README.md", "PLAN.md", "CONTRIBUTING.md",
    ".gitattributes", ".gitignore", "tests/**/*",
]
TAMPER_SEED = b"modified_bit_v44_integrity_check"  # same seed as v44 script
CLAIMED_TAMPER_ROOT_PREFIX = "9ec54b0f"            # from docs/analysis/0487-theory-audit.md
TASK_GATE = 7400
SCRIPT_GATE = 7390


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
    assets = manifest["assets"]  # dict: normpath -> stored sha256 (insertion = file order)

    n_assets = len(assets)
    stored_leaves = list(assets.values())  # file order preserved by json.load

    # 1. internal consistency
    count_consistent = (n_assets == meta.get("total_assets") ==
                        meta.get("valid_leaf_hashes"))

    # 2. root rebuild from stored leaves
    rebuilt_root, rebuilt_depth = build_merkle_root(stored_leaves)
    root_match = (rebuilt_root == meta.get("merkle_root"))
    depth_match = (rebuilt_depth == meta.get("tree_depth"))

    # 3. on-disk re-verify (read-only)
    missing, mismatched = [], []
    for path, stored in assets.items():
        p = os.path.normpath(path)
        if not os.path.isfile(p):
            missing.append(path)
        else:
            if sha256_file(p) != stored:
                mismatched.append(path)

    # 4. self-inclusion audit
    manifest_self_included = os.path.normpath(MANIFEST) in assets
    script_included = os.path.normpath(SEAL_SCRIPT) in assets

    # 5. gates
    sealed = meta.get("total_assets")
    gates = {
        "sealed_assets": sealed,
        "sibling_script_gate": SCRIPT_GATE,
        "task_sheet_gate": TASK_GATE,
        "passes_script_gate": sealed >= SCRIPT_GATE,
        "passes_task_gate": sealed >= TASK_GATE,
        "task_gate_shortfall": max(0, TASK_GATE - sealed),
    }

    # 6. quine/drift flaw: does the manifest's own path match collection patterns?
    rel_manifest = os.path.normpath(MANIFEST).replace("\\", "/")
    matched_patterns = [p for p in COLLECT_PATTERNS if fnmatch.fnmatch(rel_manifest, p)]
    rerun_drift_flaw = bool(matched_patterns)

    # 7. tamper control (file-order index 0, same seed as v44)
    tampered = list(stored_leaves)
    tampered[0] = hashlib.sha256(TAMPER_SEED).hexdigest()
    tamper_root, _ = build_merkle_root(tampered)
    tamper_reproduces_claim = tamper_root.startswith(CLAIMED_TAMPER_ROOT_PREFIX)

    verdict = {
        "seal": "v44",
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
        "seal_script_included": script_included,
        "gates": gates,
        "manifest_path_matches_patterns": matched_patterns,
        "rerun_drift_flaw_present": rerun_drift_flaw,
        "tamper_root_file_order": tamper_root,
        "tamper_reproduces_audit_claim": tamper_reproduces_claim,
    }
    verdict["internally_consistent"] = bool(
        count_consistent and root_match and depth_match
        and len(missing) == 0 and not manifest_self_included
    )
    print(json.dumps(verdict, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
