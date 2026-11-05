#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""iDSN 竞赛平台（ESAI/Trit）客户端。

要点（逆向自平台前端）：
- 登录：POST /api/auth/login  {"username": <手机号/用户名/邮箱>, "password": MD5(明文)}
- 鉴权：请求头 Authorization: Bearer <access_token>
- 响应：{"success": bool, "data": ..., "code": ..., "msg": ..., "count": ...}
- 刷新：POST /api/auth/refreshtoken（Bearer refresh_token）

用法：
  python client/trit.py login [--username <手机号>] [--password ...]
  python client/trit.py status
  python client/trit.py get /api/competition/my [--out intel/raw/trit/my.json]
  python client/trit.py probe          # 批量探测公开/常用接口，落盘
  python client/trit.py raw <method> <path> [json]
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import sys
from pathlib import Path

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

ROOT = Path(__file__).resolve().parents[1]
BASE = os.environ.get("IDSN_TRIT_BASE", "https://218.2.108.11:40000")
TOKEN_FILE = ROOT / "runs" / "trit_token.json"
SECRET_FILE = ROOT / "client" / "secrets.json"
RAW_DIR = ROOT / "intel" / "raw" / "trit"


def now() -> dt.datetime:
    return dt.datetime.now().astimezone()


def md5_hex(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def read_secrets() -> dict:
    if SECRET_FILE.exists():
        return json.loads(SECRET_FILE.read_text("utf-8-sig"))
    return {}


def load_token() -> dict:
    if TOKEN_FILE.exists():
        try:
            return json.loads(TOKEN_FILE.read_text("utf-8"))
        except Exception:
            pass
    return {}


def save_token(data: dict) -> None:
    TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    TOKEN_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), "utf-8")


def login(username: str, password: str) -> dict:
    r = requests.post(
        f"{BASE}/api/auth/login",
        json={"username": username, "password": md5_hex(password)},
        timeout=30,
        verify=False,
    )
    data = r.json()
    if not data.get("success"):
        raise SystemExit(f"[FAIL] 登录失败: {data.get('msg') or data}")
    d = data["data"]
    token = {
        "access_token": d["access_token"],
        "refresh_token": d.get("refresh_token"),
        "uuid": d.get("uuid"),
        "username": d.get("username"),
        "realname": d.get("realname"),
        "role": d.get("role"),
        "expire_in": d.get("expire_in"),
        "obtained_at": now().isoformat(timespec="seconds"),
    }
    save_token(token)
    return token


def refresh() -> dict:
    tok = load_token()
    rt = tok.get("refresh_token")
    if not rt:
        raise SystemExit("[FAIL] 无 refresh_token，需要重新 login")
    r = requests.post(
        f"{BASE}/api/auth/refreshtoken",
        headers={"Authorization": f"Bearer {rt}"},
        timeout=30,
        verify=False,
    )
    data = r.json()
    if not data.get("success"):
        raise SystemExit(f"[FAIL] 刷新失败: {data}")
    d = data["data"]
    tok.update({"access_token": d["access_token"], "refresh_token": d.get("refresh_token", rt),
                "obtained_at": now().isoformat(timespec="seconds")})
    save_token(tok)
    return tok


def api(method: str, path: str, **kwargs) -> requests.Response:
    """带自动刷新的一次请求。path 形如 /api/competition/my 或 /competition/my。"""
    if not path.startswith("/api"):
        path = "/api" + ("" if path.startswith("/") else "/") + path
    url = BASE + path
    tok = load_token()
    headers = kwargs.pop("headers", {})
    if tok.get("access_token"):
        headers.setdefault("Authorization", f"Bearer {tok['access_token']}")
    resp = requests.request(method.upper(), url, headers=headers, timeout=kwargs.pop("timeout", 60),
                            verify=False, **kwargs)
    if resp.status_code == 401 and tok.get("refresh_token"):
        tok = refresh()
        headers["Authorization"] = f"Bearer {tok['access_token']}"
        resp = requests.request(method.upper(), url, headers=headers, timeout=kwargs.pop("timeout", 60),
                                verify=False, **kwargs)
    return resp


def show(resp: requests.Response, out: str | None = None, limit: int = 1200) -> None:
    print(f"[HTTP {resp.status_code}] {resp.request.method} {resp.url}")
    try:
        data = resp.json()
    except ValueError:
        print(resp.text[:limit])
        return
    text = json.dumps(data, ensure_ascii=False, indent=2)
    print(text[:limit])
    if out:
        p = Path(out)
        if not p.is_absolute():
            p = ROOT / p
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, "utf-8")
        print(f"[saved] {p.relative_to(ROOT)}")


# ---------------------------------------------------------------- commands
def cmd_login(args) -> int:
    sec = read_secrets()
    # 用户名（手机号）不入库：--username > 环境变量 > client/secrets.json
    username = (args.username or os.environ.get("IDSN_TRIT_USERNAME")
                or sec.get("trit_username"))
    if not username:
        raise SystemExit(
            f"[FAIL] 没有用户名：写入 {SECRET_FILE} 的 trit_username 字段，"
            "或设置环境变量 IDSN_TRIT_USERNAME")
    password = args.password or sec.get("trit_password") or sec.get("password")
    if not password:
        raise SystemExit(f"[FAIL] 没有密码：请写入 {SECRET_FILE} 的 trit_password 字段")
    tok = login(username, password)
    print(f"[OK] 登录成功 user={tok['username']} role={tok['role']} uuid={tok['uuid']} "
          f"expire_in={tok['expire_in']}")
    return 0


def cmd_status(args) -> int:
    tok = load_token()
    if not tok:
        print("[--] 未登录")
        return 1
    print(f"BASE: {BASE}")
    print(f"user: {tok.get('username')}  role={tok.get('role')}  got={tok.get('obtained_at')}  expire_in={tok.get('expire_in')}")
    r = api("GET", "/competition/my")
    print(f"自检 GET /api/competition/my -> HTTP {r.status_code}")
    return 0 if r.status_code == 200 else 2


def cmd_get(args) -> int:
    method = (args.method or "GET").upper()
    kwargs = {}
    if args.json:
        kwargs["json"] = json.loads(args.json)
    if args.params:
        kwargs["params"] = json.loads(args.params)
    r = api(method, args.path, **kwargs)
    show(r, args.out)
    return 0 if r.status_code < 400 else 1


PROBE_PATHS = [
    "/api/competition/my",
    "/api/competition/home",
    "/api/competition/comp_examinee/self_comp_list",
    "/api/competition/match",
    "/api/user/info",
    "/api/account/info",
    "/api/competition/comp_examinee/comp_user_info_competition/b0335a137893413bac81481e58614d40",
    "/api/competition/competition/trophy/b0335a137893413bac81481e58614d40",
]


def cmd_probe(args) -> int:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    summary = []
    for path in PROBE_PATHS:
        try:
            r = api("GET", path)
        except Exception as exc:  # noqa: BLE001
            summary.append((path, "ERR", str(exc)[:120]))
            continue
        name = path.strip("/").replace("/", "_")[:90] + ".json"
        out = RAW_DIR / name
        try:
            body = r.json()
            out.write_text(json.dumps(body, ensure_ascii=False, indent=2), "utf-8")
            note = f"success={body.get('success')} keys={list(body)[:5]}"
            if isinstance(body.get("data"), list):
                note = f"list(len={len(body['data'])})"
        except ValueError:
            out.write_text(r.text, "utf-8")
            note = r.text[:80]
        summary.append((path, r.status_code, note))
        print(f"[{r.status_code}] {path}  {note}")
    (RAW_DIR / "_probe_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), "utf-8")
    return 0


def cmd_download(args) -> int:
    resp = api("GET", args.path, stream=True, timeout=600)
    if resp.status_code >= 400:
        print(f"[FAIL] HTTP {resp.status_code}: {resp.text[:300]}")
        return 1
    out = Path(args.out)
    if not out.is_absolute():
        out = ROOT / out
    out.parent.mkdir(parents=True, exist_ok=True)
    total = 0
    with out.open("wb") as fh:
        for chunk in resp.iter_content(chunk_size=1 << 20):
            if chunk:
                fh.write(chunk)
                total += len(chunk)
    print(f"[OK] {out}  {total:,} bytes")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="iDSN 竞赛平台客户端")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("login")
    p.add_argument("--username")
    p.add_argument("--password")
    p.set_defaults(func=cmd_login)

    p = sub.add_parser("status")
    p.set_defaults(func=cmd_status)

    p = sub.add_parser("get")
    p.add_argument("path")
    p.add_argument("--method")
    p.add_argument("--json")
    p.add_argument("--params")
    p.add_argument("--out")
    p.set_defaults(func=cmd_get)

    p = sub.add_parser("probe")
    p.set_defaults(func=cmd_probe)

    p = sub.add_parser("download")
    p.add_argument("path")
    p.add_argument("out")
    p.set_defaults(func=cmd_download)

    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
