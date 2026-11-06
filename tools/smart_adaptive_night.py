#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""智能两波式自适应夜间提交调度器（2 + 3 闭环体系）。

安全约束：
- 每日最多 5 发；Wave 1 前检查额度，Wave 2 前再次检查。
- 基线榜单读取失败时拒绝提交，避免把历史 attempts 当成新出分。
- 按 submitted_at 过滤 Wave 1 之后的新出分，不依赖 attempts 返回顺序。
- 同一天只执行一次：使用 runs/adaptive_night_state.json + 文件锁。
- 超时未拿到 2 条新出分时默认不盲投；需要人工核对后手动执行 Wave 2。

用法：
  python tools/smart_adaptive_night.py --at "2026-11-07 00:05"
  python tools/smart_adaptive_night.py --dry-run
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
PY = sys.executable

BOARD_URL = "http://47.120.64.152:5000/api/leaderboard"
TEAM = "赛博coder"
LIMIT = 5

WAVE1_PLAN = ROOT / "runs" / "submit_plan_1107_wave1.json"
WAVE2_BYPASS = ROOT / "runs" / "submit_plan_1107_wave2_bypass.json"
WAVE2_FALLBACK = ROOT / "runs" / "submit_plan_1107_wave2_fallback.json"
LOG_FILE = ROOT / "runs" / "adaptive_night_log.jsonl"
SUBMISSIONS = ROOT / "runs" / "submissions.jsonl"
STATE_FILE = ROOT / "runs" / "adaptive_night_state.json"
LOCK_FILE = ROOT / "runs" / ".adaptive_night.lock"


def log_event(event: str, **kwargs) -> None:
    now_str = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    rec = {"ts": now_str, "event": event, **kwargs}
    print(f"[{now_str}] [{event}] {json.dumps(kwargs, ensure_ascii=False)}", flush=True)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")


def wait_until(target: dt.datetime) -> None:
    while True:
        now = dt.datetime.now()
        left = (target - now).total_seconds()
        if left <= 0:
            return
        print(f"[wait] 距目标 {target:%m-%d %H:%M} 还有 {left/60:.1f} 分钟 (当前 {now:%H:%M:%S})", flush=True)
        time.sleep(min(300, max(15, left)))


def plan_len(path: Path) -> int:
    try:
        data = json.loads(path.read_text("utf-8"))
    except Exception:
        return 0
    return len(data) if isinstance(data, list) else 0


def run_plan(plan_path: Path, yes: bool = True) -> int:
    cmd = [PY, str(ROOT / "tools" / "submit_batch.py"), "--plan", str(plan_path)]
    if yes:
        cmd.append("--yes")
    print(f"\n$ {' '.join(cmd)}", flush=True)
    return subprocess.call(cmd, cwd=str(ROOT))


def fetch_team_attempts() -> list[dict] | None:
    """返回团队 attempts；接口异常时返回 None，调用方必须区分 None 与 []。"""
    try:
        req = urllib.request.Request(BOARD_URL)
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        for problem in (data.get("leaderboard") or {}).get("problems") or []:
            for submission in problem.get("submissions") or []:
                if submission.get("team") == TEAM:
                    return list(submission.get("attempts") or [])
        return []
    except Exception as exc:  # noqa: BLE001
        print(f"[poll-warn] 拉取榜单失败: {exc}", flush=True)
        return None


def parse_attempt_time(attempt: dict) -> dt.datetime | None:
    raw = str(attempt.get("submitted_at", "")).strip()
    try:
        return dt.datetime.strptime(raw, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None


def attempts_since(attempts: list[dict], since: dt.datetime) -> list[dict]:
    """按 submitted_at 过滤并按时间升序，不依赖 API 返回顺序。"""
    dated = []
    for attempt in attempts:
        when = parse_attempt_time(attempt)
        if when is not None and when >= since:
            dated.append((when, attempt))
    dated.sort(key=lambda pair: pair[0])
    return [attempt for _, attempt in dated]


def download_seconds(attempt: dict) -> float | None:
    try:
        return float(attempt.get("download_seconds"))
    except (TypeError, ValueError):
        return None


def today_used() -> int:
    if not SUBMISSIONS.exists():
        return 0
    today = dt.date.today()
    used = 0
    for line in SUBMISSIONS.read_text("utf-8").splitlines():
        if not line.strip():
            continue
        try:
            rec = json.loads(line)
            if rec.get("status") == "dry-run":
                continue
            if dt.date.fromisoformat(str(rec.get("date", ""))) == today:
                used += 1
        except (ValueError, TypeError):
            continue
    return used


def has_submission_history() -> bool:
    if not SUBMISSIONS.exists():
        return False
    for line in SUBMISSIONS.read_text("utf-8").splitlines():
        if not line.strip():
            continue
        try:
            if json.loads(line).get("status") != "dry-run":
                return True
        except ValueError:
            continue
    return False


def load_state() -> dict:
    if not STATE_FILE.exists():
        return {}
    try:
        return json.loads(STATE_FILE.read_text("utf-8"))
    except Exception:  # noqa: BLE001
        return {}


def save_state(**fields) -> None:
    state = load_state()
    state.update(fields)
    state["date"] = dt.date.today().isoformat()
    state["updated_at"] = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def acquire_lock() -> bool:
    LOCK_FILE.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(LOCK_FILE, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        return False
    os.write(fd, f"pid={os.getpid()} at={dt.datetime.now():%Y-%m-%d %H:%M:%S}\n".encode("utf-8"))
    os.close(fd)
    return True


def release_lock() -> None:
    try:
        LOCK_FILE.unlink()
    except FileNotFoundError:
        pass


def choose_branch(s1: float, s2: float, args) -> tuple[str, Path, str]:
    """只有明确优于基线时才走旁路分支；两边都慢时回退保守方案。"""
    if s2 <= args.bypass_max_s2:
        return "Branch_A_Bypass", WAVE2_BYPASS, f"tb 探针 {s2:.2f}s <= {args.bypass_max_s2:.1f}s"
    if s2 < s1 - args.bypass_margin and s2 <= args.bypass_floor:
        return ("Branch_A_Bypass", WAVE2_BYPASS,
                f"tb 探针 {s2:.2f}s 明显优于 leak {s1:.2f}s（margin>{args.bypass_margin:.1f}s）")
    return ("Branch_B_Fallback", WAVE2_FALLBACK,
            f"tb 探针 {s2:.2f}s 未明显优于 leak {s1:.2f}s（或整体偏慢），回退保守方案")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--at", default="2026-11-07 00:05")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--timeout-min", type=float, default=60.0)
    ap.add_argument("--poll-sec", type=int, default=60)
    ap.add_argument("--on-timeout", choices=("abort", "bypass", "fallback"), default="abort",
                    help="超时未拿到 2 条新出分时的动作；默认 abort，不盲投")
    ap.add_argument("--bypass-max-s2", type=float, default=132.0)
    ap.add_argument("--bypass-margin", type=float, default=2.0)
    ap.add_argument("--bypass-floor", type=float, default=138.0)
    ap.add_argument("--force", action="store_true",
                    help="忽略当日幂等状态；不绕过每日 5 发额度，使用前先核对 submissions.jsonl")
    args = ap.parse_args(argv)

    log_event("init", target_at=args.at, dry_run=args.dry_run, on_timeout=args.on_timeout)

    if args.dry_run:
        print(f"[dry-run] Wave 1 plan: {WAVE1_PLAN} ({plan_len(WAVE1_PLAN)} 发)")
        print(f"[dry-run] 今日已用: {today_used()}/{LIMIT}")
        run_plan(WAVE1_PLAN, yes=False)
        return 0

    if args.at.strip().lower() != "now":
        wait_until(dt.datetime.strptime(args.at.strip(), "%Y-%m-%d %H:%M"))

    if not acquire_lock():
        print(f"[BLOCK] 另一个调度器正在运行（{LOCK_FILE}）；请勿并发提交")
        return 4

    try:
        today = dt.date.today().isoformat()
        state = load_state()
        if not args.force and state.get("date") == today and state.get("wave1_intent"):
            print(f"[BLOCK] 今日已尝试过 Wave 1（{STATE_FILE}）；"
                  "先核对 runs/submissions.jsonl 和榜单，再决定是否人工恢复")
            return 4

        used = today_used()
        wave1_count = plan_len(WAVE1_PLAN)
        if used + wave1_count > LIMIT:
            print(f"[BLOCK] 今日已用 {used}/{LIMIT}，Wave 1 需要 {wave1_count} 发")
            return 3

        baseline = fetch_team_attempts()
        if baseline is None:
            print("[BLOCK] 无法读取榜单基线；拒绝在缺少基线时提交 Wave 1")
            return 5
        if not baseline and has_submission_history():
            print("[BLOCK] 榜单返回 0 条 attempts，但本地有提交历史；疑似接口异常，拒绝提交")
            return 5

        wave1_started = dt.datetime.now().replace(microsecond=0) - dt.timedelta(seconds=1)
        save_state(wave1_intent=True, wave1_submitted=False,
                   baseline_count=len(baseline), wave1_started_at=wave1_started.isoformat())

        log_event("start_wave1", plan=str(WAVE1_PLAN), used=used, baseline=len(baseline))
        rc1 = run_plan(WAVE1_PLAN, yes=True)
        if rc1 != 0:
            log_event("error_wave1", rc=rc1)
            print(f"[ERR] 第一波提交失败，退出码 {rc1}；请人工核对，不要直接重跑")
            return rc1
        save_state(wave1_submitted=True)
        log_event("wave1_submitted", baseline_count=len(baseline))

        print(f"\n===== 等待官方出分（目标：Wave 1 之后新增 2 条，超时 {args.timeout_min} 分钟）=====")
        t_start = time.time()
        t_deadline = t_start + args.timeout_min * 60
        new_attempts: list[dict] = []
        api_errors = 0

        while time.time() < t_deadline:
            time.sleep(args.poll_sec)
            current = fetch_team_attempts()
            if current is None:
                api_errors += 1
                print(f"[{dt.datetime.now():%H:%M:%S}] 榜单不可用（第 {api_errors} 次），继续等待")
                continue
            new_attempts = attempts_since(current, wave1_started)
            if len(new_attempts) >= 2:
                print(f"[{dt.datetime.now():%H:%M:%S}] 检测到 {len(new_attempts)} 条新出分")
                break
            print(f"[{dt.datetime.now():%H:%M:%S}] 已检测到 {len(new_attempts)}/2 条新出分")

        if len(new_attempts) < 2:
            log_event("wave1_timeout", elapsed_min=(time.time() - t_start) / 60,
                      api_errors=api_errors, on_timeout=args.on_timeout)
            if args.on_timeout == "abort":
                print("[BLOCK] 未在超时内拿到 2 条新出分；不自动执行 Wave 2。"
                      "请核对榜单后手动运行 submit_batch.py，或明确传入 --on-timeout bypass/fallback")
                return 6
            chosen_plan = WAVE2_BYPASS if args.on_timeout == "bypass" else WAVE2_FALLBACK
            branch_name = f"Branch_Timeout_{args.on_timeout}"
            reason = "等待超时，按显式指定的 --on-timeout 执行"
        else:
            s1 = download_seconds(new_attempts[0])
            s2 = download_seconds(new_attempts[1])
            if s1 is None or s2 is None:
                log_event("invalid_scores", attempts=new_attempts[:2])
                print("[BLOCK] 新出分缺少 download_seconds，拒绝自动决策")
                return 7
            log_event("wave1_scores", shot1_leak=s1, shot2_tb=s2)
            print(f"\n[出分对比] Shot 1 (leak): {s1:.4f}s | Shot 2 (tb): {s2:.4f}s")
            branch_name, chosen_plan, reason = choose_branch(s1, s2, args)

        log_event("decision", branch=branch_name, chosen_plan=str(chosen_plan), reason=reason)
        print(f"\n===== 决策结果: 【{branch_name}】=====")
        print(f"决策理由: {reason}")
        print(f"部署方案: {chosen_plan.name}\n")

        used = today_used()
        wave2_count = plan_len(chosen_plan)
        if used + wave2_count > LIMIT:
            save_state(wave2_blocked=True, chosen_plan=str(chosen_plan), used=used)
            print(f"[BLOCK] 今日已用 {used}/{LIMIT}，Wave 2 需要 {wave2_count} 发；不提交")
            return 3

        save_state(wave2_plan=str(chosen_plan), wave2_started=True)
        log_event("start_wave2", plan=str(chosen_plan), used=used)
        rc2 = run_plan(chosen_plan, yes=True)
        if rc2 != 0:
            log_event("error_wave2", rc=rc2)
            print(f"[ERR] 第二波提交失败，退出码 {rc2}；请人工核对")
            return rc2

        save_state(completed=True, wave2_plan=str(chosen_plan))
        log_event("completed_all", total_slots_used=today_used())
        print("\n[OK] 两波自适应提交完成")
        return 0
    finally:
        release_lock()


if __name__ == "__main__":
    raise SystemExit(main())
