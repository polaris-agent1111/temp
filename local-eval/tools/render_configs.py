#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把一个 6 目录配置 JSON 渲染成合法的 question/1..6/pacer.txt。

配置 JSON 格式（与历史 runs/*.configs.json 一致）：
{
  "1": ["leak_bucket", {"leak_rate": 40, "bucket_cap": 40, "leak_interval_us": 4000}],
  ...
  "6": ["leak_bucket", {"leak_rate": 36, "bucket_cap": 36, "leak_interval_us": 4000}]
}

输出严格满足官方格式：UTF-8、LF、恰好三行、无末尾换行、timestamp 与目录号一致。

用法：
  python3 tools/render_configs.py --config configs/champion-1108-shot-steady.json --out question
  python3 tools/render_configs.py --config my-candidate.json --out question --print
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# 仅用于让输出顺序稳定、和线上 pacer.txt 一致；未列出的参数按字典序追加。
PREFERRED = {
    "leak_bucket": ["leak_rate", "bucket_cap", "leak_interval_us"],
    "token_bucket": ["tokens", "burst", "token_refill_rate",
                     "token_refill_interval_us", "enable_n_in_flight"],
    "coarse_grained_rate_based": ["max_pacing_rate", "clock_granularity",
                                  "enable_n_in_flight"],
    "precise_rate_based": ["max_pacing_rate", "clock_granularity",
                           "enable_n_in_flight"],
    "origin": ["burst_tokens", "max_pacing_rate", "clock_granularity"],
}


def render_one(n: int, spec) -> str:
    if not isinstance(spec, list) or len(spec) < 1:
        raise ValueError(f"目录 {n}: 配置必须是 [mode, params] 形式")
    mode = str(spec[0])
    params = spec[1] if len(spec) > 1 and spec[1] else {}
    if not isinstance(params, dict):
        raise ValueError(f"目录 {n}: params 必须是对象")
    order = PREFERRED.get(mode, [])
    keys = [k for k in order if k in params]
    keys += sorted(k for k in params if k not in keys)
    body = ",".join(f"{k}={int(params[k])}" for k in keys)
    return f"[timestamp:{n}]\npacer_mode:{mode}\npacer_config:{body}"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="渲染 question/1..6/pacer.txt")
    ap.add_argument("--config", required=True, help="6 目录配置 JSON")
    ap.add_argument("--out", default="question", help="输出根目录（默认 ./question）")
    ap.add_argument("--print", action="store_true", help="同时打印每个文件内容")
    args = ap.parse_args(argv)

    cfg = json.loads(Path(args.config).read_text("utf-8"))
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    for n in range(1, 7):
        key = str(n)
        if key not in cfg:
            raise SystemExit(f"配置缺少目录 {key}")
        text = render_one(n, cfg[key])
        d = out / key
        d.mkdir(parents=True, exist_ok=True)
        path = d / "pacer.txt"
        with open(path, "w", encoding="utf-8", newline="") as fh:
            fh.write(text)  # 注意：不写末尾换行
        if args.print:
            print(f"--- {path} ---")
            print(text)
            print()
    print(f"已写入 {out}/1..6/pacer.txt；请用 tools/validate_pacer.py {out} 校验")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
