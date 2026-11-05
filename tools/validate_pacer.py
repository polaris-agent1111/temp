#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""validate_pacer.py — pacer.txt 本地校验器 (标准库, 无外部依赖)

用法:
    python tools/validate_pacer.py <question目录> [--json]
    python tools/validate_pacer.py --selftest [--json]

检查项 (一次列全, 全部通过才 exit 0):
 1. question/ 必须恰有子目录 1..6 (不允许多/少; 根级多余文件也报错)
 2. 每个子目录至多一个普通文件 pacer.txt (不允许子目录/其它文件)
 3. pacer.txt 必须 UTF-8、LF 换行、无 CRLF、无末尾换行 (报错, 非警告)
 4. 恰好三行, 顺序 [timestamp:N] / pacer_mode:<模块> / pacer_config:k=v,... (行首尾无空白)
 5. N 必须等于目录名
 6. 模块名必须属于五选一
 7. 参数名必须属于该模块; 类型/范围/模块内约束 (burst>=tokens, bucket_cap>=leak_rate) 合法
 8. 允许 pacer_config: 后为空 (用模块默认); 允许整个子目录不放文件

退出码: 0=全通过, 1=有错误。
"""
import argparse
import json
import os
import re
import sys
import tempfile

SCHEMA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                           "configs", "params_schema.json")
DIRS = [str(i) for i in range(1, 7)]
TS_RE = re.compile(r"^\[timestamp:(\d+)\]$")
MODE_RE = re.compile(r"^pacer_mode:([A-Za-z0-9_]+)$")
CFG_RE = re.compile(r"^pacer_config:(.*)$")
PARAM_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)=(-?\d+)$")


def load_schema():
    with open(SCHEMA_PATH, encoding="utf-8") as fh:
        return json.load(fh)


class Report:
    def __init__(self):
        self.errors = []   # list[dict(check, path, msg)]

    def err(self, check, path, msg):
        self.errors.append({"check": check, "path": path, "msg": msg})


def check_question_tree(qdir, rep):
    """检查项 1、2: 目录结构。返回 {dir: pacer_path 或 None}。"""
    if not os.path.isdir(qdir):
        rep.err(1, qdir, "question 目录不存在")
        return {}
    found = {}
    entries = sorted(os.listdir(qdir))
    subdirs, other = [], []
    for name in entries:
        p = os.path.join(qdir, name)
        if os.path.isdir(p):
            subdirs.append(name)
        else:
            other.append(name)
    if other:
        rep.err(1, qdir, f"根级不允许存在文件/隐藏文件: {', '.join(other)}")
    missing = [d for d in DIRS if d not in subdirs]
    extra = [d for d in subdirs if d not in DIRS]
    if missing:
        rep.err(1, qdir, f"缺少子目录: {', '.join(missing)} (必须恰为 1..6)")
    if extra:
        rep.err(1, qdir, f"多余子目录: {', '.join(extra)} (必须恰为 1..6, 不带前导零)")
    for d in DIRS:
        dp = os.path.join(qdir, d)
        if not os.path.isdir(dp):
            found[d] = None
            continue
        files, subs = [], []
        for name in sorted(os.listdir(dp)):
            p = os.path.join(dp, name)
            if os.path.isdir(p):
                subs.append(name)
            else:
                files.append(name)
        if subs:
            rep.err(2, os.path.join(d, ""), f"不允许子目录: {', '.join(subs)}")
        non_pacer = [f for f in files if f != "pacer.txt"]
        if non_pacer:
            rep.err(2, d, f"只允许 pacer.txt, 发现其它文件: {', '.join(non_pacer)}")
        found[d] = os.path.join(dp, "pacer.txt") if "pacer.txt" in files else None
    return found


def check_encoding_bytes(path, rel, rep):
    """检查项 3: UTF-8 / LF / 无 CRLF / 无末尾换行。返回 str 或 None。"""
    raw = open(path, "rb").read()
    if raw.startswith(b"\xef\xbb\xbf"):
        rep.err(3, rel, "含 UTF-8 BOM, 必须为无 BOM 的 UTF-8")
        return None
    if b"\r" in raw:
        kind = "CRLF" if b"\r\n" in raw else "孤立 CR"
        rep.err(3, rel, f"含 {kind} 换行 (Windows 文本模式写出的 \\r\\n 会导致服务端解析失败/假成功), 必须纯 LF")
    if raw.endswith(b"\n"):
        rep.err(3, rel, "文件末尾不允许有换行 (无末尾换行)")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as e:
        rep.err(3, rel, f"不是合法 UTF-8: {e}")
        return None
    return text


def check_lines(text, d, rel, rep, schema):
    """检查项 4、5、6、7: 三行结构 / timestamp / 模块 / 参数。"""
    lines = text.split("\n")
    if len(lines) != 3:
        rep.err(4, rel, f"必须恰好 3 行, 实际 {len(lines)} 行")
        return
    for i, ln in enumerate(lines, 1):
        if ln != ln.strip() or ln.strip() == "":
            rep.err(4, rel, f"第 {i} 行行首/行尾有空白或空行: {ln!r}")
    # line1 timestamp
    m = TS_RE.match(lines[0])
    if not m:
        rep.err(4, rel, f"第 1 行必须形如 [timestamp:N], 实际: {lines[0]!r}")
    else:
        if m.group(1) != d:
            rep.err(5, rel, f"timestamp={m.group(1)} 与目录名 {d} 不一致 (必须等于目录号)")
    # line2 mode
    mode = None
    m = MODE_RE.match(lines[1])
    if not m:
        rep.err(4, rel, f"第 2 行必须形如 pacer_mode:<模块>, 实际: {lines[1]!r}")
    else:
        mode = m.group(1)
        if mode not in schema["module_names"]:
            rep.err(6, rel, f"未知模块 {mode!r}, 只允许: {', '.join(schema['module_names'])}")
    # line3 params
    m = CFG_RE.match(lines[2])
    if not m:
        rep.err(4, rel, f"第 3 行必须形如 pacer_config:k=v,..., 实际: {lines[2]!r}")
        return
    if mode is None or mode not in schema["modules"]:
        return
    body = m.group(1)
    mod = schema["modules"][mode]
    if body.strip() == "":
        return  # 检查项 8: 空参数 = 使用模块默认值
    values = {}
    for tok in body.split(","):
        pm = PARAM_RE.match(tok.strip())
        if not pm:
            rep.err(7, rel, f"参数片段非法 (须 name=整数, 无空格): {tok!r}")
            continue
        name, val = pm.group(1), int(pm.group(2))
        if name in values:
            rep.err(7, rel, f"参数重复: {name}")
            continue
        if name not in mod["params"]:
            allowed = ", ".join(mod["params"])
            rep.err(7, rel, f"模块 {mode} 不认识参数 {name!r} (允许: {allowed})")
            continue
        spec = mod["params"][name]
        t = spec["type"]
        if t == "posint" and val < 1:
            rep.err(7, rel, f"{name}={val} 非法: 必须为正整数 (>=1)")
            continue
        if t == "nonnegint" and val < 0:
            rep.err(7, rel, f"{name}={val} 非法: 必须为非负整数 (>=0)")
            continue
        if t == "bool01" and val not in (0, 1):
            rep.err(7, rel, f"{name}={val} 非法: 只允许 0 或 1")
            continue
        values[name] = val
    for c in mod.get("constraints", []):
        l, r = c["left"], c["right"]
        if l in values and r in values:
            if not (values[l] >= values[r]):
                rep.err(7, rel, f"约束违反: {c['msg']} (当前 {l}={values[l]}, {r}={values[r]})")


def validate(qdir, schema):
    rep = Report()
    files = check_question_tree(qdir, rep)
    for d in DIRS:
        p = files.get(d)
        if not p:
            continue  # 目录缺失/无文件: 检查项 8 允许无文件; 目录缺失已在检查1报
        rel = os.path.join(d, "pacer.txt")
        text = check_encoding_bytes(p, rel, rep)
        if text is None:
            continue
        check_lines(text, d, rel, rep, schema)
    return rep


def make_sample(root, kind):
    """生成自测样例: valid / crlf / invalid。"""
    q = os.path.join(root, kind, "question")
    for d in DIRS:
        os.makedirs(os.path.join(q, d), exist_ok=True)
    if kind == "valid":
        body = "[timestamp:%s]\npacer_mode:leak_bucket\npacer_config:leak_rate=9,bucket_cap=30,leak_interval_us=1000"
        for d in DIRS:
            with open(os.path.join(q, d, "pacer.txt"), "wb") as fh:
                fh.write((body % d).encode("utf-8"))  # LF, 无末尾换行
    elif kind == "crlf":
        for d in DIRS:
            with open(os.path.join(q, d, "pacer.txt"), "wb") as fh:
                fh.write(("[timestamp:%s]\r\npacer_mode:origin\r\npacer_config:burst_tokens=10\r\n" % d).encode("utf-8"))
    elif kind == "invalid":
        # 1) timestamp 错号 2) 未知参数 3) burst<tokens 4) 未知模块 5) 多余文件
        with open(os.path.join(q, "1", "pacer.txt"), "wb") as fh:
            fh.write(b"[timestamp:9]\npacer_mode:leak_bucket\npacer_config:leak_rate=9")
        with open(os.path.join(q, "2", "pacer.txt"), "wb") as fh:
            fh.write(b"[timestamp:2]\npacer_mode:token_bucket\npacer_config:tokens=50,burst=20")
        with open(os.path.join(q, "3", "pacer.txt"), "wb") as fh:
            fh.write(b"[timestamp:3]\npacer_mode:origin\npacer_config:burst_tokens=10,rate_limit=99")
        with open(os.path.join(q, "4", "pacer.txt"), "wb") as fh:
            fh.write(b"[timestamp:4]\npacer_mode:random_module\npacer_config:")
        with open(os.path.join(q, "5", "pacer.txt"), "wb") as fh:
            fh.write(b"[timestamp:5]\npacer_mode:leak_bucket\npacer_config:leak_rate=9,bucket_cap=30,leak_interval_us=1000\n")
        with open(os.path.join(q, "6", "extra.txt"), "wb") as fh:
            fh.write(b"x")
    return q


def run_selftest(schema):
    results = []
    with tempfile.TemporaryDirectory(prefix="pacer_selftest_") as tmp:
        expect = {"valid": 0, "crlf": 1, "invalid": 1}
        for kind in ("valid", "crlf", "invalid"):
            q = make_sample(tmp, kind)
            rep = validate(q, schema)
            code = 1 if rep.errors else 0
            ok = code == expect[kind]
            results.append((kind, code, expect[kind], ok, rep.errors))
    return results


def emit(rep, as_json, extra=None):
    payload = {
        "ok": not rep.errors,
        "error_count": len(rep.errors),
        "errors": rep.errors,
    }
    if extra:
        payload.update(extra)
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=1))
    else:
        if rep.errors:
            print(f"[FAIL] {len(rep.errors)} 处错误:")
            for e in rep.errors:
                print(f"  - [检查{e['check']}] {e['path']}: {e['msg']}")
        else:
            print("[PASS] 全部检查通过 (结构/换行/三行/timestamp/模块/参数)")


def main():
    ap = argparse.ArgumentParser(description="pacer.txt 本地校验器")
    ap.add_argument("question", nargs="?", help="question 目录路径")
    ap.add_argument("--json", action="store_true", help="JSON 输出")
    ap.add_argument("--selftest", action="store_true", help="运行内置三样例自测")
    args = ap.parse_args()

    schema = load_schema()

    if args.selftest:
        results = run_selftest(schema)
        if args.json:
            print(json.dumps([{"case": k, "exit": c, "expected": e, "ok": ok, "errors": errs}
                              for k, c, e, ok, errs in results], ensure_ascii=False, indent=1))
        else:
            for k, c, e, ok, errs in results:
                mark = "OK" if ok else "MISMATCH"
                print(f"== 自测样例 [{k}] 退出码 {c} (期望 {e}) -> {mark} ==")
                for err in errs:
                    print(f"   - [检查{err['check']}] {err['path']}: {err['msg']}")
                if not errs:
                    print("   (无错误)")
                print()
        all_ok = all(r[3] for r in results)
        print("SELFTEST", "PASS" if all_ok else "FAIL")
        sys.exit(0 if all_ok else 1)

    if not args.question:
        ap.error("需要 question 目录路径 (或使用 --selftest)")
    rep = validate(args.question, schema)
    emit(rep, args.json, extra={"question": args.question})
    sys.exit(1 if rep.errors else 0)


if __name__ == "__main__":
    main()
