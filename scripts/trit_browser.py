#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""用无头浏览器打开竞赛平台页面，注入登录态，抓取网络请求并截图。

用途：
- 观察前端在真实交互中调用了哪些接口（例如启动虚拟环境的接口）
- 截图（可用 read_image 查看），必要时后续用 playwright 驱动页面交互

用法：
  python scripts/trit_browser.py --path /competition/match/practice/<schedule>/<record> --wait 60
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://218.2.108.11:40000"
TOKEN_FILE = ROOT / "runs" / "trit_token.json"
OUTDIR = ROOT / "runs" / "browser"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--path", required=True, help="页面路径，如 /competition/match/practice/x/y")
    ap.add_argument("--wait", type=int, default=45, help="页面停留秒数")
    ap.add_argument("--tag", default=time.strftime("%H%M%S"))
    ap.add_argument("--headed", action="store_true")
    args = ap.parse_args()

    tok = json.loads(TOKEN_FILE.read_text("utf-8"))
    try:
        import sys as _sys
        _sys.path.insert(0, str(ROOT / "client"))
        import trit  # noqa: E402
        sec = json.loads((ROOT / "client" / "secrets.json").read_text("utf-8-sig"))
        tok = trit.login(sec.get("trit_username"), sec.get("trit_password"))
        print("[OK] 已刷新登录令牌")
    except Exception as exc:  # noqa: BLE001
        print("[WARN] 刷新令牌失败，使用旧令牌:", str(exc)[:120])
    user_token = json.dumps({
        "access_token": tok["access_token"],
        "refresh_token": tok.get("refresh_token"),
        "user_uuid": tok.get("uuid"),
    }, ensure_ascii=False)

    OUTDIR.mkdir(parents=True, exist_ok=True)
    netlog: list[dict] = []
    console: list[str] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=not args.headed, args=["--ignore-certificate-errors"])
        ctx = browser.new_context(ignore_https_errors=True, viewport={"width": 1600, "height": 1000})
        ctx.add_init_script(
            "try{localStorage.setItem('USER_TOKEN', %s);}catch(e){}" % json.dumps(user_token)
        )

        page = ctx.new_page()

        def on_response(resp):
            try:
                url = resp.url
                if "/api/" not in url:
                    return
                req = resp.request
                item = {
                    "ts": round(time.time(), 2),
                    "method": req.method,
                    "url": url,
                    "status": resp.status,
                    "post": (req.post_data or "")[:600] if req.method != "GET" else "",
                }
                ctype = (resp.headers or {}).get("content-type", "")
                if "json" in ctype and resp.status < 400:
                    try:
                        item["body"] = resp.text()[:1200]
                    except Exception:
                        pass
                netlog.append(item)
            except Exception:
                pass

        page.on("response", on_response)
        page.on("console", lambda m: console.append(f"[{m.type}] {m.text}"[:400]))

        last_err = None
        for attempt in range(5):
            try:
                page.goto(f"{BASE}{args.path}", wait_until="domcontentloaded", timeout=45000)
                break
            except Exception as exc:  # noqa: BLE001
                last_err = exc
                print(f"[retry {attempt+1}] goto 失败: {str(exc)[:120]}")
                time.sleep(3)
                try:
                    page.reload(wait_until="domcontentloaded", timeout=45000)
                    break
                except Exception:
                    pass
        else:
            print(f"[WARN] 页面始终未加载成功: {str(last_err)[:200]}")
        shots = sorted({3, 8, 15, 30, args.wait})
        for sec in range(1, args.wait + 1):
            time.sleep(1)
            if sec in shots:
                page.screenshot(path=str(OUTDIR / f"{args.tag}_t{sec:02d}.png"))
        page.screenshot(path=str(OUTDIR / f"{args.tag}_final.png"), full_page=True)

        html = page.content()
        (OUTDIR / f"{args.tag}_page.html").write_text(html, "utf-8")
        (OUTDIR / f"{args.tag}_network.json").write_text(
            json.dumps(netlog, ensure_ascii=False, indent=1), "utf-8")
        (OUTDIR / f"{args.tag}_console.txt").write_text("\n".join(console), "utf-8")
        browser.close()

    print(f"[OK] screenshots/logs -> {OUTDIR}")
    print(f"     network entries: {len(netlog)}")
    for item in netlog[-40:]:
        print(f"  {item['status']} {item['method']} {item['url'][:150]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
