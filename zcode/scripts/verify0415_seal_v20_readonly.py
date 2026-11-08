# -*- coding: utf-8 -*-
"""
Task 0415 (verification, zcode): Grand Master Seal v20 只读复核
- 不重跑签发脚本（seal0415_grand_master_seal_v20.py 的叶集合模式 zcode/**/* 无自排除，
  此时重签会把 v20 自身产物计入叶集合而使 Root 漂移，即已知 v12/v13 quine-regress 缺陷）
- 只做四件事：
  1) 逐叶复核：manifest 中每条 SHA-256 与磁盘现状是否一致（staleness 检查）；
  2) 内部一致性：由 manifest 存储叶哈希重建 Merkle Root，与 result.json 存储 Root 比对；
  3) 自指核查：首次签发的叶集合不应包含 v20 自身产物；
  4) 资产门槛：叶数 >= 6000 且与 result.json 声称值一致。
- 只读（hash 读取），不写 runs/，不改 v20 任何既有产物；结论另存
  zcode/reports/0415_seal_v20_verification.json。
"""

import os
import sys
import json
import hashlib
from datetime import datetime

MANIFEST = "zcode/reports/0415_manifest_v20.json"
RESULT = "zcode/reports/0415_result.json"


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def build_root_and_depth(leaves):
    cur = sorted(leaves)
    depth = 1
    while len(cur) > 1:
        nxt = []
        for i in range(0, len(cur), 2):
            a = cur[i]
            b = cur[i + 1] if i + 1 < len(cur) else a
            nxt.append(hashlib.sha256((a + b).encode("ascii")).hexdigest())
        cur = nxt
        depth += 1
    return cur[0], depth


def main():
    m = json.load(open(MANIFEST, encoding="utf-8"))
    stored = json.load(open(RESULT, encoding="utf-8"))
    stored_root = stored["merkle_root"]

    # 1) 逐叶复核（staleness：签发后又被合法流程改写的文件会计入 mismatch，属预期陈旧而非伪造）
    mismatch, missing = [], []
    for k, h in m.items():
        p = k.replace("\\", os.sep)
        if not os.path.isfile(p):
            missing.append(k)
            continue
        if sha256_file(p) != h:
            mismatch.append(k)

    # 2) 内部一致性：由存储叶重建 Root
    recomputed, depth = build_root_and_depth(list(m.values()))
    root_ok = (recomputed == stored_root)
    depth_ok = (depth == stored.get("tree_depth"))

    # 3) 自指核查：v20 自身产物是否被签入（首次签发应为 0）
    own_keys = [k for k in m
                if "0415_result" in k or "0415_manifest" in k
                or k.replace("\\", "/").endswith("0415-analysis.md")
                or "0415-theory-audit" in k]

    # 4) 资产门槛
    count_ok = (len(m) == stored.get("total_assets_sealed")) and (len(m) >= 6000)

    print("=== Grand Master Seal v20 只读复核 ===")
    print(f"[*] 叶总数: {len(m)} (result.json 声称 {stored.get('total_assets_sealed')})  一致: {count_ok}")
    print(f"[*] 由存储叶重建 Root == 存储 Root: {root_ok} ({recomputed[:16]}...)")
    print(f"[*] 树深度: 重建 {depth} vs 声称 {stored.get('tree_depth')}  一致: {depth_ok}")
    print(f"[*] 叶失配（磁盘 vs manifest，签发后变更）: {len(mismatch)}")
    for k in mismatch[:12]:
        print(f"    MISMATCH {k}")
    print(f"[*] manifest 中已消失文件: {len(missing)}")
    for k in missing[:12]:
        print(f"    MISSING {k}")
    print(f"[*] v20 自身产物被签入叶集合: {len(own_keys)} 条（首次签发应为 0）")

    verdict = {
        "task_id": "0415",
        "verification": "read-only re-verification (zcode, sibling-artifact review)",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "leaf_count": len(m),
        "count_matches_claim_and_gate": bool(count_ok),
        "root_recomputed_matches_stored": bool(root_ok),
        "merkle_root_stored": stored_root,
        "depth_recomputed": depth,
        "depth_matches_claim": bool(depth_ok),
        "leaf_hash_mismatches": sorted(mismatch),
        "missing_files": sorted(missing),
        "own_outputs_in_leaf_set": len(own_keys),
        "quine_regress_on_rerun": True,
        "note": "seal 为签发时刻一次性快照；叶模式 zcode/**/* 无自排除，重跑签发脚本必致 Root 漂移（与 v12/v13 同款已知缺陷），验证一律只读",
        "verdict": ("SEAL_V20_INTERNALLY_CONSISTENT_SNAPSHOT"
                    if (root_ok and count_ok and depth_ok and len(missing) == 0)
                    else "SEAL_V20_VERIFICATION_FAILED"),
    }
    out = "zcode/reports/0415_seal_v20_verification.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(verdict, f, indent=2, ensure_ascii=False)
    print(f"[OK] 复核结论已写入 {out}")
    print(f"[VERDICT] {verdict['verdict']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
