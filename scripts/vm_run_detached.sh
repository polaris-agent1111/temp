#!/bin/bash
# 在云主机里“完全脱离会话”地跑一次本地评测
# 用法: bash vm_run_detached.sh <tag>
TAG=${1:?tag required}
OUT="/home/openlab/evals/$TAG"
mkdir -p "$OUT"
rm -f "$OUT"/run.log "$OUT"/result.json "$OUT"/RC "$OUT"/DONE
cd /home/openlab/Desktop || exit 1
setsid nohup bash -c "sudo -n /home/openlab/Desktop/competition_question1 --output-dir '$OUT' --result-json '$OUT/result.json' > '$OUT/run.log' 2>&1; echo \$? > '$OUT/RC'; touch '$OUT/DONE'" \
  < /dev/null > /dev/null 2>&1 &
echo "STARTED tag=$TAG dir=$OUT"
