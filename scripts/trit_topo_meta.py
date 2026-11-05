#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""打开竞赛实战页，读取拓扑 iframe 的隐藏参数（expt_id 等），为 API 驱动准备。"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://218.2.108.11:40000"
TOKEN_FILE = ROOT / "runs" / "trit_token.json"
URL = ("/competition/match/practice/d825bc6c-e957-4d62-a444-2bf53a606060/"
       "fd126f3e-94e0-48b4-9685-7eb169591e6e"
       "?from=/competition/detail/b0335a137893413bac81481e58614d40")

sys.path.insert(0, str(ROOT / "client"))
import trit  # noqa: E402


def fresh_token() -> dict:
    secrets = json.loads((ROOT / "client" / "secrets.json").read_text("utf-8-sig"))
    return trit.login(secrets.get("trit_username"), secrets.get("trit_password"))


def main() -> int:
    tok = fresh_token()
    user_token = json.dumps({
        "access_token": tok["access_token"],
        "refresh_token": tok.get("refresh_token"),
        "user_uuid": tok.get("uuid"),
    })
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--ignore-certificate-errors"])
        ctx = browser.new_context(ignore_https_errors=True, viewport={"width": 1600, "height": 1000})
        ctx.add_init_script("try{localStorage.setItem('USER_TOKEN', %s);}catch(e){}" % json.dumps(user_token))
        page = ctx.new_page()
        for attempt in range(4):
            try:
                page.goto(BASE + URL, wait_until="domcontentloaded", timeout=45000)
                break
            except Exception as exc:  # noqa: BLE001
                print("retry", attempt, str(exc)[:100])
                time.sleep(3)
        time.sleep(10)
        frames = page.frames
        print("frames:", [(f.name, f.url[:90]) for f in frames])
        ifrs = page.evaluate("""() => Array.from(document.querySelectorAll('iframe')).map(f => ({id: f.id, src: f.src}))""")
        print("iframes in DOM:", ifrs)
        if len(frames) < 2:
            time.sleep(25)
            frames = page.frames
            print("frames(after 35s):", [(f.name, f.url[:90]) for f in frames])
            ifrs = page.evaluate("""() => Array.from(document.querySelectorAll('iframe')).map(f => ({id: f.id, src: f.src}))""")
            print("iframes in DOM:", ifrs)
        topo = None
        for f in frames:
            if "/topo/" in f.url:
                topo = f
                break
        if not topo:
            print("[WARN] 未找到 topo iframe")
            page.screenshot(path=str(ROOT / "runs/browser/frames.png"))
            browser.close()
            return 1
        info = topo.evaluate("""() => {
            const out = {title: document.title, url: location.href};
            const inputs = {};
            document.querySelectorAll('input,select').forEach(el => {
                if (el.id) inputs[el.id] = el.value;
            });
            out.inputs = inputs;
            out.fns = ['techStartDevice','startDevice','deviceOperate','openVnc','openConsole','techConsole']
                .filter(n => typeof window[n] === 'function' || typeof window[n] !== 'undefined');
            out.cookies = document.cookie ? true : false;
            return out;
        }""")
        print(json.dumps(info, ensure_ascii=False, indent=1)[:4000])
        (ROOT / "runs/browser/topo_meta.json").write_text(
            json.dumps(info, ensure_ascii=False, indent=1), "utf-8")
        page.screenshot(path=str(ROOT / "runs/browser/topo_meta.png"))
        browser.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
