from pathlib import Path
for tid in ["0098", "0099", "0100"]:
    for f in Path("zcode/requests").glob(f"{tid}*.md"):
        print("=== File:", f.name)
        print(f.read_text("utf-8")[:300])
