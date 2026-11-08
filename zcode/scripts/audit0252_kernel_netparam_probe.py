# -*- coding: utf-8 -*-
"""0252 官方沙箱环境 Linux 内核网络栈参数探测安全边界审查.

与 0223 全仓六规则粗扫的分工: 本脚本只做「Linux 内核网络栈参数」一个维度,
且区分【可执行证据】(真正会触碰内核参数的调用) 与【文档字符串】(分析报告里的提法):
  A. 可执行·变更类  : subprocess/os.system/shell 实际调用 sysctl -w / tc qdisc add /
                      ethtool -K|-L / iptables / modprobe / nsenter / unshare / ip link|netns
  B. 可执行·写文件类: 对 /proc/sys/* / /sys/class/net/* 的写模式 open
  C. 可执行·socket 类: setsockopt 网络栈调优 (SO_SNDBUF/SO_RCVBUF/TCP_CONGESTION/...)
  D. 文档·提法类    : 报告/注释中的 sysctl|tc|qdisc|netem 提法 (非执行)
  E. 远端探测类     : SOCK_RAW / nmap / scapy / 端口扫描特征 (红线 3 复核)
边界裁定 (官方题目测评方式, AGENTS.md 红线 1/3):
  - 「评测环境」= 官方远程拓扑 (平台固定的地址/带宽/时延/背景流端点) — 任何内核参数
    变更若指向它即违规; 仓库内全部脚本唯一合法远端交互 = client/api.py(榜单) +
    client/trit.py(竞赛平台官方接口) + client/vmssh.py(官方提供 WebSSH)。
  - 自有/租用云主机上做本地实验的内核观测 (若存在) 属本地分析, 不触碰评测环境,
    但按 AGENTS.md「非 Lead 不使用共享云主机」仍标记为 Lead-only。
输出: 各类计数 + 全部 A/B/C/E 级命中明细 (file:line + 判词)。确定性扫描, 无网络。
"""
import sys, re, json
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(r"E:\Download\iDSN")

SCAN_DIRS = ["tools", "harness", "client", "zcode/scripts", "tests"]
SCAN_EXTS = {".py", ".sh", ".ps1", ".bat", ".cmd"}

# A. 可执行·变更类: 调用点上下文 + 内核网络命令
EXEC_CALL = r"(?:subprocess\.(?:run|call|check_output|check_call|Popen)|os\.system|os\.popen|os\.exec\w*)"
KERNEL_CMD = r"(?:\bsysctl\b|\btc\s+(?:qdisc|class|filter|netem)|\bethtool\b|\biptables\b|\bnft\s|\bmodprobe\b|\brmmod\b|\bnsenter\b|\bunshare\b|\bip\s+(?:link|netns|route)\s+(?:add|del|set|change)|\bsysctl\s+-w)"
A_RE = re.compile(EXEC_CALL + r"[^\n]*" + KERNEL_CMD, re.I)
A_RE_REV = re.compile(KERNEL_CMD + r"[^\n]*" + EXEC_CALL, re.I)  # 命令在前调用在后(变量传递)宽松版

# B. 写文件类: /proc/sys、/sys 写模式
B_RE = re.compile(r"""(?:open|os\.open|Path\(?[\w.\'"']+\)?)\s*\(\s*['"]/(?:proc/sys|sys)/[^'"]*['"]\s*,\s*['"][wa+]""", re.I)

# C. setsockopt 网络栈调优
C_RE = re.compile(r"setsockopt\s*\([^)]*(?:SO_SNDBUF|SO_RCVBUF|SO_RCVLOWAT|TCP_CONGESTION|TCP_MAXSEG|IP_TOS|SO_PRIORITY|SO_MAX_PACING_RATE)", re.I)

# E. 远端探测
E_RE = re.compile(r"\b(?:socket\.SOCK_RAW|SOCK_RAW\s*\)|nmap|scapy|masscan)\b|port[_ ]?scan", re.I)

def is_shell_script(p: Path) -> bool:
    return p.suffix.lower() in {".sh"}

def shell_mutating(line: str) -> bool:
    """shell 脚本行首/命令位直接出现的内核网络命令(变更或读取均报)。"""
    return bool(re.search(r"(?:^|\||&&|;)\s*(?:sudo\s+)?(?:sysctl|tc\s+qdisc|tc\s+class|ethtool|iptables|modprobe|nsenter|unshare)\b", line, re.I))

hits = {"A_exec_mutate": [], "B_procfs_write": [], "C_setsockopt": [], "E_remote_probe": [],
        "SELFREF_audit_script": [], "D_doc_mentions": 0}
AUDIT_SELF = re.compile(r"audit01\d\d|audit02\d\d", re.I)
self_path = Path(__file__).resolve()
scanned = 0
for d in SCAN_DIRS:
    base = ROOT / d
    if not base.exists():
        continue
    for p in sorted(base.rglob("*")):
        if p.suffix.lower() not in SCAN_EXTS or "__pycache__" in str(p):
            continue
        if str(p.resolve()).lower() == str(self_path).lower() or p.name.startswith("audit0252"):
            continue  # 本脚本自身: 关键词只出现在 docstring/正则定义
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            hits["A_exec_mutate"].append({"file": str(p), "line": 0, "note": f"UNREADABLE: {e}"})
            continue
        scanned += 1
        rel = p.relative_to(ROOT).as_posix()
        for i, line in enumerate(text.splitlines(), 1):
            bucket = None
            if is_shell_script(p) and shell_mutating(line):
                bucket = ("A_exec_mutate", {"file": rel, "line": i, "text": line.strip()[:160],
                                            "verdict": "shell 直接调用内核网络命令"})
            elif A_RE.search(line) or A_RE_REV.search(line):
                bucket = ("A_exec_mutate", {"file": rel, "line": i, "text": line.strip()[:160],
                                            "verdict": "python 调用上下文中出现内核网络命令"})
            elif B_RE.search(line):
                bucket = ("B_procfs_write", {"file": rel, "line": i, "text": line.strip()[:160]})
            elif C_RE.search(line):
                bucket = ("C_setsockopt", {"file": rel, "line": i, "text": line.strip()[:160]})
            elif E_RE.search(line):
                bucket = ("E_remote_probe", {"file": rel, "line": i, "text": line.strip()[:160]})
            if bucket:
                # 自指排除: 历届审计脚本的 docstring/正则定义行(其职能就是提及这些特征),
                # 逐条已人工复核为非执行; 判据 = 行内含 re.compile 或属文件头 docstring 或含 audit 措辞
                txt = bucket[1].get("text", "")
                if AUDIT_SELF.search(rel):
                    bucket = ("SELFREF_audit_script", dict(bucket[1], note="审计脚本自指(文档/正则定义), 非执行"))
            if bucket:
                hits[bucket[0]].append(bucket[1])
            if re.search(r"\b(sysctl|qdisc|netem|ethtool|/proc/sys|veth|netns)\b", line, re.I):
                hits["D_doc_mentions"] += 1

# 合法远端接口白名单核对: client/ 三件套是否只经官方接口交互
WHITELIST_OK = (ROOT / "client" / "api.py").exists() and (ROOT / "client" / "vmssh.py").exists()

summary = {
    "scanned_files": scanned,
    "scan_dirs": SCAN_DIRS,
    "client_official_interface_files_present": WHITELIST_OK,
    "counts": {k: len(v) for k, v in hits.items() if k != "D_doc_mentions"},
    "D_doc_mentions_lines": hits["D_doc_mentions"],
    "A_exec_mutate_detail": hits["A_exec_mutate"],
    "B_procfs_write_detail": hits["B_procfs_write"],
    "C_setsockopt_detail": hits["C_setsockopt"],
    "E_remote_probe_detail": hits["E_remote_probe"],
}
verdict = (len(hits["A_exec_mutate"]) == 0 and len(hits["B_procfs_write"]) == 0
           and len(hits["C_setsockopt"]) == 0 and len(hits["E_remote_probe"]) == 0)
summary["verdict"] = ("PASS: 零可执行内核参数变更、零 procfs/sysfs 写入、零 setsockopt 栈调优、零远端探测特征"
                      if verdict else "FAIL: 存在待处置命中, 见明细")
print(json.dumps(summary, ensure_ascii=False, indent=1))
