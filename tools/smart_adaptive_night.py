#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""智能两波式自适应夜间提交调度器（2 + 3 闭环体系）。

业务逻辑：
1. 等待至北京时间 00:05（额度刷新后 5 分钟避开高峰并发）；
2. 第一波（Wave 1）：提交 2 发低风险探测
   - Shot 1 (基准锚点): leak 36/40/4000（已知 133.086s，标定凌晨评测机状态与环境漂移）
   - Shot 2 (核心探针): tb 40/40/r36@4k（与 R1 速率完全同构，单变量测在途旁路）
3. 闭环决策窗口（约 00:05 ~ 00:45）：
   - 轮询官方榜单 API http://47.120.64.152:5000/api/leaderboard（每 60 秒）；
   - 抓取我方最新出分，解析 Shot 1 与 Shot 2 得分；
4. 第二波自适应触发（Wave 2，消耗剩余 3 发额度）：
   - 分支 A（旁路验证通过：Shot 2 <= 132.0s 或 Shot 2 < Shot 1）：
     自动点火王牌夺冠阵容 runs/submit_plan_1107_wave2_bypass.json
     (Shot 3: 90M/96M 细粒度平滑 -> 冲击 117~120s;
      Shot 4: 96M/96M 满线速平滑 -> 冲击 115~118s;
      Shot 5: 王牌复投吃 min-of-N 极值红利)
   - 分支 B（异常回退：Shot 2 > 135.0s 或出现平台惩罚）：
     自动切换至保守最小桶回退方案 runs/submit_plan_1107_wave2_fallback.json
   - 超时兜底（若 60 分钟内榜单未刷新）：默认安全执行分支 A。

用法：
  python tools/smart_adaptive_night.py --at "2026-11-07 00:05"
  python tools/smart_adaptive_night.py --dry-run
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable

BOARD_URL = "http://47.120.64.152:5000/api/leaderboard"
TEAM = "赛博coder"

WAVE1_PLAN = ROOT / "runs" / "submit_plan_1107_wave1.json"
WAVE2_BYPASS = ROOT / "runs" / "submit_plan_1107_wave2_bypass.json"
WAVE2_FALLBACK = ROOT / "runs" / "submit_plan_1107_wave2_fallback.json"
LOG_FILE = ROOT / "runs" / "adaptive_night_log.jsonl"


def log_event(event: str, **kwargs) -> None:
    now_str = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    rec = {"ts": now_str, "event": event, **kwargs}
    print(f"[{now_str}] [{event}] {json.dumps(kwargs, ensure_ascii=False)}", flush=True)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def wait_until(target: dt.datetime) -> None:
    while True:
        now = dt.datetime.now()
        left = (target - now).total_seconds()
        if left <= 0:
            return
        print(f"[wait] 距目标 {target:%m-%d %H:%M} 还有 {left/60:.1f} 分钟 (当前 {now:%H:%M:%S})", flush=True)
        time.sleep(min(300, max(15, left)))


def run_plan(plan_path: Path, yes: bool = True) -> int:
    cmd = [PY, str(ROOT / "tools" / "submit_batch.py"), "--plan", str(plan_path)]
    if yes:
        cmd.append("--yes")
    print(f"\n$ {' '.join(cmd)}", flush=True)
    return subprocess.call(cmd, cwd=str(ROOT))


def fetch_team_attempts() -> list[dict]:
    try:
        req = urllib.request.Request(BOARD_URL)
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        for p in (data.get("leaderboard") or {}).get("problems") or []:
            for s in p.get("submissions") or []:
                if s.get("team") == TEAM:
                    return list(s.get("attempts") or [])
    except Exception as exc:
        print(f"[poll-warn] 拉取榜单失败: {exc}", flush=True)
    return []


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--at", default="2026-11-07 00:05")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--timeout-min", type=float, default=60.0)
    ap.add_argument("--poll-sec", type=int, default=60)
    args = ap.parse_args(argv)

    log_event("init", target_at=args.at, dry_run=args.dry_run)

    if not args.dry_run and args.at.lower() != "now":
        target = dt.datetime.strptime(args.at.strip(), "%Y-%m-%d %H:%M")
        wait_until(target)

    # ================= 第一波：提交 Wave 1 (2 发) =================
    log_event("start_wave1", plan=str(WAVE1_PLAN))
    baseline_attempts = fetch_team_attempts()
    baseline_count = len(baseline_attempts)
    print(f"[status] 当前已出分历史记录数: {baseline_count}")

    if not args.dry_run:
        rc1 = run_plan(WAVE1_PLAN, yes=True)
        if rc1 != 0:
            log_event("error_wave1", rc=rc1)
            print(f"[ERR] 第一波提交失败，退出码 {rc1}")
            return rc1
    else:
        print("[dry-run] 演练执行 Wave 1")
        run_plan(WAVE1_PLAN, yes=False)

    log_event("wave1_submitted", baseline_count=baseline_count)

    if args.dry_run:
        print("[dry-run] 演练模式结束，退出")
        return 0

    # ================= 闭环监测：等待 Wave 1 出分 =================
    print(f"\n===== 正在等待官方出分（目标：新增 2 次出分，超时限额 {args.timeout_min} 分钟）=====")
    t_start = time.time()
    t_deadline = t_start + args.timeout_min * 60
    new_attempts = []

    while time.time() < t_deadline:
        time.sleep(args.poll_sec)
        cur_attempts = fetch_team_attempts()
        if len(cur_attempts) > baseline_count:
            diff = len(cur_attempts) - baseline_count
            print(f"[{dt.datetime.now():%H:%M:%S}] 榜单已更新！检测到 {diff} 次新出分")
            if diff >= 2:
                new_attempts = cur_attempts[baseline_count:]
                break
            else:
                print(f"已出分 {diff}/2 条，继续等待另一条...")
        else:
            elapsed = (time.time() - t_start) / 60
            print(f"[{dt.datetime.now():%H:%M:%S}] 已等待 {elapsed:.1f} 分钟，榜单尚未刷新...", flush=True)

    # ================= 研判决策：选择分支 A 或 B =================
    chosen_plan = WAVE2_BYPASS
    branch_name = "Branch_A_Bypass"
    reason = "默认旁路冲冠"

    if len(new_attempts) >= 2:
        # new_attempts[0] 是 Shot 1 (leak 36/40)，new_attempts[1] 是 Shot 2 (tb 36)
        s1 = float(new_attempts[0].get("download_seconds", 999))
        s2 = float(new_attempts[1].get("download_seconds", 999))
        log_event("wave1_scores", shot1_leak=s1, shot2_tb=s2)
        print(f"\n[出分对比] Shot 1 (leak 36/40): {s1:.4f}s | Shot 2 (tb 40/40/r36): {s2:.4f}s")

        if s2 <= 132.0 or s2 < s1:
            branch_name = "Branch_A_Bypass"
            chosen_plan = WAVE2_BYPASS
            reason = f"tb 实测有效 ({s2:.2f}s <= 132s 或优于 leak {s1:.2f}s) -> 全面点火王牌夺冠阵容"
        else:
            branch_name = "Branch_B_Fallback"
            chosen_plan = WAVE2_FALLBACK
            reason = f"tb 表现异常 ({s2:.2f}s > 132s 且劣于 leak) -> 切换至保守最小桶剪刀差方案"
    else:
        log_event("wave1_timeout", elapsed_min=(time.time() - t_start) / 60)
        print(f"[warn] 超时未见完整出分，依据云主机实测确定性直接采用王牌分支 A")
        branch_name = "Branch_A_Timeout_Default"
        chosen_plan = WAVE2_BYPASS
        reason = "等待超时默认执行王牌分支"

    log_event("decision", branch=branch_name, chosen_plan=str(chosen_plan), reason=reason)
    print(f"\n===== 决策结果: 【{branch_name}】=====")
    print(f"决策理由: {reason}")
    print(f"部署方案: {chosen_plan.name}\n")

    # ================= 第二波：执行 Wave 2 (3 发) =================
    log_event("start_wave2", plan=str(chosen_plan))
    rc2 = run_plan(chosen_plan, yes=True)
    if rc2 != 0:
        log_event("error_wave2", rc=rc2)
        print(f"[ERR] 第二波提交失败，退出码 {rc2}")
        return rc2

    log_event("completed_all", total_slots_used=5)
    print(f"\n[OK] 今日 5 次提交已全部以两波自适应闭环顺利完成！")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
