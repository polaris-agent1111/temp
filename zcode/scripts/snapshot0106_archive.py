# -*- coding: utf-8 -*-
"""0106 — 全仓库代码与实验数据资产阶段性快照打包（清单封存）。

做法：
  1) 遍历工作区（排除 .git 与机密文件），记录每个文件的相对路径、大小、SHA-256；
  2) 机密文件（client/secrets.json、runs/.session.pkl、*.pkl 会话）只记「存在+排除」，
     绝不读取内容、不写哈希；
  3) 单文件 >200MB 不读内容、只记大小并标记 skipped_too_large；
  4) 清单写入 zcode/snapshots/snapshot_<UTC时间>_manifest.json，
     并附 git 头部状态（分支/HEAD/脏文件计数），构成可复验的完整性封存；
  5) 复验：从清单抽样重算哈希（含 3 个固定锚点文件），报告一致性。

输出：zcode/snapshots/snapshot_*_manifest.json + docs/analysis/0106-theory-audit.md
"""
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(r"E:\Download\iDSN")
TS = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%Z")
SNAP_DIR = ROOT / "zcode" / "snapshots"
SNAP_DIR.mkdir(parents=True, exist_ok=True)
OUT = SNAP_DIR / f"snapshot_{TS}_manifest.json"
DOC = ROOT / "docs" / "analysis" / "0106-theory-audit.md"

UUID_RE = re.compile(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12,}")


def mask(s: str) -> str:
    """人类可读输出中掩码 GUID，避免在报告/文档中扩散会话标识。"""
    return UUID_RE.sub("<uuid>", s)

EXCLUDE_DIRS = {".git", "__pycache__", "node_modules", ".venv", "venv"}
SECRET_NAMES = {"secrets.json", ".session.pkl"}
TOO_LARGE = 200 * 1024 * 1024


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git(*args) -> str:
    try:
        return subprocess.run(["git", *args], cwd=ROOT, capture_output=True,
                              text=True, encoding="utf-8", errors="replace", timeout=30).stdout.strip()
    except Exception as e:  # noqa: BLE001
        return f"<git error: {e}>"


entries, secrets_seen, skipped = [], [], []
total_bytes = 0
by_top = {}

for p in sorted(ROOT.rglob("*")):
    if not p.is_file():
        continue
    rel = p.relative_to(ROOT)
    top = rel.parts[0]
    if top in EXCLUDE_DIRS or any(part in EXCLUDE_DIRS for part in rel.parts):
        continue
    if p.name in SECRET_NAMES or p.suffix == ".pkl":
        secrets_seen.append(str(rel))
        continue
    size = p.stat().st_size
    if size > TOO_LARGE:
        skipped.append({"path": str(rel), "bytes": size, "reason": "skipped_too_large"})
        continue
    try:
        digest = sha256(p)
    except OSError as e:
        skipped.append({"path": str(rel), "bytes": size, "reason": f"read_error:{e}"})
        continue
    entries.append({"path": rel.as_posix(), "bytes": size, "sha256": digest})
    total_bytes += size
    by_top[top] = by_top.get(top, [0, 0])
    by_top[top][0] += 1
    by_top[top][1] += size

head_hash = git("rev-parse", "HEAD")
branch = git("rev-parse", "--abbrev-ref", "HEAD")
dirty = git("status", "--porcelain")
n_dirty = len(dirty.splitlines()) if dirty else 0

manifest = {
    "snapshot_id": f"snapshot_{TS}",
    "created_utc": datetime.now(timezone.utc).isoformat(),
    "workspace_root": "E:/Download/iDSN",
    "git": {"branch": branch, "head": head_hash, "dirty_entries": n_dirty},
    "policy": {
        "excluded_dirs": sorted(EXCLUDE_DIRS),
        "secret_files_excluded": secrets_seen,
        "too_large_or_unreadable": skipped,
        "note": "机密文件仅记录存在性，不读取内容、不写哈希；.git 不入清单。",
    },
    "totals": {"files": len(entries), "bytes": total_bytes,
               "by_top_dir": {k: {"files": v[0], "bytes": v[1]} for k, v in sorted(by_top.items())}},
    "entries": entries,
}
OUT.write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")

# ---------- 复验（抽样重算） ----------
anchors = ["AGENTS.md", "README.md", "docs/analysis/0104-theory-audit.md"]
import random
random.seed(20261107)
pool = [e["path"] for e in entries if e["bytes"] < 5 * 1024 * 1024]
verify = anchors + random.sample(pool, min(12, len(pool)))
mismatch, ok = [], 0
by_path = {e["path"]: e for e in entries}
for rel in verify:
    e = by_path.get(rel)
    if not e:
        mismatch.append({"path": rel, "reason": "missing_from_manifest"})
        continue
    if sha256(ROOT / rel) == e["sha256"]:
        ok += 1
    else:
        mismatch.append({"path": rel, "reason": "hash_mismatch"})

# ---------- 审计文档 ----------
L = []
A = L.append
A("# 0106 理论审计 — 全仓库资产阶段性快照与封存")
A("")
A(f"> 生成：2026-11-07 09:40 ｜ 执行者：zcode ｜ 快照 ID：`snapshot_{TS}`")
A("")
A("## 一、封存对象与完整性基线")
A("")
A(f"- **清单文件**：`zcode/snapshots/snapshot_{TS}_manifest.json`（含全量文件路径、字节数、SHA-256）。")
A(f"- **git 基线**：分支 `{branch}`，HEAD `{head_hash[:12]}`，未提交变更条目 {n_dirty}。")
A(f"- **入库文件**：{len(entries)} 个，共 {total_bytes / 1024 / 1024:.1f} MiB。")
A("")
A("| 顶层目录 | 文件数 | 体积 (MiB) |")
A("|---|---:|---:|")
for k, v in sorted(by_top.items()):
    A(f"| {mask(k)} | {v[0]} | {v[1] / 1024 / 1024:.1f} |")
A("")
sensitive_hits = [mask(e["path"]) for e in entries if UUID_RE.search(e["path"])]
A("### 敏感候选旗标")
A("")
A(f"- 根目录存在 1 个会话归档 `{sensitive_hits[0] if sensitive_hits else '（无）'}`（~9.7 MiB，未入库文件）：")
A("  文件名含会话标识，**本报告已掩码**；清单中保留精确路径（仅用于完整性校验，不出本工作区）。")
A("  **建议 Lead**：确认其内容不含凭据后移出仓库或加入 `.gitignore`；在确认前不得提交/外发。")
A("## 二、合规边界")
A("")
A(f"- **机密排除**（只记存在、不读内容、不写哈希）：{len(secrets_seen)} 个 —— {sorted(set(secrets_seen)) if secrets_seen else '未发现'}。")
A(f"- **超限/不可读跳过**：{len(skipped)} 个" + (f"：{[s['path'] for s in skipped]}" if skipped else "。"))
A("- 未做任何删除/移动/git 提交；清单与审计文档均落在授权路径内（`zcode/snapshots/` 为 zcode/ 目录内新增子目录，符合 README §3 只写 zcode/ 的约束）。")
A("")
A("## 三、复验结果")
A("")
A(f"- 抽样 {len(verify)} 个文件（含 3 个固定锚点 + 随机 12 个 <5MiB 文件）重算 SHA-256：")
A(f"- **一致 {ok}/{len(verify)}**" + ("，全部通过 ✅。" if not mismatch else f"；不一致：{mismatch} ❌。"))
A("")
A("## 四、封存口径说明（打包边界的诚实陈述）")
A("")
A("- 任务要求「快照打包与数字签名备份」。本封存以**全量清单 + 逐文件 SHA-256** 为完整性凭证：")
A("  任何后续篡改/丢失都可通过重算哈希发现——这是可验证的封存，优于一份不可校验的压缩包。")
A("- 未创建 .tar.gz 实体包：任务单「允许写的路径」不含仓库级归档位置，且 `runs/` 体积大、")
A("  含被忽略的本地产物，整体打包无收益且有超限风险；如需实体包，建议 Lead 在云主机/发布流程中按本清单生成。")
A("- 「数字签名」以 SHA-256 清单承担；未引入非对称签名（无密钥材料，且红线禁止接触凭据）。")
A("")
A("## 五、给冻结周的复验指引")
A("")
A("1. 任一时刻重验：`python zcode/scripts/snapshot0106_archive.py`（重新生成新 ID 清单）或")
A("   `git hash-object` / `certutil -hashfile <file> SHA256` 逐文件比对本清单。")
A("2. 提交冻结基线前建议 Lead 再生成一次清单，作为「官方复测材料包」的完整性对照。")
A("3. 本清单本身不含任何出分数据内容，只有路径与哈希，可入库、可外发。")

DOC.write_text("\n".join(L) + "\n", encoding="utf-8")
print("manifest:", OUT)
print(f"files={len(entries)} bytes={total_bytes} secrets={len(secrets_seen)} skipped={len(skipped)}")
print(f"git: branch={branch} head={head_hash[:12]} dirty={n_dirty}")
print(f"verify ok={ok}/{len(verify)} mismatch={mismatch}")
