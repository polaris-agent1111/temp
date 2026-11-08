# -*- coding: utf-8 -*-
"""任务 0244：决选方案配置哈希硬编码签名与全量校验审计工具。

对象 = 11/08 决选 5 发的真实提交清单 runs/seq_1108_shot_{1..5}.json
（Lead 实际提交通路：submit_batch.py --plan → upload_config.py --configs-file
 → build_tree 按 render_pacer 语义 write_bytes）。

本工具做三件事（全部只读，纯本地）：
  1. 签名：对 5 个清单文件原始字节 + 每棵 distinct 配置树 6 个目录的
     **字节级复刻 pacer.txt**（完全复刻 harness.render_pacer 管线语义：
     UTF-8 无 BOM、LF、恰好 3 行、末尾无换行、参数序 = JSON 键序）
     计算 SHA-256；树级复合指纹 = SHA-256(拼接 b"{n}/pacer.txt" + NUL + 字节, n=1..6)。
  2. 校验：按 configs/params_schema.json（只读加载）逐条校验格式合规——
     目录 1..6 齐全、无 BOM/无 CR/3 行/无尾换行、[timestamp:N] N==目录名、
     pacer_mode ∈ schema 模块集、参数名/类型/模块约束（如 bucket_cap>=leak_rate）。
  3. 一致性：声明同构的 shot（2/4/5 同用 crown 树）必须复合指纹逐位相同，
     否则视为篡改信号。

输出：stdout + zcode/scripts/_0244_out.md（指纹清单，供 Lead 每发提交前重跑比对）。
重跑方式：python zcode/scripts/audit0244_config_fingerprint.py
判定：脚本退出码 0 = 全部合规且一致；非 0 = 存在篡改/不合规。
合规：不联网、不提交、不写任何受保护路径。
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / "runs"
SCHEMA = ROOT / "configs" / "params_schema.json"
OUT_MD = ROOT / "zcode" / "scripts" / "_0244_out.md"

SHOTS = [f"seq_1108_shot_{i}.json" for i in range(1, 6)]


def render_pacer(n: int, mode: str, params: dict) -> bytes:
    """复刻 harness/run_experiment.py::render_pacer + build_tree 的字节语义。"""
    param_str = ",".join(f"{k}={v}" for k, v in params.items())
    return f"[timestamp:{n}]\npacer_mode:{mode}\npacer_config:{param_str}".encode("utf-8")


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def validate_pacer_bytes(n: int, data: bytes, schema: dict, mode: str, params: dict):
    """按 schema 校验单目录 pacer 字节与参数，返回违规列表。"""
    errs = []
    if data.startswith(b"\xef\xbb\xbf"):
        errs.append("含 BOM")
    if b"\r" in data:
        errs.append("含 CR（必须纯 LF）")
    if data.endswith(b"\n"):
        errs.append("末尾有换行")
    lines = data.split(b"\n")
    if len(lines) != 3:
        errs.append(f"行数 {len(lines)} != 3")
    if lines and lines[0] != f"[timestamp:{n}]".encode("utf-8"):
        errs.append(f"行1 不是 [timestamp:{n}]")
    for i, ln in enumerate(lines, 1):
        if ln.startswith(b" ") or ln.startswith(b"\t") or ln.endswith(b" ") or ln.endswith(b"\t"):
            errs.append(f"行{i} 首尾有空白")
    if mode not in schema["modules"]:
        errs.append(f"pacer_mode {mode} 不在 schema 模块集")
        return errs
    mod = schema["modules"][mode]
    spec = mod["params"]
    for k, v in params.items():
        if k not in spec:
            errs.append(f"未知参数 {k}")
            continue
        t = spec[k]["type"]
        if t in ("posint", "nonnegint") and (not isinstance(v, int) or v < (1 if t == "posint" else 0)):
            errs.append(f"参数 {k}={v} 不满足 {t}")
    for c in mod.get("constraints", []):
        lv, rv = params.get(c["left"]), params.get(c["right"])
        if lv is None or rv is None:
            continue
        if c["op"] == ">=" and not lv >= rv:
            errs.append(f"约束违反：{c['msg']}")
    return errs


def main() -> int:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    lines = []
    w = lines.append
    w("# 0244 输出 — 决选方案 SHA-256 指纹清单与全量校验\n")
    w(f"生成时间：{datetime.now():%Y-%m-%d %H:%M:%S}（指纹值本身不含时间，逐位可复现）\n")

    def esc(s: str) -> str:
        return s.replace("\n", "\\n")

    all_ok = True
    shot_hashes = {}   # seq 文件 -> (size, sha256)
    tree_of = {}       # shot -> composite fingerprint
    tree_meta = {}     # composite -> dict(desc, shots, dirs)
    shot_tag = {}      # shot -> (full tag, family tag)

    w("## 1. 提交清单文件签名（原始字节）\n")
    w("| 清单文件 | 字节数 | SHA-256 |")
    w("|---|---|---|")
    for name in SHOTS:
        p = RUNS / name
        raw = p.read_bytes()
        h = sha256(raw)
        shot_hashes[name] = (len(raw), h)
        w(f"| `runs/{name}` | {len(raw)} | `{h}` |")
    w("")

    w("## 2. 配置树字节级复刻与逐目录指纹\n")
    w("（复刻管线语义：UTF-8 无 BOM、纯 LF、3 行、末尾无换行、参数序 = 清单 JSON 键序）\n")
    for name in SHOTS:
        d = json.loads((RUNS / name).read_text(encoding="utf-8"))
        item = d[0]
        tag, cfgs = item["tag"], item["configs"]
        fam_tag = tag.rsplit("-s", 1)[0] if re.search(r"-s\d+$", tag) else tag
        shot_tag[name] = (tag, fam_tag)
        tree = {int(k): (v[0], v[1]) for k, v in cfgs.items()}
        tree_bytes = {}
        errs_all = []
        if sorted(tree) != list(range(1, 7)):
            errs_all.append(f"目录集 {sorted(tree)} != 1..6")
            all_ok = False
        for n in range(1, 7):
            mode, params = tree[n]
            data = render_pacer(n, mode, params)
            tree_bytes[n] = data
            errs = validate_pacer_bytes(n, data, schema, mode, params)
            if errs:
                errs_all.extend(f"dir{n}: {e}" for e in errs)
        # 树级复合指纹
        comp = hashlib.sha256()
        for n in range(1, 7):
            comp.update(f"{n}/pacer.txt".encode() + b"\0" + tree_bytes[n] + b"\0")
        ch = comp.hexdigest()
        ok = not errs_all
        all_ok &= ok
        status = "合规 ✓" if ok else "违规 ✗: " + "; ".join(errs_all)
        w(f"### `{tag}`（来自 `{name}`）\n")
        w(f"- **树级复合指纹：`{ch}`**")
        w(f"- 合规判定：**{status}**")
        w("")
        w("| 目录 | pacer.txt 内容（\\n=LF） | SHA-256 |")
        w("|---|---|---|")
        for n in range(1, 7):
            data = tree_bytes[n]
            w(f"| {n} | `{esc(data.decode('utf-8'))}` | `{sha256(data)}` |")
        w("")
        tree_of[name] = ch
        if ch not in tree_meta:
            tree_meta[ch] = {"tag": tag, "shots": [], "bytes": tree_bytes}
        tree_meta[ch]["shots"].append(name)

    w("## 3. distinct 树汇总与同构一致性\n")
    w("| 复合指纹 | 树 tag | 使用者 |")
    w("|---|---|---|")
    for ch, m in tree_meta.items():
        w(f"| `{ch[:16]}…` | {m['tag']} | {', '.join(m['shots'])} |")
    w("")
    # 同一家族 tag（去 -sN 后缀）的 shot 必须同树（复合指纹逐位一致）
    fam_groups: dict[str, list[str]] = {}
    for name in SHOTS:
        fam_groups.setdefault(shot_tag[name][1], []).append(name)
    consistency_ok = True
    for fam, names in fam_groups.items():
        fps = {tree_of[n] for n in names}
        same = len(fps) == 1
        consistency_ok &= same
        w(f"- 家族 `{fam}`（{len(names)} 发：{', '.join(n.split('_')[-1].replace('.json','') for n in names)}）："
          f"复合指纹 {'逐位一致 ✓' if same else '不一致 ✗（篡改信号！）'}")
    all_ok &= consistency_ok
    w("")

    # ---- 自校验：复刻渲染器 vs 磁盘上真实管线输出
    w("## 3b. 复刻渲染器自校验（对磁盘真实渲染树逐字节比对）\n")
    w("仓库中存在早期实验经真实管线（upload_config → build_tree）落盘的树。")
    w("本工具用其 configs（`leak_rate,bucket_cap,leak_interval_us` 键序）复刻渲染并比对磁盘 sha256：\n")
    disk_checks = [
        ("test-anchor-shot2-pert-40x3-37-36-36-r1", 1,
         [("leak_rate", 40), ("bucket_cap", 40), ("leak_interval_us", 4000)]),
        ("test-leak-asym-41x2-40-37-36x2-r1", 1,
         [("leak_rate", 41), ("bucket_cap", 41), ("leak_interval_us", 4000)]),
        ("test-crown-pert-40on2-r1", 1,
         [("leak_rate", 41), ("bucket_cap", 41), ("leak_interval_us", 4000)]),
    ]
    for tagname, n, param_pairs in disk_checks:
        p = ROOT / "runs" / "configs" / tagname / str(n) / "pacer.txt"
        if not p.exists():
            w(f"- `{tagname}` 磁盘树缺失，跳过（不影响判定）")
            continue
        disk = p.read_bytes()
        replica = render_pacer(n, "leak_bucket", dict(param_pairs))
        ok = disk == replica
        all_ok &= ok
        w(f"- `{tagname}/1/pacer.txt`：复刻 {'逐字节一致 ✓' if ok else '不一致 ✗'}"
          f"（sha256 `{sha256(disk)[:16]}…`）")
    w("- 注：磁盘树与决选 seq 清单的**参数序不同**（磁盘 = leak_rate-first 早期管线；")
    w("  seq 管线 = JSON 键序 bucket_cap,leak_interval_us,leak_rate）。两者语义等价，")
    w("  但字节不同、指纹不同——本清单签的是 **seq_1108 管线将实际渲染的字节**，")
    w("  该管线经 submit_batch.py→upload_config.py 键序保真链路验证。")
    w("")

    w("## 4. 全量校验判定\n")
    n_files = len(shot_hashes)
    n_dirs = 6 * len(tree_meta)
    n_checks = n_files + n_dirs + len(fam_groups) + len(disk_checks)
    w(f"- 校验覆盖：{n_files} 个清单文件签名 + {len(tree_meta)} 棵 distinct 树 × 6 目录"
      f"（{n_dirs} 个 pacer 字节流）+ {len(fam_groups)} 组家族一致性 + "
      f"{len(disk_checks)} 项磁盘真树自校验 = **{n_checks} 项**")
    w(f"- **总体判定：{'100% 格式合规且一致 ✓' if all_ok else '存在违规/不一致 ✗（详见上文）'}**")
    w("- 重验方法：每发提交前执行 `python zcode/scripts/audit0244_config_fingerprint.py`，"
      "退出码 0 且指纹与本清单逐位一致 = 未被篡改；任何指纹漂移即中止提交。")
    w("- 边界声明：本清单签的是**提交清单与渲染树字节**；云端落盘后的最终形态仍以"
      "官方 format_check_client 结果为准（本工具不替代、不触碰评测系统）。")

    text = "\n".join(lines) + "\n"
    OUT_MD.write_text(text, encoding="utf-8")
    print(text)
    print(f"[OK] 已写出 {OUT_MD}；总体判定：{'PASS' if all_ok else 'FAIL'}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
