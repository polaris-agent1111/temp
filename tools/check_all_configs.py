#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check_all_configs.py — runs/configs/**/pacer.txt 全量格式体检（只读，一条命令重跑）。

检查项（逐文件）:
  1 UTF-8 无 BOM            2 无 \\r（CRLF/孤立CR）     3 无末尾换行
  4 三行结构                5 行首尾无空白              6 timestamp == 目录号
  7 模块白名单 + 参数名/类型/约束（bucket_cap≥leak_rate、burst≥tokens）
  8 字节数 90–120（越界=警告）
  9 leak_interval_us ≥ 4000（越界=警告：官方 4ms 粒度咬合风险，见 0013）
按 tag 聚合:
  10 六目录齐全、每目录恰一个 pacer.txt、无多余文件/子目录
  11 六目录 pacer_config 一致（mix 类 tag 为有意设计 → 记 info）

输出: report/配置全量校验.md（覆盖写）——合格率 + 不合格清单 + 修复建议。
退出码: 0 恒定（体检工具，不因发现错误而失败）。
"""
import os
import re
import sys
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG_DIR = os.path.join(ROOT, "runs", "configs")
OUT = os.path.join(ROOT, "report", "配置全量校验.md")
HARNESS_REGEN = os.path.join(ROOT, "harness", "run_experiment.py")

MODULES = {"token_bucket", "coarse_grained_rate_based", "precise_rate_based",
           "origin", "leak_bucket"}
LEAK_KEYS = {"leak_rate", "bucket_cap", "leak_interval_us"}
TS_RE = re.compile(r"^\[timestamp:(\d+)\]$")
MODE_RE = re.compile(r"^pacer_mode:([A-Za-z0-9_]+)$")
CFG_RE = re.compile(r"^pacer_config:(.*)$")
KV_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)=(-?\d+)$")
DIRS = [str(i) for i in range(1, 7)]


def check_file(path, dir_no):
    """返回 (errors[], warnings[], parsed(dict|None))。"""
    err, warn = [], []
    raw = open(path, "rb").read()
    if raw.startswith(b"\xef\xbb\xbf"):
        err.append("含 UTF-8 BOM")
    if b"\r" in raw:
        err.append("含 \\r（CRLF/孤立CR）")
    if raw.endswith(b"\n"):
        err.append("以换行结尾（应无末尾换行）")
    if not (90 <= len(raw) <= 120):
        warn.append(f"字节数 {len(raw)} 越出 90–120 参考带")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as e:
        err.append(f"非 UTF-8: {e}")
        return err, warn, None
    lines = text.split("\n")
    if len(lines) != 3:
        err.append(f"行数 {len(lines)} ≠ 3")
        return err, warn, None
    for i, ln in enumerate(lines, 1):
        if ln != ln.strip() or ln == "":
            err.append(f"第{i}行行首尾空白/空行: {ln!r}")
    m = TS_RE.match(lines[0])
    if not m:
        err.append(f"第1行非法: {lines[0]!r}")
    elif m.group(1) != dir_no:
        err.append(f"timestamp={m.group(1)} ≠ 目录号 {dir_no}")
    m = MODE_RE.match(lines[1])
    mode = m.group(1) if m else None
    if not mode:
        err.append(f"第2行非法: {lines[1]!r}")
    elif mode not in MODULES:
        err.append(f"未知模块 {mode!r}")
    m = CFG_RE.match(lines[2])
    if not m:
        err.append(f"第3行非法: {lines[2]!r}")
        return err, warn, None
    body = m.group(1)
    params = {}
    if body.strip():
        for tok in body.split(","):
            km = KV_RE.match(tok.strip())
            if not km:
                err.append(f"参数片段非法: {tok!r}")
                continue
            k, v = km.group(1), int(km.group(2))
            if k in params:
                err.append(f"参数重复: {k}")
                continue
            params[k] = v
        if mode == "leak_bucket":
            for k in ("leak_rate", "bucket_cap", "leak_interval_us"):
                if k not in params:
                    err.append(f"leak 缺参数 {k}（无法做安全检查）")
            if "bucket_cap" in params and "leak_rate" in params \
                    and params["bucket_cap"] < params["leak_rate"]:
                err.append(f"bucket_cap({params['bucket_cap']}) < leak_rate({params['leak_rate']})")
            if "leak_interval_us" in params and params["leak_interval_us"] < 4000:
                warn.append(f"leak_interval_us={params['leak_interval_us']} < 4000"
                            f"（官方 4ms 粒度咬合风险，0013）")
        if mode == "token_bucket":
            if "burst" in params and "tokens" in params and params["burst"] < params["tokens"]:
                err.append(f"burst({params['burst']}) < tokens({params['tokens']})")
    return err, warn, {"mode": mode, "params": params, "line3": lines[2]}


def main():
    if not os.path.isdir(CFG_DIR):
        print("runs/configs 不存在")
        return 0

    tags = sorted(d for d in os.listdir(CFG_DIR)
                  if os.path.isdir(os.path.join(CFG_DIR, d)))
    file_stats = Counter()
    file_issues = []          # (relpath, [issues])
    warn_issues = []
    tag_rows = []             # (tag, n_files, n_err_files, mixed, cfg_consistent, notes)
    cfg_variants = 0

    for tag in tags:
        tdir = os.path.join(CFG_DIR, tag)
        entries = sorted(os.listdir(tdir))
        subdirs = [e for e in entries if os.path.isdir(os.path.join(tdir, e))]
        files = [e for e in entries if os.path.isfile(os.path.join(tdir, e))]
        extras = [e for e in files if e != "pacer.txt"]
        missing_dirs = [d for d in DIRS if d not in subdirs]
        tag_err, tag_note = [], []
        if missing_dirs:
            tag_err.append(f"缺子目录 {','.join(missing_dirs)}")
        if extras:
            tag_err.append(f"根级多余文件 {','.join(extras)}")
        if subdirs and set(subdirs) - set(DIRS):
            tag_err.append(f"非法子目录 {','.join(set(subdirs) - set(DIRS))}")
        line3s = {}
        n_err_files = 0
        n_files_here = 0
        for d in DIRS:
            dp = os.path.join(tdir, d)
            if not os.path.isdir(dp):
                continue
            inner = sorted(os.listdir(dp))
            pacer = [f for f in inner if f == "pacer.txt"]
            others = [f for f in inner if f != "pacer.txt"]
            if others:
                tag_err.append(f"目录 {d} 多余文件 {','.join(others)}")
            if not pacer:
                continue
            n_files_here += 1
            rel = os.path.relpath(os.path.join(dp, "pacer.txt"), CFG_DIR).replace(os.sep, "/")
            err, warn, parsed = check_file(os.path.join(dp, "pacer.txt"), d)
            file_stats["files"] += 1
            if err:
                file_stats["err_files"] += 1
                n_err_files += 1
                for e in err:
                    file_issues.append((rel, e))
            else:
                file_stats["ok_files"] += 1
            for w in warn:
                warn_issues.append((rel, w))
            if parsed and parsed.get("line3"):
                line3s[d] = parsed["line3"]
        variants = set(line3s.values())
        consistent = len(variants) <= 1
        if not consistent:
            cfg_variants += 1
            kind = "info(mix 设计)" if "mix" in tag else "warning"
            tag_note.append(f"六目录配置不一致（{len(variants)} 种）[{kind}]")
        tag_rows.append((tag, n_files_here, n_err_files, not subdirs,
                         consistent, tag_err + tag_note))

    total_files = file_stats["files"]
    ok_files = file_stats["ok_files"]
    err_files = file_stats["err_files"]

    L = []
    A = L.append
    A("# 配置快照全量校验（runs/configs/**/pacer.txt）\n")
    A(f"- 生成：`python tools/check_all_configs.py`（一条命令重跑，只读不改）——覆盖 **{len(tags)} 个 tag / {total_files} 个 pacer.txt**")
    A("- 口径：**格式合格** = 无任何 ERROR（结构/编码/timestamp/参数约束）；"
      "**interval 安全** = `leak_interval_us ≥ 4000`（官方 4ms 粒度咬合风险，0013）；"
      "字节数越界与 mix 类不一致记 WARNING/INFO，不算格式不合格。")
    A("")

    A("## 1. 总览\n")
    A("| 指标 | 数值 |")
    A("|---|---|")
    A(f"| tag 数 | {len(tags)} |")
    A(f"| pacer.txt 总数 | {total_files} |")
    A(f"| 格式合格 | **{ok_files}（{ok_files/max(total_files,1)*100:.1f}%）** |")
    A(f"| 格式不合格 | {err_files} |")
    safe = sum(1 for p, w in warn_issues if "leak_interval_us" in w)
    A(f"| 格式合格中 interval<4000（官方咬合风险⚠） | {safe} |")
    A(f"| 六目录配置不一致的 tag | {cfg_variants}（mix 类为有意设计） |")
    A("")

    A("## 2. 不合格清单（ERROR，按问题类型汇总）\n")
    by_issue = Counter(issue for _, issue in file_issues)
    if by_issue:
        A("| 问题 | 文件数 |")
        A("|---|---|")
        for issue, n in by_issue.most_common():
            A(f"| {issue} | {n} |")
        A("")
        A("### 逐文件明细\n")
        cur = None
        for rel, issue in file_issues:
            if rel != cur:
                A(f"- **{rel}**")
                cur = rel
            A(f"  - {issue}")
    else:
        A("（无 ERROR——全部格式合格）")
    A("")

    A("## 3. 警告清单（WARNING：interval 陷阱 / 字节数越界）\n")
    warn_by = Counter(w for _, w in warn_issues)
    if warn_by:
        A("| 警告 | 文件数 |")
        A("|---|---|")
        for w, n in warn_by.most_common():
            A(f"| {w} | {n} |")
        A("")
        bad_int = sorted({rel for rel, w in warn_issues if "leak_interval_us" in w})
        A("<details><summary>interval&lt;4000 全部文件（1ms/2ms/3ms 陷阱族，官方 ×2 风险）</summary>\n")
        for rel in bad_int:
            A(f"- {rel}")
        A("\n</details>")
    else:
        A("（无 WARNING）")
    A("")

    A("## 4. tag 级问题（目录结构 / 一致性）\n")
    bad_tags = [t for t in tag_rows if t[2] or t[5]]
    if bad_tags:
        A("| tag | 文件数 | ERROR 文件数 | 问题 |")
        A("|---|---|---|---|")
        for tag, nf, ne, _, cons, notes in bad_tags:
            A(f"| {tag} | {nf} | {ne} | {'；'.join(notes)} |")
    else:
        A("（所有 tag 目录结构完好）")
    A("")

    regen = "存在（harness/run_experiment.py）" if os.path.exists(HARNESS_REGEN) else "未找到"
    A("## 5. 修复建议（只判断，不改文件）\n")
    A(f"- 再生成工具：{regen}。**整 tag 同因失败**（如整 tag CRLF/整 tag 缺参数）可直接用该 tag 的实验流程重跑生成，"
      "比手改快且不会引入新错；零星单文件问题建议手改后过 `tools/validate_pacer.py`。")
    A("- **优先级**：① `submit-*` 与明日计划相关 tag 必须零 ERROR（投递链路直接使用）；"
      "② 1 ms 陷阱族（leak9/leak8 等）**不要修复成官方推荐**——它们是跨环境差异的证据样本（0017）；"
      "③ 其余历史 tag 修复与否不影响复现结论，仅保持仓库整洁。")
    A("- 本工具只读；任何修复请走原生成流程并重跑本脚本复核。")
    A("")
    A("（本文件由 tools/check_all_configs.py 覆盖生成；重跑：`python tools/check_all_configs.py`）")

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(L) + "\n")
    print(f"[ok] tags={len(tags)} files={total_files} ok={ok_files} err={err_files} "
          f"warn={len(warn_issues)} bad_tags={len(bad_tags)} -> {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
