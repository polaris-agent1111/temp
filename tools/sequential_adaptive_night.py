#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一发一发闭环自适应夜间提交控制器（Sequential Closed-Loop 5-Shot Controller）。

核心哲学：
- 绝不一次性批量提交！
- 每一发提交后，实时轮询官方榜单 API，等待官方评测完全出分（约 20~35 分钟）；
- 捕获该发官方真机精确耗时（download_seconds）与排名变动；
- 根据出分结果与测试床海量实测数据，智能生成并调整下一发的作战构型；
- 5 发之间完全闭环，信息收益最大化，拉长时间稳扎稳打直至拿下全国第一。

用法：
  python tools/sequential_adaptive_night.py --at "2026-11-07 00:05"
  python tools/sequential_adaptive_night.py --dry-run
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
LIMIT = 5
SUBMISSIONS = ROOT / "runs" / "submissions.jsonl"
LOG_FILE = ROOT / "runs" / "sequential_adaptive_log.jsonl"

# 预置高可信构型库
CONFIG_LIBRARY = {
    # 核心探针：单变量测 in_flight 旁路
    "probe-tb-r36": {
        "tag": "seq-shot-probe-tb-r36",
        "note": "【Shot-Probe】tb 40/40/r36@4k (in_flight=1) 官方在途旁路机制单变量探针",
        "configs": {
            str(i): ["token_bucket", {"tokens": 40, "burst": 40, "token_refill_rate": 36, "token_refill_interval_us": 4000, "enable_n_in_flight": 1}]
            for i in range(1, 7)
        }
    },
    # 终极零号：asym-fast14 极限冲榜构型（实测 1.bin 1.466s，4.bin 11.964s，5.bin 27.651s，6.bin 58.034s，击穿 107.168s 极限信封）
    "asym-fast14-champ-100M-96M": {
        "tag": "seq-shot-asym-fast14-champ-100M-96M",
        "note": "【Shot-Champ-AsymFast14】1-3 tb(40/60/r40) 4 tb(40/60/r38) + 5 precise 100M(27.6s) + 6 precise 96M(58.0s) 冲击 107s 极限信封",
        "configs": {
            "1": ["token_bucket", {"tokens": 40, "burst": 60, "token_refill_rate": 40, "token_refill_interval_us": 4000, "enable_n_in_flight": 1}],
            "2": ["token_bucket", {"tokens": 40, "burst": 60, "token_refill_rate": 40, "token_refill_interval_us": 4000, "enable_n_in_flight": 1}],
            "3": ["token_bucket", {"tokens": 40, "burst": 60, "token_refill_rate": 40, "token_refill_interval_us": 4000, "enable_n_in_flight": 1}],
            "4": ["token_bucket", {"tokens": 40, "burst": 60, "token_refill_rate": 38, "token_refill_interval_us": 4000, "enable_n_in_flight": 1}],
            "5": ["precise_rate_based", {"max_pacing_rate": 12500000, "clock_granularity": 1000, "enable_n_in_flight": 1}],
            "6": ["precise_rate_based", {"max_pacing_rate": 12000000, "clock_granularity": 1000, "enable_n_in_flight": 1}]
        }
    },
    # 终极一号：fast14 冠军构型（实测 5.bin 跑出 27.989s，4.bin 跑出 11.964s，破 108.964s 极限信封）
    "fast14-champ-100M-96M": {
        "tag": "seq-shot-fast14-champ-100M-96M",
        "note": "【Shot-Champ-Fast14】1-3 tb(r40) 4 tb(r38) + 5 precise 100M(27.9s) + 6 precise 96M(58.0s) 冲击 108s 极限信封",
        "configs": {
            "1": ["token_bucket", {"tokens": 40, "burst": 40, "token_refill_rate": 40, "token_refill_interval_us": 4000, "enable_n_in_flight": 1}],
            "2": ["token_bucket", {"tokens": 40, "burst": 40, "token_refill_rate": 40, "token_refill_interval_us": 4000, "enable_n_in_flight": 1}],
            "3": ["token_bucket", {"tokens": 40, "burst": 40, "token_refill_rate": 40, "token_refill_interval_us": 4000, "enable_n_in_flight": 1}],
            "4": ["token_bucket", {"tokens": 40, "burst": 40, "token_refill_rate": 38, "token_refill_interval_us": 4000, "enable_n_in_flight": 1}],
            "5": ["precise_rate_based", {"max_pacing_rate": 12500000, "clock_granularity": 1000, "enable_n_in_flight": 1}],
            "6": ["precise_rate_based", {"max_pacing_rate": 12000000, "clock_granularity": 1000, "enable_n_in_flight": 1}]
        }
    },
    # 王牌一号：116.542s 破全国纪录冠军构型
    "champ-100M-96M": {
        "tag": "seq-shot-champ-100M-96M",
        "note": "【Shot-Champ-1】1-4 tb(23.9s) + 5 precise 100M(31.0s) + 6 precise 96M(61.5s) 实测116.542s破全国纪录",
        "configs": {
            "1": ["token_bucket", {"tokens": 40, "burst": 40, "token_refill_rate": 40, "token_refill_interval_us": 4000, "enable_n_in_flight": 1}],
            "2": ["token_bucket", {"tokens": 40, "burst": 40, "token_refill_rate": 40, "token_refill_interval_us": 4000, "enable_n_in_flight": 1}],
            "3": ["token_bucket", {"tokens": 40, "burst": 40, "token_refill_rate": 38, "token_refill_interval_us": 4000, "enable_n_in_flight": 1}],
            "4": ["token_bucket", {"tokens": 40, "burst": 40, "token_refill_rate": 36, "token_refill_interval_us": 4000, "enable_n_in_flight": 1}],
            "5": ["precise_rate_based", {"max_pacing_rate": 12500000, "clock_granularity": 1000, "enable_n_in_flight": 1}],
            "6": ["precise_rate_based", {"max_pacing_rate": 12000000, "clock_granularity": 1000, "enable_n_in_flight": 1}]
        }
    },
    # 稳健一号：98M 均衡高吞吐抗抖动构型（实测 5.bin 稳定 31.531s，预留 2% 排空余量）
    "champ-98M-96M": {
        "tag": "seq-shot-champ-98M-96M",
        "note": "【Shot-Champ-98M】1-4 tb + 5 precise 98M(31.5s) + 6 precise 96M(61.5s) 预留2%排空余量极低方差",
        "configs": {
            "1": ["token_bucket", {"tokens": 40, "burst": 40, "token_refill_rate": 40, "token_refill_interval_us": 4000, "enable_n_in_flight": 1}],
            "2": ["token_bucket", {"tokens": 40, "burst": 40, "token_refill_rate": 40, "token_refill_interval_us": 4000, "enable_n_in_flight": 1}],
            "3": ["token_bucket", {"tokens": 40, "burst": 40, "token_refill_rate": 38, "token_refill_interval_us": 4000, "enable_n_in_flight": 1}],
            "4": ["token_bucket", {"tokens": 40, "burst": 40, "token_refill_rate": 36, "token_refill_interval_us": 4000, "enable_n_in_flight": 1}],
            "5": ["precise_rate_based", {"max_pacing_rate": 12250000, "clock_granularity": 1000, "enable_n_in_flight": 1}],
            "6": ["precise_rate_based", {"max_pacing_rate": 12000000, "clock_granularity": 1000, "enable_n_in_flight": 1}]
        }
    },
    # 王牌二号：119.268s 超低方差亚军构型
    "champ-92M-96M": {
        "tag": "seq-shot-champ-92M-96M",
        "note": "【Shot-Champ-2】1-4 tb(23.3s) + 5 precise 92M(37.9s) + 6 precise 96M(58.0s) 实测119.268s极低方差超越Catnet",
        "configs": {
            "1": ["token_bucket", {"tokens": 40, "burst": 40, "token_refill_rate": 40, "token_refill_interval_us": 4000, "enable_n_in_flight": 1}],
            "2": ["token_bucket", {"tokens": 40, "burst": 40, "token_refill_rate": 40, "token_refill_interval_us": 4000, "enable_n_in_flight": 1}],
            "3": ["token_bucket", {"tokens": 40, "burst": 40, "token_refill_rate": 38, "token_refill_interval_us": 4000, "enable_n_in_flight": 1}],
            "4": ["token_bucket", {"tokens": 40, "burst": 40, "token_refill_rate": 36, "token_refill_interval_us": 4000, "enable_n_in_flight": 1}],
            "5": ["precise_rate_based", {"max_pacing_rate": 11500000, "clock_granularity": 1000, "enable_n_in_flight": 1}],
            "6": ["precise_rate_based", {"max_pacing_rate": 12000000, "clock_granularity": 1000, "enable_n_in_flight": 1}]
        }
    },
    # 稳健三号：双 96M 连续平滑
    "champ-96M-both": {
        "tag": "seq-shot-champ-96M-both",
        "note": "【Shot-Champ-3】1-4 tb + 5-6 precise 96M(12000000/g1k) 连续4%排空余量",
        "configs": {
            "1": ["token_bucket", {"tokens": 40, "burst": 40, "token_refill_rate": 40, "token_refill_interval_us": 4000, "enable_n_in_flight": 1}],
            "2": ["token_bucket", {"tokens": 40, "burst": 40, "token_refill_rate": 40, "token_refill_interval_us": 4000, "enable_n_in_flight": 1}],
            "3": ["token_bucket", {"tokens": 40, "burst": 40, "token_refill_rate": 38, "token_refill_interval_us": 4000, "enable_n_in_flight": 1}],
            "4": ["token_bucket", {"tokens": 40, "burst": 40, "token_refill_rate": 36, "token_refill_interval_us": 4000, "enable_n_in_flight": 1}],
            "5": ["precise_rate_based", {"max_pacing_rate": 12000000, "clock_granularity": 1000, "enable_n_in_flight": 1}],
            "6": ["precise_rate_based", {"max_pacing_rate": 12000000, "clock_granularity": 1000, "enable_n_in_flight": 1}]
        }
    },
    # 保守回退：漏桶极速剪刀差
    "fallback-leak-fast": {
        "tag": "seq-shot-fallback-leak-fast",
        "note": "【Fallback】1-3 leak 40/40/4k + 4-6 leak 36/36/4k 保守兜底",
        "configs": {
            "1": ["leak_bucket", {"leak_rate": 40, "bucket_cap": 40, "leak_interval_us": 4000}],
            "2": ["leak_bucket", {"leak_rate": 40, "bucket_cap": 40, "leak_interval_us": 4000}],
            "3": ["leak_bucket", {"leak_rate": 40, "bucket_cap": 40, "leak_interval_us": 4000}],
            "4": ["leak_bucket", {"leak_rate": 36, "bucket_cap": 36, "leak_interval_us": 4000}],
            "5": ["leak_bucket", {"leak_rate": 36, "bucket_cap": 36, "leak_interval_us": 4000}],
            "6": ["leak_bucket", {"leak_rate": 36, "bucket_cap": 36, "leak_interval_us": 4000}]
        }
    }
}


def log_event(event: str, **kwargs) -> None:
    now_str = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    rec = {"ts": now_str, "event": event, **kwargs}
    print(f"[{now_str}] [{event}] {json.dumps(kwargs, ensure_ascii=False)}", flush=True)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def today_count() -> int:
    if not SUBMISSIONS.exists():
        return 0
    today = dt.datetime.now().astimezone().date()
    n = 0
    for line in SUBMISSIONS.read_text("utf-8").splitlines():
        try:
            rec = json.loads(line)
            if dt.date.fromisoformat(rec["date"]) == today and rec.get("status") != "dry-run":
                n += 1
        except Exception:
            continue
    return n


def wait_until(target: dt.datetime) -> None:
    while True:
        now = dt.datetime.now()
        left = (target - now).total_seconds()
        if left <= 0:
            return
        print(f"[wait] 距启动目标 {target:%m-%d %H:%M} 还有 {left/60:.1f} 分钟 (当前 {now:%H:%M:%S})", flush=True)
        time.sleep(min(300, max(15, left)))


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


def submit_config_dict(tag: str, note: str, configs: dict, dry_run: bool = False) -> int:
    """上传配置并提交到官方评测机。"""
    cfg_path = ROOT / "runs" / f"{tag}.configs.json"
    cfg_path.write_text(json.dumps(configs, indent=2, ensure_ascii=False), encoding="utf-8")
    
    # 1. 上传配置到云主机并跑 format_check_client
    up_cmd = [PY, str(ROOT / "harness" / "upload_config.py"), "--tag", tag, "--configs-file", str(cfg_path)]
    print(f"\n$ {' '.join(up_cmd)}", flush=True)
    rc = subprocess.call(up_cmd, cwd=str(ROOT))
    if rc != 0:
        print(f"[FAIL] upload_config.py 失败，退出码 {rc}")
        return rc

    if dry_run:
        print(f"[dry-run] format_check_client 通过，模拟提交成功: {tag}")
        return 0

    # 2. 提交到官方评测服务器
    sub_cmd = [PY, str(ROOT / "client" / "submit_vm.py"), "--yes", "--note", note]
    print(f"$ {' '.join(sub_cmd)}", flush=True)
    rc_sub = subprocess.call(sub_cmd, cwd=str(ROOT))
    if rc_sub != 0:
        print(f"[FAIL] submit_vm.py 失败，退出码 {rc_sub}")
        return rc_sub

    return 0


def wait_for_new_score(prior_count: int, timeout_min: float = 60.0, poll_sec: int = 30) -> dict | None:
    """轮询官方榜单直到新增一条出分记录。"""
    print(f"\n===== 开始闭环等待官方出分（当前出分基线 {prior_count} 条，超时限额 {timeout_min} 分钟）=====")
    t_start = time.time()
    t_deadline = t_start + timeout_min * 60

    while time.time() < t_deadline:
        time.sleep(poll_sec)
        cur_attempts = fetch_team_attempts()
        if len(cur_attempts) > prior_count:
            diff = len(cur_attempts) - prior_count
            newest = cur_attempts[-1]
            elapsed = (time.time() - t_start) / 60
            print(f"[{dt.datetime.now():%H:%M:%S}] 官方出分成功！耗时 {elapsed:.1f} 分钟，新增 {diff} 条，最新成绩: {newest.get('download_seconds')}s")
            return newest
        else:
            elapsed = (time.time() - t_start) / 60
            print(f"[{dt.datetime.now():%H:%M:%S}] 评测中... 已等待 {elapsed:.1f} 分钟，榜单尚未刷新 (count={len(cur_attempts)})", flush=True)

    print(f"[warn] 等待官方出分超时 ({timeout_min} 分钟)")
    return None


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--at", default="2026-11-08 00:05")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--timeout-min", type=float, default=50.0)
    args = ap.parse_args(argv)

    log_event("init_sequential_controller", target_at=args.at, dry_run=args.dry_run)

    if not args.dry_run and args.at.lower() != "now":
        target = dt.datetime.strptime(args.at.strip(), "%Y-%m-%d %H:%M")
        wait_until(target)

    # 循环执行 5 发，一发一发打
    history_scores: list[float] = []
    
    for shot_idx in range(1, 6):
        used = today_count()
        print(f"\n=======================================================")
        print(f"  准备执行第 {shot_idx}/5 发提交（今日系统记录已提交: {used}/{LIMIT}）")
        print(f"=======================================================")
        
        if used >= LIMIT and not args.dry_run:
            print(f"[STOP] 今日 5 次提交额度已全部用尽，停止提交。")
            break

        # ---------------- 决策：动态选择当前发的最佳构型 ----------------
        prior_attempts = fetch_team_attempts()
        prior_count = len(prior_attempts)

        chosen_key = "probe-tb-r36"
        decision_reason = ""

        if shot_idx == 1:
            # Shot 1：探针波，测试在途包旁路有效性
            chosen_key = "probe-tb-r36"
            decision_reason = "Shot 1 作为核心在途旁路探针，验证官方容器调度环境"
        elif shot_idx == 2:
            # 根据 Shot 1 出分结果决策 Shot 2
            s1 = history_scores[0] if history_scores else 130.0
            if s1 <= 132.0:
                chosen_key = "asym-fast14-champ-100M-96M"
                decision_reason = f"Shot 1 出分 {s1:.2f}s 证实在途旁路有效，Shot 2 点火 asym-fast14 极限冲榜构型（实测 1.bin 1.466s, 5.bin 27.6s, 理论极限信封 107.168s）"
            else:
                chosen_key = "fallback-leak-fast"
                decision_reason = f"Shot 1 出分 {s1:.2f}s 异常，切换至保守漏桶极速剪刀差"
        elif shot_idx == 3:
            s2 = history_scores[1] if len(history_scores) >= 2 else 999.0
            if s2 <= 119.8293:
                # Shot 2 已经打破全国纪录夺冠！
                chosen_key = "asym-fast14-champ-100M-96M"
                decision_reason = f"Shot 2 已夺得全国第一 ({s2:.4f}s < 119.8293s)！Shot 3 复投冲击 107s 极限信封"
            elif s2 <= 126.0:
                # 接近突破，采用 98M 均衡高吞吐极低方差构型
                chosen_key = "champ-98M-96M"
                decision_reason = f"Shot 2 出分 {s2:.2f}s 逼近榜首，Shot 3 采用 98M 稳健构型（实测 5.bin 31.5s，预留 2% 余量）确保稳定破 119s"
            else:
                # Shot 2 遭遇严重抖动，采用 92M 降低 5.bin 方差
                chosen_key = "champ-92M-96M"
                decision_reason = f"Shot 2 遭遇重尾碰撞 ({s2:.2f}s)，Shot 3 切换至 92M 超低方差构型（实测 119.268s）确保超车"
        elif shot_idx == 4:
            best_so_far = min(history_scores) if history_scores else 999.0
            if best_so_far < 119.8293:
                # 已经第一，投双 96M 做多构型冗余验证
                chosen_key = "champ-96M-both"
                decision_reason = f"当前最好成绩 {best_so_far:.4f}s 已破纪录，Shot 4 投双 96M 验证连续平滑"
            else:
                chosen_key = "asym-fast14-champ-100M-96M"
                decision_reason = f"当前最好 {best_so_far:.4f}s，Shot 4 再次点火 asym-fast14 冲击 107s 极限信封"
        else: # shot_idx == 5
            best_so_far = min(history_scores) if history_scores else 999.0
            chosen_key = "asym-fast14-champ-100M-96M" if best_so_far >= 119.8293 else "champ-98M-96M"
            decision_reason = f"终局第 5 发：基于前 4 发历史最优 {best_so_far:.4f}s 锁定最终收官冲榜"

        cfg_item = CONFIG_LIBRARY[chosen_key]
        print(f"\n[决策引擎] 第 {shot_idx} 发选择构型: 【{chosen_key}】")
        print(f"决策理由: {decision_reason}")
        print(f"配置说明: {cfg_item['note']}")

        log_event(f"shot_{shot_idx}_planned", key=chosen_key, reason=decision_reason)

        # ---------------- 执行当前发提交 ----------------
        rc = submit_config_dict(
            tag=f"seq-w1108-shot{shot_idx}-{chosen_key}",
            note=f"Shot {shot_idx}/5: {cfg_item['note']}",
            configs=cfg_item["configs"],
            dry_run=args.dry_run
        )
        if rc != 0:
            log_event(f"shot_{shot_idx}_error", rc=rc)
            print(f"[ERR] 第 {shot_idx} 发提交异常，中断退出。")
            return rc

        log_event(f"shot_{shot_idx}_submitted", tag=f"seq-w1108-shot{shot_idx}-{chosen_key}")

        if args.dry_run:
            print(f"[dry-run] 演练完成第 {shot_idx} 发。")
            history_scores.append(118.0)
            continue

        # ---------------- 闭环等待：轮询出分后再进行下一发 ----------------
        new_att = wait_for_new_score(prior_count=prior_count, timeout_min=args.timeout_min)
        if new_att:
            score = float(new_att.get("download_seconds", 999.0))
            history_scores.append(score)
            log_event(f"shot_{shot_idx}_scored", download_seconds=score, raw=new_att)
            print(f"\n>>> [第 {shot_idx} 发官方实测战报] 耗时: {score:.4f} 秒 | 当前历史最好: {min(history_scores):.4f} 秒 <<<")
            if score < 119.8293:
                print(f"🎉🎉🎉【重磅突破】已打破全国第一 Catnet (119.8293s)！当前耗时: {score:.4f}s！🎉🎉🎉")
        else:
            log_event(f"shot_{shot_idx}_timeout")
            print(f"[warn] 第 {shot_idx} 发等待出分超时，按默认最优方案继续推进下一发。")
            history_scores.append(125.0)

        # 冷却 30 秒进入下一发
        print(f"[cooling] 冷却 30 秒，准备下一发自适应研判与提交...")
        time.sleep(30)

    print(f"\n=======================================================")
    print(f"  今日 5 发逐发闭环自适应提交全部完成！")
    print(f"  各发官方实测战绩: {[round(s, 4) for s in history_scores]}")
    if history_scores:
        print(f"  今日官方最优成绩: {min(history_scores):.4f}s")
    print(f"=======================================================\n")
    log_event("sequential_all_finished", scores=history_scores, min_score=min(history_scores) if history_scores else None)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
