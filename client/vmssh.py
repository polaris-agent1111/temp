#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VM 交互客户端：通过竞赛平台的 WebSSH 代理在云主机里执行命令。

背景（逆向自平台前端）：
- 平台提供 WebSSH 页面 /webssh?ssh_info=<base64("host=..&username=..&password=..")>
- 前端用 xterm.js 直连 WebSocket：wss://<platform>/webssh/term?sshInfo=<b64(JSON)>&rows=..&cols=..&closeTip=..
- WebSocket 上收发的是终端原始文本（无 JSON 包装），支持 "resize:<rows>:<cols>" 与 "ping"

用法：
  python client/vmssh.py shell                 # 交互式命令：ls、cat 等
  python client/vmssh.py run "uname -a"
  python client/vmssh.py push local remote
  python client/vmssh.py pull remote local
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import re
import ssl
import sys
import time
import uuid
from pathlib import Path

import websocket

ROOT = Path(__file__).resolve().parents[1]
TOKEN_FILE = ROOT / "runs" / "trit_token.json"
SECRETS = ROOT / "client" / "secrets.json"

# 云主机 SSH 信息（平台 topo 接口返回的设备属性）
# 注意：密码不入库。优先读环境变量 IDSN_VM_PASS，其次读 client/secrets.json 的 vm_password 字段
# （client/secrets.json 已被 .gitignore 排除，队友需自行向队长索取）。
VM_HOST = os.environ.get("IDSN_VM_HOST", "192.168.181.16")
VM_USER = os.environ.get("IDSN_VM_USER", "openlab")


def _secret(name: str, default: str = "") -> str:
    """读取敏感配置：环境变量 IDSN_<NAME> 优先，其次 client/secrets.json。"""
    env = os.environ.get(f"IDSN_{name.upper()}")
    if env:
        return env
    try:
        data = json.loads(SECRETS.read_text("utf-8-sig"))
        return str(data.get(name) or default)
    except Exception:  # noqa: BLE001
        return default


VM_PASS = os.environ.get("IDSN_VM_PASS") or _secret("vm_password")
PLATFORM = os.environ.get("IDSN_TRIT_BASE", "https://218.2.108.11:40000")
WS_BASE = PLATFORM.replace("https://", "wss://").replace("http://", "ws://")

ANSI_RE = re.compile(r"\x1b\[[0-9;?]*[a-zA-Z]|\x1b\][^\x07]*\x07|\r")


def clean(text: str) -> str:
    text = ANSI_RE.sub("", text)
    # 去掉 shell 提示符（形如 openlab@host:~$ 或 root@host:/#）
    text = re.sub(r"\S+@\S+:[^\s$#]*[$#]\s?", "", text)
    return text


class VmShell:
    def __init__(self, rows: int = 40, cols: int = 160, retries: int = 3):
        self.rows, self.cols = rows, cols
        self.retries = retries
        self.ws: websocket.WebSocket | None = None
        self.buffer = ""
        self.io_timeout = float(os.environ.get("IDSN_WS_TIMEOUT", "900"))

    # ---------------------------------------------------------------- conn
    def _ws_url(self) -> str:
        payload = json.dumps({
            "username": VM_USER,
            "ipaddress": VM_HOST,
            "port": 22,
            "password": VM_PASS,
            "logintype": 0,
        })
        b64 = base64.b64encode(payload.encode()).decode()
        return (f"{WS_BASE}/webssh/term?sshInfo={b64}&rows={self.rows}&cols={self.cols}"
                f"&closeTip=closed")

    def connect(self, timeout: float | None = None) -> None:
        timeout = timeout or self.io_timeout
        last = None
        for attempt in range(1, self.retries + 1):
            try:
                ws = websocket.create_connection(
                    self._ws_url(),
                    sslopt={"cert_reqs": ssl.CERT_NONE},
                    timeout=timeout,
                    suppress_origin=True,
                )
                self.ws = ws
                self.buffer = ""
                self._drain_until_prompt(timeout=timeout)
                # 关闭终端回显，避免命令文本混入输出（影响标记解析）
                try:
                    self.ws.send("stty -echo 2>/dev/null\r\n")
                    time.sleep(0.3)
                    self._drain_until_prompt(timeout=10)
                except Exception:  # noqa: BLE001
                    pass
                return
            except Exception as exc:  # noqa: BLE001
                last = exc
                time.sleep(2 * attempt)
        raise RuntimeError(f"连接 VM 失败: {last}")

    def _drain_until_prompt(self, timeout: float = 30) -> str:
        deadline = time.time() + timeout
        self.buffer = ""
        while time.time() < deadline:
            try:
                data = self.ws.recv()
            except Exception:  # noqa: BLE001
                break
            if isinstance(data, (bytes, bytearray)):
                data = data.decode("utf-8", "replace")
            self.buffer += data
            if self.buffer.rstrip().endswith("$") or self.buffer.rstrip().endswith("#"):
                return self.buffer
            if len(self.buffer) > 200000:
                self.buffer = self.buffer[-100000:]
        return self.buffer

    def close(self) -> None:
        try:
            if self.ws:
                self.ws.close()
        except Exception:  # noqa: BLE001
            pass
        self.ws = None

    # ---------------------------------------------------------------- run
    def run(self, cmd: str, timeout: float = 180, max_output: int = 400000) -> tuple[int, str]:
        """执行命令，返回 (退出码, 去 ANSI 的输出)。"""
        if not self.ws:
            self.connect()
        marker = f"DSH{uuid.uuid4().hex[:10]}"
        payload = f"{cmd}\r\n printf '<<<{marker}:%s>>>\\n' \"$?\"\r\n"
        self.ws.send(payload)
        out = ""
        deadline = time.time() + timeout
        found = None
        while time.time() < deadline:
            try:
                data = self.ws.recv()
            except websocket.WebSocketTimeoutException:
                continue
            except Exception as exc:  # noqa: BLE001
                raise RuntimeError(f"读取超时/断开: {exc}") from exc
            if isinstance(data, (bytes, bytearray)):
                data = data.decode("utf-8", "replace")
            out += data
            m = re.search(rf"<<<{marker}:(\d+)>>>", clean(out))
            if m:
                found = m
                break
            if len(out) > max_output:
                out = out[-max_output:]
        text = clean(out)
        code = -1
        if found:
            code = int(found.group(1))
            text = text[: found.start()]
        # 去掉残留的 shell 提示符行（连接建立时可能带入）
        lines = [ln for ln in text.splitlines()
                 if not re.match(r"^\s*\S+@\S+:[^$]*\$\s*$", ln)
                 and "stty -echo" not in ln]
        return code, "\n".join(lines).strip("\n")

    # ---------------------------------------------------------------- sudo
    def sudo(self, cmd: str, timeout: float = 600, password: str | None = None) -> tuple[int, str]:
        """以 sudo 执行命令（VM 的 openlab 需要密码）。"""
        import shlex
        pw = password or VM_PASS
        return self.run(f"printf '%s\\n' {shlex.quote(pw)} | sudo -S -p '' bash -lc "
                        f"{shlex.quote(cmd)} 2>&1", timeout=timeout)

    # ---------------------------------------------------------------- files
    def push_file(self, local: Path | str, remote: str, chunk: int = 60000) -> None:
        local = Path(local)
        data = base64.b64encode(local.read_bytes()).decode()
        self.run(f": > {remote}.b64", timeout=60)
        for i in range(0, len(data), chunk):
            part = data[i:i + chunk]
            self.run(f"printf '%s' '{part}' >> {remote}.b64", timeout=120)
        code, out = self.run(f"base64 -d {remote}.b64 > {remote} && rm -f {remote}.b64 && ls -l {remote}",
                             timeout=120)
        if code != 0:
            raise RuntimeError(f"上传失败: {out[:300]}")

    def pull_file(self, remote: str, local: Path | str) -> None:
        """拉取文件。适用于小文件（结果 JSON / 日志，<200KB）：单次 base64 传输。"""
        local = Path(local)
        local.parent.mkdir(parents=True, exist_ok=True)
        code, out = self.run(f"base64 -w0 {remote}; echo", timeout=180)
        if code != 0:
            raise RuntimeError(f"读取远端文件失败: {out[:300]}")
        b64 = "".join(t for t in out.split() if re.fullmatch(r"[A-Za-z0-9+/=]+", t))
        if not b64:
            raise RuntimeError(f"base64 内容为空: {out[:200]}")
        data = base64.b64decode(b64 + "=" * (-len(b64) % 4))
        local.write_bytes(data)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="VM shell 客户端")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("run")
    p.add_argument("command")
    p.add_argument("--timeout", type=float, default=180)
    p = sub.add_parser("push")
    p.add_argument("local")
    p.add_argument("remote")
    p = sub.add_parser("pull")
    p.add_argument("remote")
    p.add_argument("local")
    p = sub.add_parser("probe")
    args = ap.parse_args(argv)

    vm = VmShell()
    try:
        if args.cmd == "run":
            code, out = vm.run(args.command, timeout=args.timeout)
            print(out)
            print(f"\n[exit={code}]")
            return code if code >= 0 else 0
        if args.cmd == "push":
            vm.push_file(args.local, args.remote)
            print(f"[OK] {args.local} -> {args.remote}")
            return 0
        if args.cmd == "pull":
            vm.pull_file(args.remote, args.local)
            print(f"[OK] {args.remote} -> {args.local}")
            return 0
        if args.cmd == "probe":
            vm.connect()
            code, out = vm.run("hostname; whoami; pwd; ls -la ~/Desktop 2>/dev/null | head -30")
            print(out)
            return 0
    finally:
        vm.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
