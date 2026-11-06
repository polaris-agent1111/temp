"""测试「官方惩罚 = CPU 核数少导致定时器粒度变大」假说。

把本地评测器用 taskset 限制到 1 个核上跑，看低包速率配置(24/60/4000)是否
相对高包速率配置(36/40/4000)变差——官方里 24/60=150.7 而 36/40=133.1。

用法: python tools/test_1core.py [--cores 0] [--rounds 1]
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
PY = sys.executable

from client.vmssh import VmShell  # noqa: E402

CONFIGS = {
    "1c-low": (24, 60, 4000),
    "1c-high": (36, 40, 4000),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cores", default="0")
    ap.add_argument("--rounds", type=int, default=1)
    args = ap.parse_args()

    runner = f"""#!/bin/bash
TAG=$1; OUT="/home/openlab/evals/$TAG"
mkdir -p "$OUT"
rm -f "$OUT/run.log" "$OUT/result.json" "$OUT/RC" "$OUT/DONE"
cd /home/openlab/Desktop || exit 1
setsid nohup bash -c "sudo -n taskset -c {args.cores} /home/openlab/Desktop/competition_question1 --output-dir '$OUT' --result-json '$OUT/result.json' > '$OUT/run.log' 2>&1; echo \\$? > '$OUT/RC'; touch '$OUT/DONE'" \
  < /dev/null > /dev/null 2>&1 &
echo "STARTED $TAG"
"""

    vm = VmShell()
    vm.connect()
    # 写 runner
    b64 = __import__("base64").b64encode(runner.encode()).decode()
    vm.run(f"echo {b64} | base64 -d > /home/openlab/vm_run_1core.sh && chmod +x /home/openlab/vm_run_1core.sh")

    out = []
    for rnd in range(1, args.rounds + 1):
        for tag, (rate, cap, iv) in CONFIGS.items():
            t = f"{tag}-r{rnd}"
            rc = subprocess.run([PY, "harness/upload_config.py", "--tag", t, "--mode", "leak_bucket",
                                 "--params", f"leak_rate={rate}", f"bucket_cap={cap}",
                                 f"leak_interval_us={iv}"], cwd=ROOT)
            if rc.returncode != 0:
                print(f"[ERR] upload {t}")
                continue
            vm.run(f"bash /home/openlab/vm_run_1core.sh {t}")
            print(f"[start] {t} rate={rate} cap={cap} iv={iv}", flush=True)
            deadline = time.time() + 420
            res = None
            while time.time() < deadline:
                time.sleep(15)
                code, o = vm.run(f"test -f /home/openlab/evals/{t}/DONE && cat /home/openlab/evals/{t}/result.json | base64 -w0; echo", timeout=60)
                s = o.strip()
                if s and len(s) > 20:
                    try:
                        import base64
                        res = json.loads(base64.b64decode(s).decode())
                        break
                    except Exception:
                        pass
            if res:
                tot = res.get("total_seconds") or res.get("total") or res
                print(f"[result] {t}: {str(tot)[:200]}", flush=True)
                out.append((t, res))
            else:
                print(f"[timeout] {t}", flush=True)

    print("\n=== 汇总 ===")
    for t, r in out:
        print(t, json.dumps(r, ensure_ascii=False)[:200])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
