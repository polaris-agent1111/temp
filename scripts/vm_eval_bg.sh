#!/bin/bash
# 在云主机后台启动一次本地评测
# 用法: bash vm_eval_bg.sh <tag>
TAG=${1:-run}
cd /home/openlab/Desktop || exit 1
OUT="/home/openlab/evals/$TAG"
mkdir -p "$OUT"
rm -f "$OUT"/result.json "$OUT"/run.log
nohup sudo -n /home/openlab/Desktop/competition_question1 \
    --output-dir "$OUT" --result-json "$OUT/result.json" \
    > "$OUT/run.log" 2>&1 &
echo "STARTED pid=$! tag=$TAG dir=$OUT"
