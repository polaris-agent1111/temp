# -*- coding: utf-8 -*-
"""
Task 0439 (verification, zcode): Grand Master Seal v28 只读复核
- 不重跑签发脚本（seal0439_grand_master_seal_v28.py 的叶集合模式含 zcode/**/* 与 docs/**/*，
  无自排除；此时重签会把 v28 自身产物计入叶集合而使 Root 漂移 —— 与 v12~v20 已知
  quine-regress 缺陷同款，重跑 seal 脚本一律禁止）
- 只做五件事：
  1) 资产门槛：叶数 >= 7150 且与 manifest.meta 声称值一致；
  2) 内部一致性：由 manifest 存储叶哈希重建 Merkle Root / 树深度，与 meta 比对；
  3) 逐叶复核：每条 SHA-256 与磁盘现状是否一致（签发后合法写入的文件计入
     staleness mismatch，属预期陈旧而非篡改）；
  4) 自指核查：首次签发的叶集合不应包含 v28 自身产物；
  5) 篡改雪崩复现：按签发脚本的 tamper 测试（首个排序叶替换为固定摘要）重建
     篡改根，与审计声称值 734f6d32... 前缀比对。
- 只读（hash 读取），不写 runs/，不改 v28 任何既有产物；结论另存
  zcode/reports/0439_seal_v28_verification.json。
"""

import os
import sys
import json
import hashlib
from datetime import datetime

MANIFEST = "docs/analysis/0439-seal-v28-manifest.json"

sys.stdout.reconfigure(encoding="utf-8")


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
    meta = m["meta"]
    assets = m["assets"]
    stored_root = meta["merkle_root"]

    # 1) 资产门槛
    count_ok = (len(assets) == meta["total_assets"]) and (len(assets) >= 7150)

    # 2) 内部一致性：由存储叶重建 Root / 深度
    recomputed, depth = build_root_and_depth(list(assets.values()))
    root_ok = (recomputed == stored_root)
    depth_ok = (depth == meta["tree_depth"])

    # 3) 逐叶复核（staleness）
    mismatch, missing = [], []
    for k, h in assets.items():
        p = k.replace("\\", os.sep)
        if not os.path.isfile(p):
            missing.append(k)
            continue
        if sha256_file(p) != h:
            mismatch.append(k)

    # 4) 自指核查（首次签发应为 0）
    own_keys = [k for k in assets
                if "0439-seal-v28-manifest" in k
                or k.replace("\\", "/").endswith("0439-analysis.md")
                or "0439-theory-audit" in k
                or "seal0439_grand_master_seal_v28" in k
                or "verify0439_seal_v28_readonly" in k]

    # 5) 篡改雪崩复现（与签发脚本严格同构：签发脚本在【文件序】叶列表上替换
    #    index 0，随后 build_merkle_tree 内部才排序 —— 故复现须按 manifest 插入序
    #    （即文件序）替换首叶，而非哈希序）
    leaves_file_order = list(assets.values())  # json.load 保持插入序 = 签发时文件序
    tampered = list(leaves_file_order)
    tampered[0] = hashlib.sha256(b"tampered_bit_v28_grand_master").hexdigest()
    tampered_root, _ = build_root_and_depth(tampered)
    tamper_repro_ok = (tampered_root != stored_root)
    # 审计文档声称的篡改根前缀
    audit_claim_prefix = "734f6d32"
    tamper_prefix_match = tampered_root.startswith(audit_claim_prefix)
    # 对照组：哈希序首叶替换（另一合法但非签发脚本语义的变体）
    leaves_sorted = sorted(assets.values())
    tampered_sorted = list(leaves_sorted)
    tampered_sorted[0] = tampered[0]
    tampered_root_hashorder, _ = build_root_and_depth(tampered_sorted)

    print("=== Grand Master Seal v28 只读复核 ===")
    print(f"[*] 叶总数: {len(assets)} (meta 声称 {meta['total_assets']}, 门槛>=7150)  一致: {count_ok}")
    print(f"[*] 由存储叶重建 Root == 存储 Root: {root_ok} ({recomputed[:16]}...)")
    print(f"[*] 树深度: 重建 {depth} vs 声称 {meta['tree_depth']}  一致: {depth_ok}")
    print(f"[*] 叶失配（磁盘 vs manifest，签发后变更）: {len(mismatch)}")
    for k in mismatch[:15]:
        print(f"    MISMATCH {k}")
    print(f"[*] manifest 中已消失文件: {len(missing)}")
    for k in missing[:15]:
        print(f"    MISSING {k}")
    print(f"[*] v28 自身产物被签入叶集合: {len(own_keys)} 条（首次签发应为 0）")
    for k in own_keys:
        print(f"    SELF {k}")
    print(f"[*] 篡改雪崩复现（文件序首叶，签发脚本语义）: 篡改根 {tampered_root[:16]}... != 原根: {tamper_repro_ok}"
          f"; 与审计声称前缀 {audit_claim_prefix} 一致: {tamper_prefix_match}")
    print(f"    [对照] 哈希序首叶替换篡改根: {tampered_root_hashorder[:16]}...（非签发脚本语义）")

    # 0437/0438 兄弟任务产物是否被签入（provenance 参考）
    siblings_in = [k for k in assets
                   if "0437-theory-audit" in k or "0438-theory-audit" in k]

    verdict = {
        "task_id": "0439",
        "verification": "read-only re-verification (zcode, sibling-artifact review)",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "leaf_count": len(assets),
        "count_matches_claim_and_gate": bool(count_ok),
        "root_recomputed_matches_stored": bool(root_ok),
        "merkle_root_stored": stored_root,
        "depth_recomputed": depth,
        "depth_matches_claim": bool(depth_ok),
        "leaf_hash_mismatches": sorted(mismatch),
        "missing_files": sorted(missing),
        "own_outputs_in_leaf_set": len(own_keys),
        "tamper_avalanche_reproduced": bool(tamper_repro_ok),
        "tamper_root_matches_audit_prefix": bool(tamper_prefix_match),
        "sibling_0437_0438_docs_in_leaf_set": sorted(siblings_in),
        "quine_regress_on_rerun": True,
        "note": "seal 为签发时刻一次性快照；叶模式含 zcode/**/* 与 docs/**/* 无自排除，"
                "重跑签发脚本必致 Root 漂移（与 v12~v20 同款已知缺陷），验证一律只读",
        "verdict": ("SEAL_V28_INTERNALLY_CONSISTENT_SNAPSHOT"
                    if (root_ok and count_ok and depth_ok and len(missing) == 0
                        and tamper_repro_ok and tamper_prefix_match)
                    else "SEAL_V28_VERIFICATION_FAILED"),
    }
    out = "zcode/reports/0439_seal_v28_verification.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(verdict, f, indent=2, ensure_ascii=False)
    print(f"[OK] 复核结论已写入 {out}")
    print(f"[VERDICT] {verdict['verdict']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
