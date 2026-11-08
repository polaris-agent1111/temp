from pathlib import Path
for tid in ["0098", "0099", "0100"]:
    reps = list(Path("zcode/reports").glob(f"{tid}*.md"))
    print(tid, "Reports:", reps)
