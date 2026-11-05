#!/bin/bash
cd ~/Desktop || exit 1
echo "=== question tree ==="
find question -maxdepth 2 | sort
echo
echo "=== pacer files ==="
for f in $(find question -name '*.txt' 2>/dev/null | sort); do
  echo "--- $f"; cat "$f"; echo
done
echo "=== .bak dir ==="
ls -la ~/.bak 2>/dev/null | head -20
echo
echo "=== resources ==="
nproc; free -g | head -3; df -h /home | tail -1
echo
echo "=== sudo test ==="
sudo -n true 2>&1 && echo "SUDO_NOPASSWD=yes" || echo "SUDO_NOPASSWD=no"
echo
echo "=== network test ==="
timeout 8 curl -s -o /dev/null -w "env40000=%{http_code}\n" -k https://218.2.108.11:40000/ 2>&1
timeout 8 curl -s -o /dev/null -w "baidu=%{http_code}\n" https://www.baidu.com 2>&1
timeout 8 curl -s -o /dev/null -w "github=%{http_code}\n" https://github.com 2>&1
echo
echo "=== binaries help ==="
./format_check_client --help 2>&1 | head -30
echo "---"
./competition_question1 --help 2>&1 | head -30
echo "---"
./local_send_client --help 2>&1 | head -30
