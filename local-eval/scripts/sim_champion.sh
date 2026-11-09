#!/usr/bin/env bash
# 用离线仿真器评估冠军配置。
# 用法: ./scripts/sim_champion.sh [seeds] [output.json]
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SEEDS="${1:-100}"
OUT="${2:-$ROOT/runs/sim-champion.json}"

mkdir -p "$(dirname "$OUT")"
echo "仿真配置: $ROOT/configs/champion-1108-shot-steady.json"
echo "种子数:   $SEEDS"
echo "输出:     $OUT"
echo

python3 "$ROOT/tools/offline_pacer_sim.py" \
  --configs "$ROOT/configs/champion-1108-shot-steady.json" \
  --seeds "$SEEDS" \
  --json-out "$OUT"
