#!/bin/bash
cd ~/Desktop || exit 1
rm -rf /home/openlab/run1 && mkdir -p /home/openlab/run1
echo "=== run eval WITH sudo (nopasswd) ==="
START=$(date +%s)
sudo -n /home/openlab/Desktop/competition_question1 \
  --output-dir /home/openlab/run1 --result-json /home/openlab/run1/result.json 2>&1 | tail -40
RC=${PIPESTATUS[0]}
END=$(date +%s)
echo "RC=$RC ELAPSED=$((END-START))s"
echo
echo "=== result json ==="
cat /home/openlab/run1/result.json 2>/dev/null
echo
echo "=== output files ==="
ls -la /home/openlab/run1
