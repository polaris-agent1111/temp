#!/bin/bash
cd ~/Desktop || exit 1
# VM 的 openlab 密码不硬编码：优先环境变量 IDSN_VM_PASS，其次 ~/.idsn_vm_pass 文件
VM_PASS="${IDSN_VM_PASS:-$(cat ~/.idsn_vm_pass 2>/dev/null)}"
if [ -z "$VM_PASS" ]; then
  echo "[ERR] 缺少 VM 密码：export IDSN_VM_PASS 或把密码写入 ~/.idsn_vm_pass" >&2
  exit 1
fi
echo "=== sudo rules ==="
printf '%s\n' "$VM_PASS" | sudo -S -p '' -l 2>&1 | head -30
echo
echo "=== run eval WITHOUT sudo ==="
mkdir -p /home/openlab/run1
/usr/bin/time -f "REAL_SECONDS=%e" timeout 900 ./competition_question1 \
  --output-dir /home/openlab/run1 --result-json /home/openlab/run1/result.json 2>&1 | tail -40
echo
echo "=== result json ==="
cat /home/openlab/run1/result.json 2>/dev/null | head -60
echo
echo "=== output files ==="
ls -la /home/openlab/run1
