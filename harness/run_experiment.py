#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""iDSN 实验编排：生成 pacer 配置 -> 上传云主机 -> 本地评测 -> 拉回结果 -> 落盘。

重要经验（实测）：
- 评测启动 containernet 会短暂打断到云主机的 WebSSH 连接，所以**不能在评测期间保持长连接**；
  采用「短连接轮询」：开始评测后断开，之后每隔一段时间新建连接查 DONE。
- 无效跑识别：下载耗时低于链路物理下限（630MB/12.5MB/s ≈ 50s；单文件同理）说明下载失败被误判成功。

用法：
  python harness/run_experiment.py --tag base --note "默认"                 # 空配置
  python harness/run_experiment.py --tag p1 --mode origin --params "burst_tokens=100"
  python harness/run_experiment.py --tag p2 --configs-file cfg.json --repeat 2
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import tarfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "client"))
from vmssh import VmShell  # noqa: E402

RESULTS = ROOT / "runs" / "results.jsonl"
EVALS = ROOT / "runs" / "evals"
CONFIGS = ROOT / "runs" / "configs"
VM_QUESTION = "/home/openlab/Desktop/question"
VM_TMP = "/home/openlab"
SIZES_MB = {"1.bin": 10, "2.bin": 20, "3.bin": 40, "4.bin": 80, "5.bin": 160, "6.bin": 320}
LINK_MBPS = 100.0  # 瓶颈链路 100 Mbps = 12.5 MB/s


def connect_vm(retries: int = 8, wait: float = 8) -> VmShell:
    last = None
    for i in range(retries):
        try:
            vm = VmShell()
            vm.connect()
            return vm
        except Exception as exc:  # noqa: BLE001
            last = exc
            time.sleep(wait * (i + 1))
    raise RuntimeError(f"无法连接云主机: {last}")


def render_pacer(n: int, mode: str, params: dict | None) -> str:
    """生成 pacer.txt 内容。【重要】末尾不能有换行——带末尾换行会让运行时段解析失败（实测跑批全挂）。"""
    param_str = ",".join(f"{k}={v}" for k, v in (params or {}).items())
    return f"[timestamp:{n}]\npacer_mode:{mode}\npacer_config:{param_str}"


def build_tree(tag: str, per_dir: dict[int, tuple[str, dict] | None]) -> Path:
    base = CONFIGS / tag
    if base.exists():
        shutil.rmtree(base)
    base.mkdir(parents=True, exist_ok=True)
    for n in range(1, 7):
        (base / str(n)).mkdir(parents=True, exist_ok=True)
        cfg = per_dir.get(n)
        if cfg:
            mode, params = cfg
            # 必须用 write_bytes：Windows 下 write_text 会把 \n 转成 \r\n，而服务端解析器会因此失败
            (base / str(n) / "pacer.txt").write_bytes(render_pacer(n, mode, params).encode("utf-8"))
    return base


def make_tar(tree: Path, tag: str) -> Path:
    tar_path = CONFIGS / f"{tag}.tar.gz"
    with tarfile.open(tar_path, "w:gz") as tf:
        for n in range(1, 7):
            p = tree / str(n) / "pacer.txt"
            if p.exists():
                tf.add(p, arcname=f"{n}/pacer.txt")
    return tar_path


def validate(downloads: dict[str, float], total: float) -> list[str]:
    bad = []
    for fn, sec in downloads.items():
        floor = SIZES_MB[fn] / (LINK_MBPS / 8) * 0.9
        if sec < floor:
            bad.append(f"{fn}={sec:.2f}s<{floor:.1f}s")
    floor_total = sum(SIZES_MB.values()) / (LINK_MBPS / 8) * 0.9
    if total < floor_total:
        bad.append(f"total={total:.1f}s<{floor_total:.1f}s")
    return bad


def config_desc(per_dir: dict[int, tuple[str, dict]]) -> dict:
    out = {}
    for n in range(1, 7):
        cfg = per_dir.get(n)
        out[str(n)] = (cfg[0] + ":" + ",".join(f"{k}={v}" for k, v in (cfg[1] or {}).items())) if cfg else "(inherit/default)"
    return out


def run_one(tag: str, per_dir: dict[int, tuple[str, dict]], note: str, timeout: float,
            poll: float, from_tree: Path | None = None) -> dict:
    tree = Path(from_tree) if from_tree else build_tree(tag, per_dir)
    tar_path = make_tar(tree, tag)
    print(f"[config] {tree}", flush=True)
    for n in range(1, 7):
        if per_dir.get(n):
            mode, params = per_dir[n]
            print(f"  dir{n}: {render_pacer(n, mode, params).strip()}", flush=True)

    # ---- 阶段 A：上传 + 格式检查 + 启动（短连接）----
    vm = connect_vm()
    try:
        vm.run(f"rm -f {VM_TMP}/cfg_{tag}.tar.gz", timeout=60)
        vm.push_file(tar_path, f"{VM_TMP}/cfg_{tag}.tar.gz")
        code, out = vm.run(
            f"cd {VM_QUESTION} && find . -name pacer.txt -delete && "
            f"tar xzf {VM_TMP}/cfg_{tag}.tar.gz -C {VM_QUESTION} && "
            f"find . -name pacer.txt | sort", timeout=120)
        if code != 0:
            raise RuntimeError(f"上传配置失败: {out[:300]}")
        code, out = vm.run("cd /home/openlab/Desktop && ./format_check_client 2>&1 | tail -8",
                           timeout=120)
        if "检查结果: 通过" not in out:
            raise RuntimeError(f"格式检查未通过:\n{out[:600]}")
        code, out = vm.run(f"bash /home/openlab/vm_run_detached.sh {tag}", timeout=120)
        print(f"[start] {out.strip()}", flush=True)
    finally:
        vm.close()

    # ---- 阶段 B：短连接轮询（评测会打断连接，失败就重连）----
    t0 = time.time()
    done = False
    while time.time() - t0 < timeout:
        time.sleep(poll)
        try:
            vm = connect_vm(retries=3, wait=5)
            try:
                code, out = vm.run(
                    f"cat /home/openlab/evals/{tag}/RC 2>/dev/null; "
                    f"test -f /home/openlab/evals/{tag}/DONE && echo DSHDONE", timeout=60)
            finally:
                vm.close()
        except Exception as exc:  # noqa: BLE001
            print(f"[poll] 连接失败，稍后重试: {str(exc)[:80]}", flush=True)
            continue
        if "DSHDONE" in out:
            done = True
            break
        print(f"[poll] {int(time.time() - t0)}s 仍在评测…", flush=True)
    if not done:
        raise RuntimeError("评测超时")

    # ---- 阶段 C：拉结果 ----
    EVALS.mkdir(parents=True, exist_ok=True)
    local_json = EVALS / f"{tag}.json"
    last_err = None
    for attempt in range(6):
        try:
            vm = connect_vm(retries=3, wait=5)
            try:
                vm.pull_file(f"/home/openlab/evals/{tag}/result.json", local_json)
                vm.pull_file(f"/home/openlab/evals/{tag}/run.log", EVALS / f"{tag}.log")
            finally:
                vm.close()
            break
        except Exception as exc:  # noqa: BLE001
            last_err = exc
            time.sleep(5)
    else:
        raise RuntimeError(f"拉取结果失败: {last_err}")

    data = json.loads(local_json.read_text("utf-8"))
    q = data["question"][0]
    downloads = {d["filename"]: d["seconds"] for d in q["downloads"]}
    bad = validate(downloads, q["total_seconds"])
    rec = {
        "at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "tag": tag,
        "note": note,
        "config": config_desc(per_dir),
        "total_seconds": q["total_seconds"],
        "downloads": downloads,
        "valid": not bad,
        "invalid_reason": "; ".join(bad),
        "wall_seconds": round(time.time() - t0, 1),
    }
    RESULTS.parent.mkdir(parents=True, exist_ok=True)
    with RESULTS.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    flag = "OK" if not bad else f"INVALID({rec['invalid_reason']})"
    print(f"[result] tag={tag} total={q['total_seconds']:.3f}s {flag} downloads={downloads}",
          flush=True)
    return rec


def run_experiment(tag: str, per_dir: dict[int, tuple[str, dict]], note: str = "",
                   timeout: float = 900, poll: float = 20, dry_run: bool = False,
                   repeat: int = 1, from_tree: Path | None = None) -> dict:
    if dry_run:
        tree = build_tree(tag, per_dir)
        print(f"[dry-run] {tree}", flush=True)
        return {"dry_run": True}
    results = []
    for idx in range(1, repeat + 1):
        run_tag = tag if repeat == 1 else f"{tag}-r{idx}"
        results.append(run_one(run_tag, per_dir, note, timeout, poll, from_tree=from_tree))
    return results[-1]


def parse_uniform(pairs: list[str]) -> dict:
    params = {}
    for item in pairs:
        k, v = item.split("=", 1)
        params[k.strip()] = v.strip()
    return params


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", required=True)
    ap.add_argument("--mode")
    ap.add_argument("--params", nargs="*", default=[])
    ap.add_argument("--configs-file")
    ap.add_argument("--note", default="")
    ap.add_argument("--timeout", type=float, default=900)
    ap.add_argument("--poll", type=float, default=20)
    ap.add_argument("--repeat", type=int, default=1)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)

    if args.configs_file:
        raw = json.loads(Path(args.configs_file).read_text("utf-8"))
        per_dir = {int(k): (v[0], v[1] if len(v) > 1 and v[1] else {}) for k, v in raw.items()}
    elif args.mode:
        per_dir = {n: (args.mode, parse_uniform(args.params)) for n in range(1, 7)}
    else:
        per_dir = {}
    run_experiment(args.tag, per_dir, note=args.note, timeout=args.timeout, poll=args.poll,
                   dry_run=args.dry_run, repeat=args.repeat)
    return 0


if __name__ == "__main__":
    sys.exit(main())
