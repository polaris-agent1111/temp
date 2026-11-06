#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""在云主机上探测 pacer.txt 的格式边界。

这是一个手动 VM 脚本，不是单元测试：
- 只调用本地 `format_check_client`，不调用 `local_send_client`，不消耗提交额度；
- 测试前备份 `question/`，结束后恢复，避免把测试配置留在提交目录；
- pacer.txt 必须和生产路径一致：三行、LF、无末尾换行。
"""
from __future__ import annotations

import argparse
import shlex
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "client"))
try:
    from vmssh import VmShell
except Exception:  # 离线导入时允许缺依赖，便于单测只调用 render_pacer
    VmShell = None

QUESTION = "/home/openlab/Desktop/question"
TEST_DIR = "/home/openlab/evals/test_fmt"
BACKUP = "/home/openlab/evals/question_backup"


def render_pacer(n: int, mode: str, cfg_text: str) -> str:
    """与 harness/run_experiment.render_pacer 一致：三行、无末尾换行。"""
    return f"[timestamp:{n}]\npacer_mode:{mode}\npacer_config:{cfg_text}"


def write_command(mode: str, cfg_text: str) -> str:
    parts = []
    for n in range(1, 7):
        directory = f"{TEST_DIR}/{n}"
        path = f"{directory}/pacer.txt"
        parts.append(f"mkdir -p {shlex.quote(directory)}")
        parts.append(f"printf '%s' {shlex.quote(render_pacer(n, mode, cfg_text))} > {shlex.quote(path)}")
    return " && ".join(parts)


def check_cfg(vm, mode: str, cfg_text: str) -> tuple[bool, str]:
    cmd = (
        f"{write_command(mode, cfg_text)} && "
        f"cp -a {TEST_DIR}/. {QUESTION}/ && "
        "cd /home/openlab/Desktop && ./format_check_client 2>&1 | tail -8"
    )
    code, out = vm.run(cmd, timeout=60)
    lines = [line.strip() for line in out.strip().splitlines() if line.strip()]
    return ("检查结果: 通过" in out), (lines[-1] if lines else "")


def backup_question(vm) -> None:
    code, out = vm.run(
        "mkdir -p /home/openlab/evals && "
        f"rm -rf {shlex.quote(BACKUP)} && cp -a {QUESTION} {shlex.quote(BACKUP)}",
        timeout=60,
    )
    if code != 0:
        raise RuntimeError(f"备份 question/ 失败: {out[-300:]}")


def restore_question(vm) -> None:
    vm.run(
        f"rm -rf {QUESTION} && cp -a {shlex.quote(BACKUP)} {QUESTION}",
        timeout=60,
    )


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--keep", action="store_true", help="结束后不恢复 question/（调试用）")
    args = ap.parse_args(argv)

    if VmShell is None:
        raise SystemExit("vmssh 不可用：请先安装依赖并在云主机环境运行")

    tests = [
        ("token_bucket", "tokens=50,burst=50,token_refill_rate=50,token_refill_interval_us=4000,enable_n_in_flight=1"),
        ("token_bucket", "tokens=60,burst=60,token_refill_rate=60,token_refill_interval_us=4000,enable_n_in_flight=1"),
        ("token_bucket", "tokens=40,burst=40,token_refill_rate=10,token_refill_interval_us=1000,enable_n_in_flight=1"),
        ("token_bucket", "tokens=100,burst=100,token_refill_rate=100,token_refill_interval_us=4000,enable_n_in_flight=1"),
        ("precise_rate_based", "max_pacing_rate=12500000,clock_granularity=2000,enable_n_in_flight=1"),
        ("precise_rate_based", "max_pacing_rate=12500000,clock_granularity=1000,enable_n_in_flight=0"),
        ("precise_rate_based", "max_pacing_rate=12000000,clock_granularity=1000,enable_n_in_flight=1"),
        ("precise_rate_based", "max_pacing_rate=11800000,clock_granularity=1000,enable_n_in_flight=1"),
        ("precise_rate_based", "max_pacing_rate=11600000,clock_granularity=1000,enable_n_in_flight=1"),
        ("precise_rate_based", "max_pacing_rate=13000000,clock_granularity=1000,enable_n_in_flight=1"),
        ("coarse_grained_rate_based", "max_pacing_rate=12500000,clock_granularity=1000,enable_n_in_flight=1"),
        ("origin", "burst_tokens=50,max_pacing_rate=12000000,clock_granularity=1000"),
    ]

    vm = VmShell()
    vm.connect()
    passed = 0
    backed_up = False
    try:
        backup_question(vm)
        backed_up = True
        print(f"[backup] {QUESTION} -> {BACKUP}")
        for mode, cfg in tests:
            ok, last = check_cfg(vm, mode, cfg)
            passed += int(ok)
            print(f"[{'PASS' if ok else 'FAIL'}] {mode:25} -> {cfg} | {last}")
    finally:
        if backed_up and not args.keep:
            restore_question(vm)
            print(f"[restore] {BACKUP} -> {QUESTION}")
        vm.close()

    print(f"\n[summary] {passed}/{len(tests)} passed")
    return 0 if passed == len(tests) else 1


if __name__ == "__main__":
    raise SystemExit(main())
