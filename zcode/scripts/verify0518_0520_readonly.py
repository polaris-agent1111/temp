#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Read-only verification for batch batch_campaign_0700_morning (tasks 0518/0519/0520)
executed by a concurrent sibling session 2026-11-08 06:12-06:16.

- Part A: sandbox re-run of 0518/0519 scripts in a temp dir (outside workspace),
  byte-compare their metrics JSON against the sibling's archived outputs.
- Part B: re-verify Grand Master Seal v55 (zcode/reports/seal0520_manifest_v55.json)
  READ-ONLY: rebuild the seal-time file set (mtime <= seal cutoff), reconstruct the
  3 known post-seal-mutated leaf files byte-exactly (dispatcher.log prefix truncation,
  request 0520 status flip, zcode/STATUS.md template derivation), rebuild the Merkle
  root and compare with the stored root. NEVER re-runs the seal script itself.

Writes NOTHING inside the workspace. Temp artifacts live in a system temp dir.
client/secrets.json is hashed as part of the leaf set but its content is never
read into memory beyond the hash stream and never printed (red-line safe).
"""

import os
import re
import sys
import glob
import json
import shutil
import hashlib
import subprocess
import tempfile
import datetime

WS = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MANIFEST = os.path.join(WS, "zcode", "reports", "seal0520_manifest_v55.json")
STORED_ROOT = "aa42919c833bd4ff1d702dc4b4d7566369d1b018c105471eb5f40f05435c641b"

PATTERNS = [
    "configs/**/*", "harness/**/*", "client/**/*", "tools/**/*", "docs/**/*",
    "hourly/**/*", "report/**/*", "question/**/*", "runs/**/*", "zcode/**/*",
    "STATUS.md", "README.md", "PLAN.md", "CONTRIBUTING.md", "AGENTS.md",
    "HANDOFF.md", ".gitattributes", ".gitignore", "tests/**/*", "intel/**/*",
    "scripts/**/*",
]


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def build_root(leaf_hashes):
    level = list(leaf_hashes)
    depth = 1
    while len(level) > 1:
        nxt = []
        for i in range(0, len(level), 2):
            left = level[i]
            right = level[i + 1] if i + 1 < len(level) else left
            nxt.append(hashlib.sha256((left + right).encode("utf-8")).hexdigest())
        level = nxt
        depth += 1
    return level[0], depth


# ---------------------------------------------------------------- Part A
def sandbox_rerun(tag, script_name):
    tmp = tempfile.mkdtemp(prefix="zc0520_verify_")
    src = os.path.join(WS, "zcode", "scripts", script_name)
    dst = os.path.join(tmp, script_name)
    shutil.copyfile(src, dst)
    proc = subprocess.run(
        [sys.executable, "-I", "-X", "utf8", dst],
        cwd=tmp, capture_output=True, text=True, encoding="utf-8",
        errors="replace", timeout=300,
    )
    out = {
        "returncode": proc.returncode,
        "stdout_tail": proc.stdout.strip().splitlines()[-4:],
        "stderr_tail": proc.stderr.strip().splitlines()[-3:] if proc.returncode else [],
    }
    ws_metrics = os.path.join(WS, "zcode", "reports", f"{tag}_metrics.json")
    tmp_metrics = os.path.join(tmp, "zcode", "reports", f"{tag}_metrics.json")
    if os.path.isfile(tmp_metrics) and os.path.isfile(ws_metrics):
        a = open(tmp_metrics, "rb").read()
        b = open(ws_metrics, "rb").read()
        out["metrics_byte_identical"] = (a == b)
        out["workspace_metrics"] = json.loads(b.decode("utf-8"))
    else:
        out["metrics_byte_identical"] = False
        out["error"] = "sandbox metrics file missing"
    shutil.rmtree(tmp, ignore_errors=True)
    return out


# ---------------------------------------------------------------- Part B
def status_md_variants():
    """Derive the 06:11 board bytes from the CURRENT board template,
    robust to the dispatcher having advanced to any later batch."""
    cur_path = os.path.join(WS, "zcode", "STATUS.md")
    cur = open(cur_path, "rb").read()

    task_map = {
        "1. **`0524`**": "1. **`0518`** — `拓扑量子马尔可夫半群完全正保迹整形策动`",
        "2. **`0525`**": "2. **`0519`** — `随机热力学微观不可逆熵增率与拥塞相变`",
        "3. **`0526`**": "3. **`0520`** — `全局大封印 Grand Master Seal v55 时空密码学签名存证`",
    }
    task_map = {k.encode("utf-8"): v.encode("utf-8") for k, v in task_map.items()}
    item_re = re.compile(r"^\d+\. \*\*`\d{4}`\*\* — ".encode("utf-8"), re.M)
    hits = len(item_re.findall(cur))
    lines = cur.split(b"\r\n")
    slot = 0
    for i, ln in enumerate(lines):
        if item_re.match(ln):
            lines[i] = list(task_map.values())[slot] if slot < 3 else ln
            slot += 1
    derived = b"\r\n".join(lines)
    derived = re.sub(rb"batch_campaign_\d{4}_[a-z]+", b"batch_campaign_0700_morning", derived)
    derived = re.sub(rb"2026-11-08 \d{2}:\d{2}", b"2026-11-08 06:11", derived)

    info = {"board_task_item_lines_found": hits,
            "board_task_lines_replaced": slot,
            "current_board": re.search(rb"batch_campaign_\d{4}_[a-z]+", cur).group(0).decode()}

    # independent transcription (from the 06:12 read of the 0700 board), LF form
    transcription_lf = "\n".join([
        "# zcode 任务看板 — 2026-11-08 06:11 (自动派发批次 batch_campaign_0700_morning)",
        "",
        "更新时间：2026-11-08 06:11 (Asia/Shanghai)  ",
        "维护者：Lead（AI 舵手） ｜ 派发系统：Auto Continuous Dispatcher",
        "",
        "## 关键背景",
        "",
        "- **战略目标**：全力冲击全国第一（Catnet 119.8293s），理论下确界已击穿至 **106.597s**！",
        "- **作战部署**：今晚 11/07 00:05 启动后台守护任务 `tools/sequential_adaptive_night.py`（task-2135），执行「逐发闭环自适应 1-by-1 提交」，打一发看一发，根据真机出分动态调参打满 5 发冲榜。",
        "- **协同分工**：Lead 独占云主机评测、真实提交与闭环调度；**zcode 全力承担重负荷离线数理计算、蒙特卡洛随机碰撞仿真、全量资产与合规红线穿透审计**。",
        "",
        "---",
        "",
        "## 当前需求",
        "",
        "按编号从小到大顺序依次严格执行（任务单均位于 `zcode/requests/`）：",
        "",
        "1. **`0518`** — `拓扑量子马尔可夫半群完全正保迹整形策动`",
        "2. **`0519`** — `随机热力学微观不可逆熵增率与拥塞相变`",
        "3. **`0520`** — `全局大封印 Grand Master Seal v55 时空密码学签名存证`",
        "",
        "---",
        "",
        "## 任务执行须知",
        "",
        "- 请严格遵循 `zcode/README.md` 协议；",
        "- 仅在任务单指定的「允许写的路径」中写入文件；",
        "- 任务完成后在 `zcode/reports/` 写入同名交付报告，并将 `requests/` 中对应的任务单头部 `status: open` 修改为 `status: done`；",
        "- 禁止登录比赛平台、禁止修改真实提交凭据与评测代码。",
    ])
    t_bytes = transcription_lf.encode("utf-8")
    d_norm = derived.replace(b"\r\n", b"\n")
    info["transcription_matches_template"] = (d_norm == t_bytes)
    info["transcription_matches_template_ignoring_trailing_ws"] = (
        b"\n".join(x.rstrip() for x in d_norm.split(b"\n"))
        == b"\n".join(x.rstrip() for x in t_bytes.split(b"\n"))
    )

    variants = {}
    d_crlf = derived
    d_lf = d_norm
    for name, base in (("template_crlf", d_crlf), ("template_lf", d_lf)):
        variants[name] = base
        if not base.endswith(b"\n"):
            variants[name + "_eofnl"] = base + (b"\r\n" if base is d_crlf else b"\n")
    # transcription fallbacks (in case template derivation is wrong)
    variants["transcript_crlf"] = t_bytes.replace(b"\n", b"\r\n")
    variants["transcript_lf"] = t_bytes
    variants["transcript_crlf_notrail"] = t_bytes.replace(b"\n", b"\r\n").replace(
        "(Asia/Shanghai)  \r\n".encode(), "(Asia/Shanghai)\r\n".encode())
    variants["transcript_lf_notrail"] = t_bytes.replace(
        "(Asia/Shanghai)  \n".encode(), "(Asia/Shanghai)\n".encode())
    return variants, info


def reconstruct_dispatcher_log():
    path = os.path.join(WS, "runs", "zcode_dispatcher.log")
    raw = open(path, "rb").read()
    marker = b"[2026-11-08 06:16:34]"
    idx = raw.find(marker)
    if idx < 0:
        return None, {"error": "marker not found"}
    return raw[:idx], {"prefix_bytes": idx, "total_bytes": len(raw),
                       "marker_unique": raw.count(marker) == 1}


def reconstruct_request_0520():
    path = os.path.join(WS, "zcode", "requests",
                        "0520-全局大封印-Grand-Master-Seal-v55-时空密码学签名存证.md")
    raw = open(path, "rb").read()
    assert raw.startswith(b"status: done"), "unexpected request head"
    return raw.replace(b"status: done", b"status: open", 1), {"bytes": len(raw)}


def main():
    report = {"generated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

    # ---- Part A
    report["rerun_0518"] = sandbox_rerun("0518", "qms0518_cptp_pacing_master.py")
    report["rerun_0519"] = sandbox_rerun("0519", "thermo0519_entropy_production.py")

    # ---- Part B
    man = json.load(open(MANIFEST, "r", encoding="utf-8"))
    cutoff = os.path.getmtime(MANIFEST)
    cutoff_dt = datetime.datetime.fromtimestamp(cutoff).strftime("%Y-%m-%d %H:%M:%S.%f")

    files = set()
    for p in PATTERNS:
        for match in glob.glob(os.path.join(WS, p), recursive=True):
            if os.path.isfile(match):
                files.add(os.path.normpath(os.path.relpath(match, WS)))
    all_files = sorted(files)
    manifest_norm = os.path.normpath("zcode/reports/seal0520_manifest_v55.json")
    # 3 pre-existing leaf files mutated AFTER the seal hash pass (known, expected):
    # dispatcher log append, board batch-advance, request 0520 status flip.
    mutated_preexisting = {
        os.path.normpath("runs/zcode_dispatcher.log"),
        os.path.normpath("zcode/STATUS.md"),
        os.path.normpath("zcode/requests/0520-全局大封印-Grand-Master-Seal-v55-时空密码学签名存证.md"),
    }
    seal_set = [f for f in all_files
                if (os.path.getmtime(os.path.join(WS, f)) <= cutoff
                    or f in mutated_preexisting)
                and f != manifest_norm]
    excluded_new = [f for f in all_files
                    if f not in seal_set and f != manifest_norm]
    expected_new_dirs = tuple(os.path.normpath(d) + os.sep for d in (
        "zcode/scripts", "zcode/reports", "zcode/requests", "docs/analysis"))
    late_but_unexplained = [f for f in excluded_new
                            if os.path.getmtime(os.path.join(WS, f)) > cutoff
                            and f not in mutated_preexisting
                            and not f.startswith(expected_new_dirs)]
    report["seal"] = {
        "cutoff": cutoff_dt,
        "current_pattern_files": len(all_files),
        "excluded_new_post_seal": len(excluded_new),
        "seal_set_count": len(seal_set),
        "manifest_asset_count": man["asset_count"],
        "count_match": len(seal_set) == man["asset_count"],
        "late_writes_in_task_dirs_not_new": sorted(late_but_unexplained)[:10],
    }

    # sample-manifest spot check (20 stored hashes vs current files)
    checks = []
    for path, expected in man["sample_manifest"].items():
        fp = os.path.join(WS, path)
        ok = os.path.isfile(fp) and sha256_file(fp) == expected
        checks.append((path, ok))
    report["seal"]["sample_checks"] = {
        "total": len(checks),
        "passed": sum(1 for _, ok in checks if ok),
        "failed": [p for p, ok in checks if not ok],
    }

    # byte-exact reconstructions of the 3 known post-seal mutations
    log_bytes, log_info = reconstruct_dispatcher_log()
    req_bytes, req_info = reconstruct_request_0520()
    status_variants, status_info = status_md_variants()
    report["seal"]["reconstructions"] = {
        "dispatcher_log": log_info,
        "request_0520": req_info,
        "status_md": status_info,
    }
    if log_bytes is None:
        report["seal"]["root_match"] = False
        report["seal"]["root_error"] = "dispatcher.log marker not found"
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return

    norm = os.path.normpath
    req_key = "zcode/requests/0520-全局大封印-Grand-Master-Seal-v55-时空密码学签名存证.md"
    override_base = {
        norm("runs/zcode_dispatcher.log"): sha256_bytes(log_bytes),
        norm(req_key): sha256_bytes(req_bytes),
    }

    # hash all stable files once
    base_hashes = {}
    for f in seal_set:
        if f in override_base:
            continue
        base_hashes[f] = sha256_file(os.path.join(WS, f))

    matched_variant = None
    for name, sbytes in status_variants.items():
        leaves = []
        ov = dict(override_base)
        ov[norm("zcode/STATUS.md")] = sha256_bytes(sbytes)
        for f in seal_set:
            leaves.append(ov[f] if f in ov else base_hashes[f])
        root, depth = build_root(leaves)
        if root == STORED_ROOT:
            matched_variant = {"variant": name, "depth": depth}
            break

    report["seal"]["stored_root"] = STORED_ROOT
    report["seal"]["manifest_tree_depth"] = man["tree_depth"]
    report["seal"]["root_match"] = matched_variant is not None
    if matched_variant:
        report["seal"]["root_match_variant"] = matched_variant

    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
