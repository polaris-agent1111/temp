#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Dump all docs to clean UTF-8 markdown file."""
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
    # Let's inspect the files
    all_docs = {}
    for f in DOCS.glob("*.docx"):
        txt = extract_docx_xml(f.read_bytes())
        all_docs[f.stem] = txt

    for zpath in DOCS.glob("*.zip"):
        with zipfile.ZipFile(zpath, "r") as z:
            for info in z.infolist():
                if info.filename.endswith(".docx"):
                    try:
                        name = info.filename.encode("cp437").decode("gbk")
                    except Exception:
                        name = info.filename
                    txt = extract_docx_xml(z.read(info.filename))
                    all_docs[Path(name).stem] = txt

    # Write each out
    for k, v in all_docs.items():
        # sanitize filename
        clean_name = "".join(c for c in k if c.isalnum() or c in ("-", "_", " "))
        if not clean_name:
            clean_name = "doc_" + str(len(k))
        p = OUT / f"{clean_name}.md"
        p.write_text(f"# {k}\n\n{v}", encoding="utf-8")
        print(f"Wrote {p.name} ({len(v)} chars)")

if __name__ == "__main__":
    main()
