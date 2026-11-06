#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Extract clean text from all docx files in docs/."""
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
OUT = DOCS / "clean_extracted"
OUT.mkdir(parents=True, exist_ok=True)

def extract_docx_xml(docx_bytes: bytes) -> str:
    import io
    with zipfile.ZipFile(io.BytesIO(docx_bytes)) as z:
        if "word/document.xml" not in z.namelist():
            return ""
        xml_content = z.read("word/document.xml")
    
    root = ET.fromstring(xml_content)
    # XML namespace
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    
    paragraphs = []
    for p in root.iter(f"{{{ns['w']}}}p"):
        texts = [t.text for t in p.iter(f"{{{ns['w']}}}t") if t.text]
        if texts:
            paragraphs.append("".join(texts))
        else:
            paragraphs.append("")
    return "\n\n".join(paragraphs)

def main():
    # 1. Top-level docx
    for f in DOCS.glob("*.docx"):
        print(f"Extracting {f.name}...")
        try:
            txt = extract_docx_xml(f.read_bytes())
            out_file = OUT / (f.stem + ".clean.txt")
            out_file.write_text(txt, encoding="utf-8")
            print(f"  -> wrote {out_file.name} ({len(txt)} chars)")
        except Exception as e:
            print(f"  Error: {e}")

    # 2. Inside zip
    for zpath in DOCS.glob("*.zip"):
        print(f"Extracting from {zpath.name}...")
        with zipfile.ZipFile(zpath, "r") as z:
            for info in z.infolist():
                if info.filename.endswith(".docx"):
                    try:
                        raw_name = info.filename.encode("cp437").decode("gbk")
                    except Exception:
                        raw_name = info.filename
                    print(f"  Found inner docx: {raw_name}")
                    txt = extract_docx_xml(z.read(info.filename))
                    safe_stem = Path(raw_name).stem
                    out_file = OUT / (safe_stem + ".clean.txt")
                    out_file.write_text(txt, encoding="utf-8")
                    print(f"    -> wrote {out_file.name} ({len(txt)} chars)")

if __name__ == "__main__":
    main()
