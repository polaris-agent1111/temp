import datetime as dt
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REVIEW_DIR = ROOT / "report" / "复核材料"
OUT = REVIEW_DIR / "review-manifest.json"

files = []
for p in sorted(REVIEW_DIR.rglob("*")):
    if p.is_file() and p.name != "review-manifest.json":
        rel_path = str(p.relative_to(REVIEW_DIR)).replace("\\", "/")
        raw = p.read_bytes()
        h = hashlib.sha256(raw).hexdigest()
        files.append({
            "path": rel_path,
            "bytes": len(raw),
            "sha256": h
        })

doc = {
    "package": "赛博coder 复核材料包 v3（王牌跨机制整形升级版）",
    "generated_at": dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "note": "本文件自身不列入；校验: 对每个 path 重算 sha256/bytes 与本表比对。best-configs 内配置与 runs/configs/ 源字节一致（cp -p 复制，sha256 已核对）。",
    "file_count": len(files),
    "files": files
}

OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"Generated review manifest with {len(files)} files at {OUT}")
