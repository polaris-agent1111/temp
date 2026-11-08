import json
from pathlib import Path

def main():
    results = Path("runs/results.jsonl")
    for line in results.read_text("utf-8").splitlines():
        if not line.strip():
            continue
        d = json.loads(line)
        if not d.get("valid"):
            continue
        cfg6 = d.get("config", {}).get("6", "")
        if "precise" in cfg6:
            for part in cfg6.split(","):
                if "max_pacing_rate=" in part:
                    rate = int(part.split("=")[1])
                    rate_mbps = rate * 8 / 1e6
                    if rate_mbps <= 92:
                        t6 = d["downloads"]["6.bin"]
                        tot = d["total_seconds"]
                        print(f"{d['tag']:35s} | 6.bin rate: {rate_mbps:5.1f}M | 6.bin time: {t6:6.3f}s | total: {tot:7.3f}s | note: {d.get('note', '')}")

if __name__ == "__main__":
    main()
