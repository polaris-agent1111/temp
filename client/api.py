#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""iDSN 挑战赛 API 客户端（登录 / 查榜 / 端点发现 / 安全提交）。

安全守则（写死在代码里）：
1. 登录失败【绝不重试】—— 错误密码有当日锁定次数，试错会废掉账号。
2. 提交有本地每日计数（硬上限 5 次/天），必须显式 --yes。
3. 只使用与网页等价的正常接口，不探测/攻击评测系统。

用法：
  python client/api.py login                 # 用 secrets.json / 环境变量 / 交互输入登录
  python client/api.py status                # 会话与今日提交额度
  python client/api.py board [--save]        # 查榜并渲染（--save 存快照 + 记流水）
  python client/api.py discover [--path /]   # 抓取登录后的页面/表单/脚本，辅助定位提交端点
  python client/api.py submit FILE [--yes]   # 按 endpoints.json 配置提交（做完 discover 后配置）
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import getpass
import hashlib
import json
import os
import pickle
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
BASE = os.environ.get("IDSN_BASE", "http://47.120.64.152:5000").rstrip("/")
TEAM = os.environ.get("IDSN_TEAM", "赛博coder")
SESSION_FILE = ROOT / "runs" / ".session.pkl"
REDIRECT_FILE = ROOT / "runs" / "login_redirect.json"
SECRET_FILE = ROOT / "client" / "secrets.json"
ENDPOINTS_FILE = ROOT / "client" / "endpoints.json"
SUBMISSIONS = ROOT / "runs" / "submissions.jsonl"
LEDGER = ROOT / "runs" / "leaderboard" / "ledger.csv"
SNAPSHOTS = ROOT / "intel" / "raw"
AUTH_RAW = ROOT / "intel" / "raw" / "auth"
DAILY_LIMIT = 5


def now_local() -> dt.datetime:
    return dt.datetime.now().astimezone()


def ts() -> str:
    return now_local().isoformat(timespec="seconds")


# ---------------------------------------------------------------- session
def load_session() -> requests.Session:
    s = requests.Session()
    s.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) idsn-agent/1.0",
        "Accept-Language": "zh-CN,zh;q=0.9",
    })
    if SESSION_FILE.exists():
        try:
            s.cookies.update(pickle.loads(SESSION_FILE.read_bytes()))
        except Exception:
            pass
    return s


def save_session(s: requests.Session) -> None:
    SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)
    SESSION_FILE.write_bytes(pickle.dumps(s.cookies))


def read_secret() -> str | None:
    pwd = os.environ.get("IDSN_PASSWORD")
    if pwd:
        return pwd
    if SECRET_FILE.exists():
        try:
            return json.loads(SECRET_FILE.read_text("utf-8-sig")).get("password")
        except Exception:
            return None
    return None


# ---------------------------------------------------------------- login
def cmd_login(args) -> int:
    pwd = args.password or read_secret()
    if not pwd:
        if not sys.stdin.isatty():
            print(f"[ERR] 找不到密码：请设置环境变量 IDSN_PASSWORD，或写入 {SECRET_FILE}")
            return 2
        pwd = getpass.getpass(f"{TEAM} 的密码: ")
    s = load_session()
    try:
        r = s.post(f"{BASE}/api/login", json={"team": TEAM, "password": pwd}, timeout=25)
    except requests.RequestException as exc:
        print(f"网络错误，未提交密码：{exc}")
        return 2
    try:
        data = r.json()
    except ValueError:
        data = {"ok": False, "message": f"非 JSON 响应 HTTP {r.status_code}: {r.text[:200]}"}

    if r.ok and data.get("ok"):
        save_session(s)
        redirect = data.get("redirect") or "/"
        REDIRECT_FILE.write_text(json.dumps({"redirect": redirect, "at": ts()}, ensure_ascii=False, indent=2), "utf-8")
        print(f"[OK] 登录成功 · 跳转: {redirect}")
        return 0

    # 失败：只报错，不重试
    msg = data.get("message") or data.get("error") or f"HTTP {r.status_code}"
    remaining = data.get("remaining")
    tail = f"（今天还剩 {remaining} 次错误机会）" if isinstance(remaining, int) else ""
    print(f"[FAIL] 登录失败：{msg}{tail}")
    print("        已停止，不重试。请核对密码后手动重试一次。")
    return 1


def auth_status() -> tuple[bool, str]:
    s = load_session()
    try:
        r = s.get(f"{BASE}/api/leaderboard", timeout=20)
        if r.status_code == 200:
            return (len(s.cookies) > 0, "已持有会话 Cookie" if s.cookies else "无会话 Cookie（榜单接口匿名可读）")
    except requests.RequestException as exc:
        return (False, f"网络错误: {exc}")
    return (False, f"HTTP {r.status_code}")


# ---------------------------------------------------------------- board
def fetch_board(s: requests.Session) -> dict:
    r = s.get(f"{BASE}/api/leaderboard", timeout=25)
    r.raise_for_status()
    return r.json()


def team_results(submissions: list[dict]) -> list[dict]:
    out = []
    for sub in submissions or []:
        attempts = sub.get("attempts") or []
        if not attempts:
            continue
        best = min(attempts, key=lambda a: (float(a.get("download_seconds") or 1e18), a.get("submitted_at", "")))
        out.append({
            "team": sub.get("team"),
            "best": float(best.get("download_seconds") or 0.0),
            "submitted_at": best.get("submitted_at"),
            "n_attempts": len(attempts),
        })
    out.sort(key=lambda x: (x["best"], x["submitted_at"] or "", x["team"] or ""))
    return out


def build_board(data: dict) -> dict:
    board = data.get("leaderboard") or {}
    problems = board.get("problems") or []
    per_problem = []
    totals: dict[str, float] = {}
    finished: dict[str, set[int]] = {}
    for idx, prob in enumerate(problems):
        rows = team_results(prob.get("submissions") or [])
        per_problem.append({"id": prob.get("id"), "title": prob.get("title"), "rows": rows})
        for row in rows:
            team = row["team"]
            if idx in finished.get(team, set()):
                continue
            finished.setdefault(team, set()).add(idx)
            totals[team] = totals.get(team, 0.0) + row["best"]
    overall = []
    n = len(problems)
    for team, total in totals.items():
        if len(finished.get(team, set())) == n:
            overall.append({"team": team, "total": total})
    overall.sort(key=lambda x: (x["total"], x["team"]))

    teams = []
    seen = set()
    for prob in per_problem:
        for row in prob["rows"]:
            if row["team"] not in seen:
                seen.add(row["team"])
                teams.append(row["team"])
    return {
        "problems": per_problem,
        "overall": overall,
        "stats": {
            "count": len(teams),
            "shortest": overall[0]["total"] if overall else None,
            "average": (sum(x["total"] for x in overall) / len(overall)) if overall else None,
        },
        "log": data.get("submission_log") or [],
    }


def render_board(board: dict) -> None:
    print(f"\n=== 总排名（{len(board['overall'])} 支有成绩的队伍）===")
    print(f"{'名次':<4}{'团队':<12}{'总用时(s)':>12}")
    for i, row in enumerate(board["overall"], 1):
        print(f"{i:<4}{row['team']:<12}{row['total']:>12.4f}")
    for prob in board["problems"]:
        print(f"\n--- {prob['title']} ---")
        print(f"{'名次':<4}{'团队':<12}{'最好(s)':>12}{'提交数':>6}  最晚提交")
        for i, row in enumerate(prob["rows"], 1):
            print(f"{i:<4}{row['team']:<12}{row['best']:>12.4f}{row['n_attempts']:>6}  {row['submitted_at']}")
    if board["log"]:
        print("\n--- 最近提交日志 ---")
        for item in board["log"][-10:]:
            print(f"  {item.get('submitted_at')}  {item.get('team')}  题目{item.get('problem')}  {item.get('status')}")


def save_snapshot(data: dict) -> Path:
    SNAPSHOTS.mkdir(parents=True, exist_ok=True)
    stamp = now_local().strftime("%Y%m%dT%H%M%S")
    path = SNAPSHOTS / f"leaderboard_{stamp}.json"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), "utf-8")
    return path


def append_ledger(board: dict) -> None:
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    new = not LEDGER.exists()
    with LEDGER.open("a", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        if new:
            w.writerow(["checked_at", "problem", "rank", "team", "best_seconds", "n_attempts", "submitted_at"])
        stamp = ts()
        for prob in board["problems"]:
            for i, row in enumerate(prob["rows"], 1):
                w.writerow([stamp, prob["title"], i, row["team"], f"{row['best']:.4f}", row["n_attempts"], row["submitted_at"]])


def cmd_board(args) -> int:
    s = load_session()
    try:
        data = fetch_board(s)
    except requests.RequestException as exc:
        print(f"[ERR] 榜单获取失败: {exc}")
        return 2
    board = build_board(data)
    render_board(board)
    if args.save:
        p = save_snapshot(data)
        append_ledger(board)
        print(f"\n[OK] 快照: {p.relative_to(ROOT)}")
        print(f"[OK] 流水: {LEDGER.relative_to(ROOT)}")
    return 0


# ---------------------------------------------------------------- discover
def extract_links(html: str, base: str) -> dict:
    import re
    links = sorted(set(re.findall(r'href=["\']([^"\']+)["\']', html)))
    scripts = sorted(set(re.findall(r'src=["\']([^"\']+\.js[^"\']*)["\']', html)))
    forms = re.findall(r'(?is)<form[^>]*>', html)
    inputs = re.findall(r'(?i)<input[^>]*name=["\']([^"\']+)["\']', html)
    return {"links": links, "scripts": scripts, "forms": forms, "inputs": sorted(set(inputs))}


def cmd_discover(args) -> int:
    s = load_session()
    AUTH_RAW.mkdir(parents=True, exist_ok=True)
    targets = [args.path] if args.path else ["/"]
    if not args.path and REDIRECT_FILE.exists():
        try:
            targets.append(json.loads(REDIRECT_FILE.read_text("utf-8")).get("redirect") or "/")
        except Exception:
            pass
    seen = []
    for path in dict.fromkeys(targets):
        url = path if path.startswith("http") else f"{BASE}{path}"
        try:
            r = s.get(url, timeout=25)
        except requests.RequestException as exc:
            print(f"[ERR] {url}: {exc}")
            continue
        name = (path.strip("/").replace("/", "_") or "root")[:60]
        out = AUTH_RAW / f"page_{name}.html"
        out.write_text(r.text, "utf-8")
        info = extract_links(r.text, BASE)
        print(f"\n=== {url}  HTTP {r.status_code}  {len(r.text)} bytes -> {out.relative_to(ROOT)}")
        if info["links"]:
            print(" links:", ", ".join(info["links"][:25]))
        if info["scripts"]:
            print(" scripts:", ", ".join(info["scripts"][:15]))
        if info["forms"]:
            print(" forms:", " | ".join(f.strip()[:160] for f in info["forms"][:6]))
        if info["inputs"]:
            print(" inputs:", ", ".join(info["inputs"][:25]))
        seen.append(url)
        time.sleep(0.5)
    if not seen:
        print("[WARN] 没有抓到任何页面（可能未登录或网络异常）")
        return 1
    return 0


# ---------------------------------------------------------------- submit
def todays_submissions() -> list[dict]:
    if not SUBMISSIONS.exists():
        return []
    today = now_local().date()
    out = []
    for line in SUBMISSIONS.read_text("utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            item = json.loads(line)
        except ValueError:
            continue
        try:
            when = dt.datetime.fromisoformat(item.get("at", "")).date()
        except ValueError:
            continue
        if when == today:
            out.append(item)
    return out


def cmd_submit(args) -> int:
    cfg_path = Path(args.file)
    if not cfg_path.is_absolute():
        cfg_path = ROOT / cfg_path
    if not cfg_path.exists():
        print(f"[ERR] 配置文件不存在: {cfg_path}")
        return 2
    payload = cfg_path.read_bytes()
    digest = hashlib.sha256(payload).hexdigest()[:16]
    done = todays_submissions()
    if len(done) >= DAILY_LIMIT:
        print(f"[BLOCK] 今日已提交 {len(done)} 次，达到官方上限 {DAILY_LIMIT}，拒绝提交。")
        return 3
    if not args.yes:
        print(f"[DRY-RUN] {cfg_path.name} sha256:{digest} {len(payload)} bytes "
              f"| 今日已用 {len(done)}/{DAILY_LIMIT}。确认提交请加 --yes")
        return 0
    if not ENDPOINTS_FILE.exists():
        print(f"[BLOCK] 尚未发现提交端点。先运行 `python client/api.py discover` 定位，"
              f"再按 {ENDPOINTS_FILE.relative_to(ROOT)} 模板填好。")
        return 3
    endpoints = json.loads(ENDPOINTS_FILE.read_text("utf-8"))
    sub = endpoints.get("submit") or {}
    if not sub.get("path"):
        print("[BLOCK] endpoints.json 缺少 submit.path")
        return 3

    s = load_session()
    url = f"{BASE}{sub['path']}"
    field = sub.get("field", "file")
    extra = sub.get("extra") or {}
    try:
        if sub.get("method", "POST").upper() == "POST" and field:
            files = {field: (cfg_path.name, payload, "text/plain")}
            r = s.post(url, files=files, data=extra, timeout=180)
        else:
            r = s.post(url, json={**extra, "config": payload.decode("utf-8", "replace")}, timeout=180)
    except requests.RequestException as exc:
        print(f"[ERR] 提交网络错误（结果未知，务必登录网页确认）: {exc}")
        return 2

    record = {
        "at": ts(), "file": str(cfg_path), "sha256_16": digest, "bytes": len(payload),
        "http_status": r.status_code, "url": url,
        "response": r.text[:2000],
    }
    SUBMISSIONS.parent.mkdir(parents=True, exist_ok=True)
    with SUBMISSIONS.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(f"[HTTP {r.status_code}] {r.text[:500]}")
    print(f"[OK] 已记录到 {SUBMISSIONS.relative_to(ROOT)}（今日 {len(done) + 1}/{DAILY_LIMIT}）")
    return 0 if r.ok else 1


# ---------------------------------------------------------------- status
def cmd_status(args) -> int:
    ok, note = auth_status()
    print(f"BASE: {BASE}")
    print(f"TEAM: {TEAM}")
    print(f"会话: {note}")
    print(f"今日已提交: {len(todays_submissions())}/{DAILY_LIMIT}")
    if ENDPOINTS_FILE.exists():
        print(f"端点配置: {ENDPOINTS_FILE.relative_to(ROOT)}")
    else:
        print("端点配置: 缺失（先 discover）")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="iDSN 挑战赛 API 客户端")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("login", help="登录并持久化会话")
    p.add_argument("--password", help="密码（默认读环境变量/secrets.json/交互输入）")
    p.set_defaults(func=cmd_login)

    p = sub.add_parser("board", help="查榜")
    p.add_argument("--save", action="store_true", help="保存快照并记流水")
    p.set_defaults(func=cmd_board)

    p = sub.add_parser("discover", help="抓取登录后页面，定位提交端点")
    p.add_argument("--path", help="指定路径（默认 / 与登录 redirect）")
    p.set_defaults(func=cmd_discover)

    p = sub.add_parser("submit", help="提交参数配置文件")
    p.add_argument("file")
    p.add_argument("--yes", action="store_true", help="确认提交")
    p.set_defaults(func=cmd_submit)

    p = sub.add_parser("status", help="会话与额度状态")
    p.set_defaults(func=cmd_status)

    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
