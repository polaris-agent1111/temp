#!/usr/bin/env bash
# 用离线仿真器评估一组“六目录同配”的 leak_bucket 参数。
# 用法: ./scripts/sim_uniform.sh <leak_rate> <bucket_cap> <leak_interval_us> [seeds]
# 例:   ./scripts/sim_uniform.sh 40 40 4000 100
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RATE="${1:?需要 leak_rate}"
CAP="${2:?需要 bucket_cap}"
INT="${3:?需要 leak_interval_us}"
SEEDS="${4:-100}"

SPEC="leak_bucket:leak_rate=${RATE},bucket_cap=${CAP},leak_interval_us=${INT}"
OUT="$ROOT/runs/sim-uniform-${RATE}-${CAP}-${INT}.json"
mkdir -p "$ROOT/runs"

echo "配置: $SPEC"
echo "种子: $SEEDS"
python3 "$ROOT/tools/offline_pacer_sim.py" \
  --uniform "$SPEC" --seeds "$SEEDS" --json-out "$OUT"
