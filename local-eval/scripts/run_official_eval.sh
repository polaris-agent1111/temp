#!/usr/bin/env bash
# ============================================================================
# 官方本地评测包装脚本（可选，重）
#
# 它做四件事：
#   1. 检查官方二进制的硬依赖是否看起来就绪；
#   2. 检测是否已有 competition_question1 在跑，避免和队友并发；
#   3. 备份 /home/openlab/Desktop/question，换成 local-eval/question；
#   4. 调官方二进制跑 N 次，结果落到 local-eval/evals/<tag>/run-*/。
#
# 重要：competition_question1 硬编码 /home/openlab/Desktop/question，
#       并且需要 root / containernet / Docker / TrafficGenerator / http_server。
#       这个脚本只负责“包装”，不能凭空安装这些依赖。
#
# 用法：
#   ./scripts/run_official_eval.sh                 # 跑 1 次
#   REPEAT=3 ./scripts/run_official_eval.sh        # 跑 3 次取平均
#   TAG=my-test REPEAT=3 ./scripts/run_official_eval.sh
#   KEEP=1 ./scripts/run_official_eval.sh          # 跑完不恢复原 question
#   FORCE=1 ./scripts/run_official_eval.sh         # 跳过并发检查（危险）
# ============================================================================
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BIN="${BIN:-$ROOT/bin/competition_question1}"
WORKDIR="${WORKDIR:-/home/openlab/Desktop}"
QUESTION_SRC="${QUESTION_SRC:-$ROOT/question}"
OUT_ROOT="${OUT_ROOT:-$ROOT/evals}"
TAG="${TAG:-official-$(date +%Y%m%d-%H%M%S)}"
REPEAT="${REPEAT:-1}"
KEEP="${KEEP:-0}"
FORCE="${FORCE:-0}"

die() { echo "错误: $*" >&2; exit 1; }
info() { echo "== $* =="; }

# ---------------------------------------------------------------------------
# 0. 基本检查
# ---------------------------------------------------------------------------
[[ -x "$BIN" ]] || die "找不到可执行文件: $BIN"
[[ -d "$QUESTION_SRC" ]] || die "找不到配置树: $QUESTION_SRC"
for i in 1 2 3 4 5 6; do
  [[ -f "$QUESTION_SRC/$i/pacer.txt" ]] || die "缺少 $QUESTION_SRC/$i/pacer.txt"
done

# 官方二进制硬编码 /home/openlab/Desktop/question；换路径会找不到配置。
if [[ "$WORKDIR" != "/home/openlab/Desktop" ]]; then
  die "WORKDIR 必须是 /home/openlab/Desktop（二进制硬编码该路径）；当前: $WORKDIR"
fi

if [[ "$(id -u)" -eq 0 ]]; then
  SUDO=()
else
  command -v sudo >/dev/null 2>&1 || die "需要 root 或 sudo"
  SUDO=(sudo)
fi

# 并发保护：containernet/OVS 是全局资源，两个评测会互相污染。
if [[ "$FORCE" != "1" ]]; then
  if pgrep -af 'competition_question1' | grep -v -E "grep|$$" >/dev/null 2>&1; then
    echo "检测到已有 competition_question1 进程：" >&2
    pgrep -af 'competition_question1' | grep -v -E "grep|$$" >&2 || true
    die "为避免和队友的评测冲突，已退出。确认安全后可 FORCE=1 重跑。"
  fi
fi

# 依赖提示（不强制阻断，方便先看日志定位）
info "环境检查"
for p in docker python3; do
  command -v "$p" >/dev/null 2>&1 && echo "  [ok] $p" || echo "  [warn] 缺少 $p"
done
if "${SUDO[@]}" test -d /root/containernet 2>/dev/null; then
  echo "  [ok] /root/containernet"
else
  echo "  [warn] 看不到 /root/containernet（官方评测大概率会失败）"
fi
if "${SUDO[@]}" test -d /home/TrafficGenerator 2>/dev/null; then
  echo "  [ok] /home/TrafficGenerator"
else
  echo "  [warn] 看不到 /home/TrafficGenerator（通常在容器/镜像里，宿主机看不到不一定是问题）"
fi

# ---------------------------------------------------------------------------
# 1. 备份原 question，换成仓库里的冠军/候选配置
# ---------------------------------------------------------------------------
mkdir -p "$OUT_ROOT"
BACKUP="$OUT_ROOT/_question-backup-$TAG"
HAD_ORIGINAL=0
if [[ -d "$WORKDIR/question" ]]; then
  HAD_ORIGINAL=1
  info "备份原 question -> $BACKUP"
  rm -rf "$BACKUP"
  cp -a "$WORKDIR/question" "$BACKUP"
fi

restore() {
  if [[ "$KEEP" == "1" ]]; then
    echo "KEEP=1：保留 $WORKDIR/question（评测配置）"
    return 0
  fi
  info "恢复原 question"
  "${SUDO[@]}" rm -rf "$WORKDIR/question" 2>/dev/null || rm -rf "$WORKDIR/question"
  if [[ "$HAD_ORIGINAL" == "1" ]]; then
    "${SUDO[@]}" cp -a "$BACKUP" "$WORKDIR/question" 2>/dev/null \
      || cp -a "$BACKUP" "$WORKDIR/question"
  fi
}
trap restore EXIT

info "部署评测配置"
"${SUDO[@]}" rm -rf "$WORKDIR/question" 2>/dev/null || rm -rf "$WORKDIR/question"
cp -a "$QUESTION_SRC" "$WORKDIR/question"

# ---------------------------------------------------------------------------
# 2. 跑官方评测
# ---------------------------------------------------------------------------
mkdir -p "$OUT_ROOT/$TAG"
for i in $(seq 1 "$REPEAT"); do
  OUT="$OUT_ROOT/$TAG/run-$i"
  mkdir -p "$OUT"
  info "第 $i/$REPEAT 次：$OUT"
  set +e
  ( cd "$WORKDIR" && "${SUDO[@]}" "$BIN" \
      --output-dir "$OUT" \
      --result-json "$OUT/result.json" \
      --format-log-dir "$OUT/format-log" ) 2>&1 | tee "$OUT/run.log"
  rc=${PIPESTATUS[0]}
  set -e
  echo "$rc" > "$OUT/RC"
  if [[ "$rc" -ne 0 ]]; then
    echo "第 $i 次退出码 $rc；日志: $OUT/run.log" >&2
  fi
done

# ---------------------------------------------------------------------------
# 3. 汇总
# ---------------------------------------------------------------------------
info "汇总"
python3 "$ROOT/tools/collect_results.py" --evals-dir "$OUT_ROOT/$TAG" || true
echo
echo "原始结果: $OUT_ROOT/$TAG"
echo "提示：本地单次噪声很大；至少跑 3 次看均值和标准差，不要用单次最好值下结论。"
