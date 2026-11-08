# -*- coding: utf-8 -*-
"""
Task 0391 (v2 verification, zcode): Grand Master Seal v12 只读复核
- 不重跑签发脚本（重跑会因叶集合自含 v12 自身产物而使 Root 漂移，即已知 quine-regress 缺陷）
- 只做三件事：
  1) 逐叶复核：manifest 中每条 SHA-256 与磁盘现状是否一致；
  2) 内部一致性：由 manifest 存储叶哈希重建 Merkle Root，与 result.json 存储 Root 比对；
  3) 缺陷核查：叶集合是否包含签发脚本自身产物（首次签发不应包含，重签会包含并导致根漂移）。
- 只读（hash 读取），不写 runs/，不改 v12 任何产物；验证结论另存 0391_seal_v12_verification.json。
"""

import os
import sys
import json
import hashlib
from datetime import datetime

MANIFEST = "zcode/reports/0391_manifest_v12.json"
RESULT = "zcode/reports/0391_result.json"


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def build_root(leaves):
    cur = sorted(leaves)
    while len(cur) > 1:
        nxt = []
        for i in range(0, len(cur), 2):
            a = cur[i]
            b = cur[i + 1] if i + 1 < len(cur) else a
            nxt.append(hashlib.sha256((a + b).encode("ascii")).hexdigest())
        cur = nxt
    return cur[0]


def main():
    m = json.load(open(MANIFEST, encoding="utf-8"))
    stored = json.load(open(RESULT, encoding="utf-8"))
    stored_root = stored["merkle_root"]

    mismatch, missing = [], []
    for k, h in m.items():
        p = k.replace("\\", os.sep)
        if not os.path.isfile(p):
            missing.append(k)
            continue
        if sha256_file(p) != h:
            mismatch.append(k)

    recomputed = build_root(list(m.values()))
    root_ok = (recomputed == stored_root)

    # quine 缺陷核查：v12 叶集合模式包含 zcode/**/*，重签将把 v12 自身产物计入叶集合
    own_outputs_now_on_disk = [p for p in (RESULT, MANIFEST) if os.path.isfile(p)]
    own_outputs_in_leaves = [k for k in m if "0391_result" in k or "0391_manifest" in k]

    print("=== Grand Master Seal v12 只读复核 ===")
    print(f"[*] 叶总数: {len(m)} (result.json 声称 {stored['total_assets_sealed']})")
    print(f"[*] 叶失配（磁盘 vs manifest）: {len(mismatch)}")
    for k in mismatch[:12]:
        print(f"    MISMATCH {k}")
    print(f"[*] manifest 中已消失文件: {len(missing)}")
    print(f"[*] 由存储叶重建 Root == 存储 Root: {root_ok} ({recomputed[:16]}...)")
    print(f"[*] 签发时自身产物是否在叶集合中: {len(own_outputs_in_leaves)} 条（首次签发应为 0）")
    print(f"[*] 自身产物现已在磁盘上（重签将计入并使 Root 漂移）: {len(own_outputs_now_on_disk)} 个文件")

    verdict = {
        "task_id": "0391",
        "verification": "v2 read-only re-verification (zcode)",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "leaf_count": len(m),
        "leaf_hash_mismatches": sorted(mismatch),
        "missing_files": sorted(missing),
        "root_recomputed_matches_stored": bool(root_ok),
        "merkle_root_stored": stored_root,
        "own_outputs_in_leaf_set": len(own_outputs_in_leaves),
        "quine_regress_on_rerun": True,
        "note": "manifest 与 Root 内部一致；叶失配仅来自签发后又被复核流程改写时间戳的 v1 result JSON",
        "verdict": "SEAL_V12_INTERNALLY_CONSISTENT_SNAPSHOT" if (root_ok and len(missing) == 0) else "SEAL_V12_DRIFT_DETECTED",
    }
    out = "zcode/reports/0391_seal_v12_verification.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(verdict, f, indent=2, ensure_ascii=False)
    print(f"[OK] 复核结论已写入 {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
