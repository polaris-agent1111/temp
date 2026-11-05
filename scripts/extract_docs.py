#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""解压竞赛附件包并抽取 docx 文本（含表格）为 markdown，便于阅读与检索。"""
from __future__ import annotations

import sys
import zipfile
from pathlib import Path

import docx

ROOT = Path(__file__).resolve().parents[1]
ZIP = ROOT / "docs" / "题目1附件.zip"
DEST = ROOT / "docs" / "题目1附件"
OUT = ROOT / "docs" / "extracted"


def fix_name(info: zipfile.ZipInfo) -> str:
    name = info.filename
    if not info.flag_bits & 0x800:  # not UTF-8 flagged -> cp437 bytes are actually gbk
        try:
            name = name.encode("cp437").decode("gbk")
        except Exception:
            pass
    return name


def extract() -> list[Path]:
    DEST.mkdir(parents=True, exist_ok=True)
    files: list[Path] = []
    with zipfile.ZipFile(ZIP) as zf:
        for info in zf.infolist():
            name = fix_name(info)
            target = DEST / name
            target.parent.mkdir(parents=True, exist_ok=True)
            if info.is_dir():
                continue
            with zf.open(info) as src, target.open("wb") as dst:
                dst.write(src.read())
            files.append(target)
    return files


def docx_to_md(path: Path) -> str:
    d = docx.Document(str(path))
    lines: list[str] = [f"# {path.name}", ""]
    # 保留文档顺序：用 body 元素遍历段落与表格
    from docx.table import Table
    from docx.text.paragraph import Paragraph

    body = d.element.body
    for child in body.iterchildren():
        tag = child.tag.split("}")[-1]
        if tag == "p":
            p = Paragraph(child, d)
            text = p.text.strip()
            if text:
                style = (p.style.name or "").lower()
                if "heading" in style:
                    level = "".join(ch for ch in style if ch.isdigit()) or "2"
                    lines.append("#" * min(6, int(level) + 1) + " " + text)
                else:
                    lines.append(text)
                lines.append("")
        elif tag == "tbl":
            t = Table(child, d)
            rows = []
            for row in t.rows:
                cells = []
                for cell in row.cells:
                    cells.append(" ".join(cell.text.split()))
                rows.append(cells)
            if not rows:
                continue
            width = max(len(r) for r in rows)
            lines.append("| " + " | ".join(f"c{i+1}" for i in range(width)) + " |")
            lines.append("|" + "---|" * width)
            for r in rows:
                r = r + [""] * (width - len(r))
                lines.append("| " + " | ".join(c.replace("|", "\\|") for c in r) + " |")
            lines.append("")
    return "\n".join(lines)


def main() -> int:
    files = extract()
    OUT.mkdir(parents=True, exist_ok=True)
    print(f"extracted {len(files)} files -> {DEST}")
    for f in files:
        print(" -", f.relative_to(ROOT), f"{f.stat().st_size/1024:.1f} KB")
        if f.suffix.lower() == ".docx":
            md = docx_to_md(f)
            out = OUT / (f.stem + ".md")
            out.write_text(md, "utf-8")
            print(f"   -> {out.relative_to(ROOT)}  ({len(md)} chars)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
