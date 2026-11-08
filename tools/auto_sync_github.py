#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""自动同步仓库信息与代码到 GitHub origin/main。

支持单次同步与常驻循环定时同步（默认 3600 秒/1小时）。
"""
from __future__ import annotations

import argparse
import datetime as dt
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# 严格过滤的敏感词列表
SENSITIVE_WORDS = ["secret", "token.json", "cookie", ".key", ".pem", "credentials", "password"]


def check_sensitive_files(status_lines: list[str]) -> list[str]:
    hits = []
    for line in status_lines:
        fn = line[3:].strip().strip('"').lower()
        for kw in SENSITIVE_WORDS:
            if kw in fn:
                hits.append(fn)
    return hits


def sync_once() -> bool:
    print(f"[{dt.datetime.now():%Y-%m-%d %H:%M:%S}] 检查仓库变动...", flush=True)
    res = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"[ERR] git status 失败: {res.stderr}", file=sys.stderr)
        return False

    lines = [l for l in res.stdout.splitlines() if l.strip()]
    if not lines:
        print("[OK] 工作区干净，无需同步。", flush=True)
        return True

    print(f"检测到 {len(lines)} 个文件变动，执行安全扫描...", flush=True)
    hits = check_sensitive_files(lines)
    if hits:
        print(f"[BLOCK] 拦截到敏感文件变动，拒绝自动提交: {hits}", file=sys.stderr)
        return False

    # 添加所有变动
    add_res = subprocess.run(["git", "add", "."], cwd=ROOT)
    if add_res.returncode != 0:
        print("[ERR] git add 失败", file=sys.stderr)
        return False

    now_str = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    commit_msg = f"chore: 自动同步项目资产与进展 ({now_str})"
    c_res = subprocess.run(["git", "commit", "-m", commit_msg], cwd=ROOT)
    if c_res.returncode != 0:
        print("[WARN] git commit 未产生新提交", flush=True)
        return True

    print(f"[{dt.datetime.now():%Y-%m-%d %H:%M:%S}] 推送至 GitHub origin/main...", flush=True)
    p_res = subprocess.run(["git", "push", "origin", "main"], cwd=ROOT)
    if p_res.returncode != 0:
        print(f"[ERR] git push 失败", file=sys.stderr)
        return False

    print(f"[{dt.datetime.now():%Y-%m-%d %H:%M:%S}] 同步成功！", flush=True)
    return True


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="自动同步仓库至 GitHub")
    ap.add_argument("--loop", action="store_true", help="常驻循环运行")
    ap.add_argument("--interval", type=int, default=3600, help="循环间隔秒数，默认 3600 秒 (1小时)")
    args = ap.parse_args(argv)

    if not args.loop:
        return 0 if sync_once() else 1

    print(f"[DAEMON] 启动每 {args.interval} 秒自动同步守护进程...", flush=True)
    while True:
        try:
            sync_once()
        except Exception as e:
            print(f"[EXC] 异常: {e}", file=sys.stderr)
        time.sleep(args.interval)


if __name__ == "__main__":
    raise SystemExit(main())
