#!/usr/bin/env bash
# 本地格式自检：校验器自测 + 当前 question 树校验。
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "== validate_pacer.py 自测 =="
python3 tools/validate_pacer.py --selftest

echo
echo "== 校验 question/1..6 =="
python3 tools/validate_pacer.py question

echo
echo "提示：官方 format_check_client 也可用，但它硬编码 /home/openlab/Desktop/question；"
echo "      日常改配置优先用上面的 validate_pacer.py。"
