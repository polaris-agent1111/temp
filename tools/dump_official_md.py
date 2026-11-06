#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Extract all official docx files to clean UTF-8 markdown."""
import io
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
OUT = DOCS / "official_markdown"
OUT.mkdir(parents=True, exist_ok=True)

def docx_to_md(docx_bytes: bytes) -> str:
    with zipfile.ZipFile(io.BytesIO(docx_bytes)) as z:
        if "word/document.xml" not in z.namelist():
            return ""
        xml_content = z.read("word/document.xml")
    root = ET.fromstring(xml_content)
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    
    # Also extract tables
    body = root.find(f"{{{ns['w']}}}body")
    if body is None:
        return ""
    
    lines = []
    for elem in body:
        tag = elem.tag.split("}")[-1]
        if tag == "p":
            texts = [t.text for t in elem.iter(f"{{{ns['w']}}}t") if t.text]
            p_text = "".join(texts).strip()
            if p_text:
                lines.append(p_text)
                lines.append("")
        elif tag == "tbl":
            # parse table
            table_rows = []
            for tr in elem.iter(f"{{{ns['w']}}}tr"):
                row = []
                for tc in tr.iter(f"{{{ns['w']}}}tc"):
                    cell_texts = [t.text for t in tc.iter(f"{{{ns['w']}}}t") if t.text]
                    row.append("".join(cell_texts).strip())
                table_rows.append(row)
            if table_rows:
                # render markdown table
                max_cols = max(len(r) for r in table_rows)
                header = table_rows[0] + [""] * (max_cols - len(table_rows[0]))
                lines.append("| " + " | ".join(header) + " |")
                lines.append("| " + " | ".join(["---"] * max_cols) + " |")
                for r in table_rows[1:]:
                    r = r + [""] * (max_cols - len(r))
                    lines.append("| " + " | ".join(r) + " |")
                lines.append("")
    return "\n".join(lines)

def main():
    # 1. Top level
    for d in DOCS.glob("*.docx"):
        txt = docx_to_md(d.read_bytes())
        out_f = OUT / "01_赛题说明.md"
        out_f.write_text(txt, encoding="utf-8")
        print("Wrote", out_f.name, len(txt), "bytes")

    # 2. Inside zip
    for zpath in DOCS.glob("*.zip"):
        with zipfile.ZipFile(zpath) as z:
            for info in z.infolist():
                if info.filename.endswith(".docx"):
                    try:
                        raw_name = info.filename.encode("cp437").decode("gbk")
                    except Exception:
                        raw_name = info.filename
                    txt = docx_to_md(z.read(info.filename))
                    if "websearch" in raw_name:
                        out_f = OUT / "02_websearch流模型.md"
                    elif "各模块" in raw_name or "模块使用" in raw_name:
                        out_f = OUT / "03_各模块使用说明.md"
                    elif "实验环境" in raw_name or "操作手册" in raw_name:
                        out_f = OUT / "04_实验详细操作手册.md"
                    else:
                        out_f = OUT / f"inner_{Path(raw_name).stem}.md"
                    out_f.write_text(txt, encoding="utf-8")
                    print("Wrote", out_f.name, len(txt), "bytes")

if __name__ == "__main__":
    main()
