#!/usr/bin/env python3
"""在竞赛云主机上执行命令。只用标准库。

本机没有到云主机的路由，唯一通道是竞赛平台的 WebSSH 代理：
  wss://<平台>/webssh/term?sshInfo=<base64(JSON)>&rows=..&cols=..
WebSocket 上收发的是终端原始文本。

口令：环境变量 IDSN_VM_PASS 优先，其次读 vm/secrets.json 的 vm_password。

用法：
  python vm/vmssh.py                      # 连通性自检
  python vm/vmssh.py "ls ~/Desktop"       # 执行一条命令
"""
import base64
import json
import os
import re
import socket
import ssl
import struct
import sys
import time
import uuid
from pathlib import Path
from urllib.parse import urlsplit

PLATFORM = os.environ.get("IDSN_TRIT_BASE", "https://218.2.108.11:40000")
VM_HOST = os.environ.get("IDSN_VM_HOST", "192.168.181.16")
VM_USER = os.environ.get("IDSN_VM_USER", "openlab")
SECRETS = Path(__file__).with_name("secrets.json")

ANSI_RE = re.compile(r"\x1b\[[0-9;?]*[a-zA-Z]|\x1b\][^\x07]*\x07|\r")
PROMPT_RE = re.compile(r"\S+@\S+:[^\s$#]*[$#]\s?")


def vm_password() -> str:
    pw = os.environ.get("IDSN_VM_PASS")
    if pw:
        return pw
    try:
        return json.loads(SECRETS.read_text("utf-8-sig"))["vm_password"]
    except (OSError, ValueError, KeyError):
        sys.exit("缺少口令：设置 IDSN_VM_PASS，或在 vm/secrets.json 写 {\"vm_password\": \"...\"}")


class WebSocket:
    """最小 WebSocket 客户端（RFC 6455）：只收发文本帧，不校验证书。"""

    def __init__(self, url: str, timeout: float):
        u = urlsplit(url)
        raw = socket.create_connection((u.hostname, u.port or 443), timeout=timeout)
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        self.sock = ctx.wrap_socket(raw, server_hostname=u.hostname)
        self.rfile = self.sock.makefile("rb")
        key = base64.b64encode(os.urandom(16)).decode()
        self.sock.sendall((
            f"GET {u.path}?{u.query} HTTP/1.1\r\n"
            f"Host: {u.netloc}\r\n"
            "Upgrade: websocket\r\nConnection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n"
        ).encode())
        status = self.rfile.readline()
        if b" 101 " not in status:
            raise ConnectionError(f"握手失败: {status!r}")
        while self.rfile.readline() not in (b"\r\n", b""):
            pass

    def send(self, text: str, opcode: int = 0x1) -> None:
        data = text.encode()
        n = len(data)
        head = bytes([0x80 | opcode])
        if n < 126:
            head += bytes([0x80 | n])
        elif n < 65536:
            head += bytes([0x80 | 126]) + struct.pack("!H", n)
        else:
            head += bytes([0x80 | 127]) + struct.pack("!Q", n)
        mask = os.urandom(4)
        self.sock.sendall(head + mask + bytes(b ^ mask[i % 4] for i, b in enumerate(data)))

    def _read(self, n: int) -> bytes:
        data = self.rfile.read(n)
        if len(data) < n:
            raise ConnectionError("连接已关闭")
        return data

    def recv(self) -> str:
        parts = []
        while True:
            b0, b1 = self._read(2)
            opcode, n = b0 & 0x0F, b1 & 0x7F
            if n == 126:
                n = struct.unpack("!H", self._read(2))[0]
            elif n == 127:
                n = struct.unpack("!Q", self._read(8))[0]
            mask = self._read(4) if b1 & 0x80 else None
            payload = self._read(n)
            if mask:
                payload = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
            if opcode == 0x8:
                raise ConnectionError("服务端关闭连接")
            if opcode == 0x9:
                self.send(payload.decode("latin-1"), opcode=0xA)
                continue
            if opcode == 0xA:
                continue
            parts.append(payload)
            if b0 & 0x80:
                return b"".join(parts).decode("utf-8", "replace")

    def close(self) -> None:
        try:
            self.sock.close()
        except OSError:
            pass


class VmShell:
    def __init__(self, timeout: float = 900):
        info = json.dumps({"username": VM_USER, "ipaddress": VM_HOST, "port": 22,
                           "password": vm_password(), "logintype": 0})
        b64 = base64.b64encode(info.encode()).decode()
        ws_base = PLATFORM.replace("https://", "wss://")
        self.ws = WebSocket(f"{ws_base}/webssh/term?sshInfo={b64}&rows=40&cols=160&closeTip=closed",
                            timeout)
        self._wait_prompt(30)
        self.ws.send("stty -echo 2>/dev/null\r\n")  # 关闭回显，命令文本不混进输出
        self._wait_prompt(10)

    def _wait_prompt(self, seconds: float) -> None:
        buf, deadline = "", time.time() + seconds
        while time.time() < deadline:
            try:
                buf += self.ws.recv()
            except (socket.timeout, ConnectionError):
                return
            if buf.rstrip().endswith(("$", "#")):
                return

    def run(self, cmd: str, timeout: float = 180) -> tuple[int, str]:
        """执行命令，返回 (退出码, 输出)。退出码 -1 表示超时没等到结束标记。"""
        marker = f"END{uuid.uuid4().hex[:10]}"
        self.ws.send(f"{cmd}\r\n printf '<<<{marker}:%s>>>\\n' \"$?\"\r\n")
        out, deadline = "", time.time() + timeout
        while time.time() < deadline:
            out += self.ws.recv()
            text = PROMPT_RE.sub("", ANSI_RE.sub("", out))
            m = re.search(rf"<<<{marker}:(\d+)>>>", text)
            if m:
                return int(m.group(1)), text[:m.start()].strip("\n")
        return -1, PROMPT_RE.sub("", ANSI_RE.sub("", out)).strip("\n")

    def close(self) -> None:
        self.ws.close()


def main() -> int:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "hostname; whoami; ls -la ~/Desktop | head -30"
    vm = VmShell()
    try:
        code, out = vm.run(cmd)
    finally:
        vm.close()
    print(out)
    print(f"[exit={code}]")
    return max(code, 0)


if __name__ == "__main__":
    sys.exit(main())
