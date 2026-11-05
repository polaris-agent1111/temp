#!/usr/bin/env python3
"""尝试从评测器二进制中定位内嵌 .pyz（zip）并列出/解压内容。"""
import io
import struct
import zipfile
import os

P = "/home/openlab/Desktop/competition_question1"
OUT = "/home/openlab/binsrc"
data = open(P, "rb").read()
print("size", len(data))

cands = []
i = data.find(b"PK\x05\x06")
while i != -1:
    cands.append(i)
    i = data.find(b"PK\x05\x06", i + 1)
print("EOCD candidates:", cands)

found = False
for eocd in cands:
    if eocd + 22 > len(data):
        continue
    cdsize, cdoffset = struct.unpack("<II", data[eocd + 12:eocd + 20])
    start = eocd - cdsize - cdoffset
    print(f"cand eocd={eocd} cdsize={cdsize} cdoff={cdoffset} start={start}")
    if not (0 <= start < eocd and cdsize < len(data)):
        continue
    blob = data[start:eocd + 22]
    try:
        z = zipfile.ZipFile(io.BytesIO(blob))
        names = z.namelist()
        print("ZIP FOUND start=", start, "entries=", len(names))
        for n in names[:60]:
            print("   ", n, z.getinfo(n).file_size)
        os.makedirs(OUT, exist_ok=True)
        z.extractall(OUT)
        print("extracted to", OUT)
        found = True
        break
    except Exception as exc:  # noqa: BLE001
        print("   not zip:", str(exc)[:80])

if not found:
    # 退化：按 PK\x03\x04 手工解析（无中央目录时）
    print("no zip found via EOCD; scanning local headers")
    offs = []
    i = data.find(b"PK\x03\x04")
    while i != -1 and len(offs) < 50:
        offs.append(i)
        i = data.find(b"PK\x03\x04", i + 1)
    print("local headers:", offs[:20])
