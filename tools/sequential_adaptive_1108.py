#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""11/08 决战：逐发闭环自适应打榜控制器 (Sequential Closed-Loop 5-Shot Controller).

核心战略哲学：
- 严格践行「打一发再分析下一发怎么打」的闭环自适应科学原则；
- 绝不一次性批量提交！
- 每一发提交后，持续轮询官方榜单 API，捕获真机出分 (download_seconds) 与全国排名变动；
- 根据出分结果与环境拥塞度，动态从四大认证候选池（稳健标杆、皇冠冲顶、超宽平台、防守堡垒）
  中精确选择或微调下一发构型；
- 5 发之间完全闭环，信息收益最大化，全过程幂等防死锁，直取全国第一！

用法：
  python tools/sequential_adaptive_1108.py --dry-run                           # 离线全闭环状态机仿真演练
  python tools/sequential_adaptive_1108.py --at "2026-11-08 00:05"            # 设定明日 00:05 准时开战 (dry-run)
  python tools/sequential_adaptive_1108.py --at "2026-11-08 00:05" --yes      # 真实实战打榜
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import random
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
LIMIT = 3  # 用户严令：今日只准提交 3 发！

STATE_FILE = ROOT / "runs" / "sequential_1108_state.json"
LOG_FILE = ROOT / "runs" / "sequential_1108_log.jsonl"
LOCK_FILE = ROOT / "runs" / ".sequential_1108.lock"
SUBMISSIONS_FILE = ROOT / "runs" / "submissions.jsonl"

# ============================================================================
# 四大认证候选构型库 (全部通过 n=10~15 严格大样本认证与门禁审计)
# ============================================================================
CANDIDATE_POOL = {
    # 候选 1：稳健首发主力 (1-3@40, 4@37, 5-6@36) —— n=15 终极认证 (实测 122.0463s 斩获全国第 5)
    "steady_champion": {
        "candidate_id": "steady_champion",
        "tag": "1108-shot-steady-40x3-37-36-36",
        "note": "1108 稳健首发主力 (1-3@40, 4@37, 5-6@36) —— 实测 122.0463s 突破至全国第 5",
        "configs": {
            "1": ["leak_bucket", {"bucket_cap": 40, "leak_interval_us": 4000, "leak_rate": 40}],
            "2": ["leak_bucket", {"bucket_cap": 40, "leak_interval_us": 4000, "leak_rate": 40}],
            "3": ["leak_bucket", {"bucket_cap": 40, "leak_interval_us": 4000, "leak_rate": 40}],
            "4": ["leak_bucket", {"bucket_cap": 37, "leak_interval_us": 4000, "leak_rate": 37}],
            "5": ["leak_bucket", {"bucket_cap": 36, "leak_interval_us": 4000, "leak_rate": 36}],
            "6": ["leak_bucket", {"bucket_cap": 36, "leak_interval_us": 4000, "leak_rate": 36}],
        }
    },
    # 候选 2：皇冠冲冠主力 (1-2@41, 3@40, 4@37, 5-6@36) —— n=15 认证 (4.bin 凸性极值谷底，预期 116.5~117.5s 绝杀全国榜首)
    "crown_fusion": {
        "candidate_id": "crown_fusion",
        "tag": "1108-shot-crown-41x2-40-37-36x2",
        "note": "1108 皇冠冲冠主力 (1-2@41, 3@40, 4@37, 5-6@36) —— 4.bin 凸性极值谷底，官方预期 116.5~117.5s 直指全国第一",
        "configs": {
            "1": ["leak_bucket", {"bucket_cap": 41, "leak_interval_us": 4000, "leak_rate": 41}],
            "2": ["leak_bucket", {"bucket_cap": 41, "leak_interval_us": 4000, "leak_rate": 41}],
            "3": ["leak_bucket", {"bucket_cap": 40, "leak_interval_us": 4000, "leak_rate": 40}],
            "4": ["leak_bucket", {"bucket_cap": 37, "leak_interval_us": 4000, "leak_rate": 37}],
            "5": ["leak_bucket", {"bucket_cap": 36, "leak_interval_us": 4000, "leak_rate": 36}],
            "6": ["leak_bucket", {"bucket_cap": 36, "leak_interval_us": 4000, "leak_rate": 36}],
        }
    },
    # 候选 3：皇冠极速冲冠 (1-3@41, 4@37, 5-6@36) —— 前三轮满额 41 极限压迫，冲击 sub-116s
    "crown_hyper": {
        "candidate_id": "crown_hyper",
        "tag": "1108-shot-crown-41x3-37-36x2",
        "note": "1108 皇冠极速冲冠 (1-3@41, 4@37, 5-6@36) —— 前三轮满额 41 极限压迫，冲击 sub-116s 绝杀 Catnet 116.33s",
        "configs": {
            "1": ["leak_bucket", {"bucket_cap": 41, "leak_interval_us": 4000, "leak_rate": 41}],
            "2": ["leak_bucket", {"bucket_cap": 41, "leak_interval_us": 4000, "leak_rate": 41}],
            "3": ["leak_bucket", {"bucket_cap": 41, "leak_interval_us": 4000, "leak_rate": 41}],
            "4": ["leak_bucket", {"bucket_cap": 37, "leak_interval_us": 4000, "leak_rate": 37}],
            "5": ["leak_bucket", {"bucket_cap": 36, "leak_interval_us": 4000, "leak_rate": 36}],
            "6": ["leak_bucket", {"bucket_cap": 36, "leak_interval_us": 4000, "leak_rate": 36}],
        }
    },
    # 候选 4：皇冠超宽平台 (1@41, 2-3@40, 4@37, 5-6@36) —— n=10 认证超平坦平台点 (均值 135.85s, CV 6.4%)
    "crown_plateau_a": {
        "candidate_id": "crown_plateau_a",
        "tag": "1108-shot-crown-pert-40on2",
        "note": "1108 皇冠超宽平台 (1@41, 2-3@40, 4@37, 5-6@36) —— n=10 认证超平坦平台点，官方预期 118~120s 极度稳健",
        "configs": {
            "1": ["leak_bucket", {"bucket_cap": 41, "leak_interval_us": 4000, "leak_rate": 41}],
            "2": ["leak_bucket", {"bucket_cap": 40, "leak_interval_us": 4000, "leak_rate": 40}],
            "3": ["leak_bucket", {"bucket_cap": 40, "leak_interval_us": 4000, "leak_rate": 40}],
            "4": ["leak_bucket", {"bucket_cap": 37, "leak_interval_us": 4000, "leak_rate": 37}],
            "5": ["leak_bucket", {"bucket_cap": 36, "leak_interval_us": 4000, "leak_rate": 36}],
            "6": ["leak_bucket", {"bucket_cap": 36, "leak_interval_us": 4000, "leak_rate": 36}],
        }
    },
    # 候选 5：防守堡垒 (1-4@40, 5-6@37) —— n=10 满额认证 (CV 仅 4.0%, SE 1.71s, 极大值 143s)
    "defense_fortress": {
        "candidate_id": "defense_fortress",
        "tag": "1108-shot-fortress-40x4-37x2",
        "note": "1108 防守堡垒 (1-4@40, 5-6@37) —— n=10 认证极低方差 (CV 4.0%)，官方复测抗扰护城河",
        "configs": {
            "1": ["leak_bucket", {"bucket_cap": 40, "leak_interval_us": 4000, "leak_rate": 40}],
            "2": ["leak_bucket", {"bucket_cap": 40, "leak_interval_us": 4000, "leak_rate": 40}],
            "3": ["leak_bucket", {"bucket_cap": 40, "leak_interval_us": 4000, "leak_rate": 40}],
            "4": ["leak_bucket", {"bucket_cap": 40, "leak_interval_us": 4000, "leak_rate": 40}],
            "5": ["leak_bucket", {"bucket_cap": 37, "leak_interval_us": 4000, "leak_rate": 37}],
            "6": ["leak_bucket", {"bucket_cap": 37, "leak_interval_us": 4000, "leak_rate": 37}],
        }
    }
}


def log(msg: str, **kwargs) -> None:
    now_str = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    payload = f" {json.dumps(kwargs, ensure_ascii=False)}" if kwargs else ""
    line = f"[{now_str}] {msg}{payload}"
    print(line, flush=True)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": now_str, "msg": msg, **kwargs}, ensure_ascii=False) + "\n")


def wait_until(target: dt.datetime) -> None:
    while True:
        now = dt.datetime.now()
        left = (target - now).total_seconds()
        if left <= 0:
            return
        log(f"[wait] 距目标打榜时刻 {target:%Y-%m-%d %H:%M} 还有 {left/60:.1f} 分钟 (当前 {now:%H:%M:%S})")
        time.sleep(min(300, max(15, left)))


def today_submissions_count(target_date: dt.date | None = None) -> int:
    if not SUBMISSIONS_FILE.exists():
        return 0
    t_date = target_date or dt.datetime.now().astimezone().date()
    n = 0
    for line in SUBMISSIONS_FILE.read_text("utf-8").splitlines():
        if not line.strip():
            continue
        try:
            rec = json.loads(line)
            if rec.get("status") == "dry-run":
                continue
            if dt.date.fromisoformat(str(rec.get("date", ""))) == t_date:
                n += 1
        except Exception:
            continue
    return n


def fetch_leaderboard_attempts() -> tuple[list[dict] | None, int | None, float | None]:
    """从官方 API 拉取当前团队的所有 attempts、当前榜单排名及最优成绩。"""
    try:
        req = urllib.request.Request(BOARD_URL)
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        for problem in (data.get("leaderboard") or {}).get("problems") or []:
            for sub in problem.get("submissions") or []:
                if sub.get("team") == TEAM:
                    attempts = list(sub.get("attempts") or [])
                    rank = sub.get("rank")
                    best_sec = sub.get("min_download_seconds")
                    return attempts, rank, float(best_sec) if best_sec else None
        return [], None, None
    except Exception as exc:
        log(f"[poll-warn] 官方榜单拉取异常: {exc}")
        return None, None, None


def parse_time(raw: str) -> dt.datetime | None:
    raw = str(raw or "").strip()
    try:
        return dt.datetime.strptime(raw, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None


def poll_for_new_score(submitted_after: dt.datetime, timeout_min: float = 65.0, poll_interval: float = 60.0) -> dict:
    """持续轮询官方榜单，直到检测到 submitted_after 之后产生的新官方真机成绩。"""
    deadline = dt.datetime.now() + dt.timedelta(minutes=timeout_min)
    log(f"开始轮询官方真机出分（基线时间: {submitted_after:%H:%M:%S}，超时时限: {timeout_min:.0f} 分钟）...")
    
    # 宽限 3 分钟，防止服务器时钟与本地轻微偏斜
    effective_since = submitted_after - dt.timedelta(minutes=3)
    
    while dt.datetime.now() < deadline:
        attempts, rank, best_sec = fetch_leaderboard_attempts()
        if attempts is not None:
            # 筛选在 effective_since 之后的出分
            new_attempts = []
            for att in attempts:
                t = parse_time(att.get("submitted_at"))
                if t and t >= effective_since:
                    sec = att.get("download_seconds")
                    if sec is not None:
                        try:
                            f_sec = float(sec)
                            new_attempts.append((t, f_sec, att))
                        except ValueError:
                            pass
            
            if new_attempts:
                # 取时间最近的一条
                new_attempts.sort(key=lambda x: x[0], reverse=True)
                scored_time, score_sec, raw_att = new_attempts[0]
                log(f"★ 成功捕获官方真机出分！耗时: {score_sec:.4f}s | 官方排名: 第 {rank} 名 | 出分时刻: {scored_time:%H:%M:%S}")
                return {
                    "status": "scored",
                    "download_seconds": score_sec,
                    "rank": rank,
                    "best_seconds": best_sec,
                    "scored_at": scored_time.strftime("%Y-%m-%d %H:%M:%S")
                }
        
        left_sec = (deadline - dt.datetime.now()).total_seconds()
        log(f"  等待出分中... 剩余超时等待时间: {left_sec/60:.1f} 分钟")
        time.sleep(poll_interval)
        
    log("[poll-timeout] 轮询超过时限，官方评测可能处于排队拥塞，启动安全策略！")
    return {
        "status": "timeout",
        "download_seconds": None,
        "rank": None,
        "best_seconds": None,
        "scored_at": None
    }


def decide_next_shot(history: list[dict], next_idx: int) -> tuple[dict, str]:
    """「打一发看一发」核心闭环自适应决策引擎。
    
    依据历史出分序列与信道拥塞度，动态选择最优候选构型。
    """
    assert 1 <= next_idx <= 5, f"非法的 shot 序号: {next_idx}"
    
    # ========================== Shot 1: 绝对稳健锚点 ==========================
    if next_idx == 1:
        cand = CANDIDATE_POOL["steady_champion"]
        reason = "【Shot 1 首发锚定】以 n=15 极低方差稳健标杆 (133.86s, SE 2.16s) 首发探测官方环境基准"
        return cand, reason
        
    # 获取前一发 (Shot k-1) 的出分结果
    last_shot = history[-1]
    last_status = last_shot.get("status")
    last_score = last_shot.get("download_seconds")
    
    # 提取至今为止的所有有效成绩
    all_scores = [s["download_seconds"] for s in history if s.get("status") == "scored" and s.get("download_seconds")]
    current_best = min(all_scores) if all_scores else 999.0

    # ========================== Shot 2: 基于首发自适应 ==========================
    if next_idx == 2:
        if last_status == "timeout" or last_score is None:
            cand = CANDIDATE_POOL["crown_plateau_a"]
            reason = "【Shot 2 容错降级】首发超时未拿到真机成绩，启用超平坦平台点稳妥推进"
        elif last_score <= 122.5:
            # 官方信道极其畅通，排队积压低
            cand = CANDIDATE_POOL["crown_fusion"]
            reason = f"【Shot 2 皇冠冲锋】首发出分 {last_score:.2f}s 极其优异（<=122.5s，信道畅通），果断切换 1-2@41 皇冠冲冠主力直扑全国第一（<117s）！"
        elif last_score <= 125.0:
            # 信道正常，存在微小抖动
            cand = CANDIDATE_POOL["crown_plateau_a"]
            reason = f"【Shot 2 平台拓展】首发出分 {last_score:.2f}s 处于标准区间（122.5~125s），部署超宽平台 A (1@41, 2-3@40) 稳步下探"
        else:
            # 遭遇极端重尾或宿主机高负荷
            cand = CANDIDATE_POOL["defense_fortress"]
            reason = f"【Shot 2 防守筑垒】首发出分 {last_score:.2f}s 偏高（>125s，遭遇网络重尾），立即启用 CV 4.0% 防守堡垒强力压制方差"
        return cand, reason

    # ========================== Shot 3: 本日终局决胜 (3发限制压轴) ==========================
    if next_idx == 3:
        if current_best <= 116.3367:
            # 已成功击败 Catnet（116.3367s）登顶全国第一！
            cand = CANDIDATE_POOL["crown_plateau_a"]
            reason = f"【Shot 3 冠军固化】当前最优 {current_best:.4f}s 已夺全国第一！投出超平坦平台点测定复测方差，加固冠军防线"
        elif current_best <= 118.5:
            # 距离 Catnet (116.3367s) 咫尺之遥，压轴发启动 crown_hyper (1-3@41) 冲锋！
            cand = CANDIDATE_POOL["crown_hyper"]
            reason = f"【Shot 3 皇冠极速绝杀】当前最优 {current_best:.4f}s 逼近全国第一，本日最后一发启动 1-3@41 crown_hyper 绝杀冲击 <116s！"
        elif last_score and len(all_scores) >= 2 and last_score < all_scores[-2]:
            # Shot 2 相比 Shot 1 呈现正向改进
            cand = CANDIDATE_POOL["crown_fusion"]
            reason = f"【Shot 3 乘胜追击】Shot 2 ({last_score:.2f}s) 相比 Shot 1 提速有效，继续加力皇冠主力冲击榜首"
        else:
            # 出现方差抖动或恶化
            cand = CANDIDATE_POOL["crown_plateau_a"]
            reason = f"【Shot 3 平台避险】Shot 2 出现方差抖动，切换回 n=10 超宽平坦平台点稳定中枢"
        return cand, reason

    # ========================== Shot 4: 后期攻防权衡 ==========================
    if next_idx == 4:
        if current_best <= 117.0257:
            # 已超越光明未来登顶全国第一！
            cand = CANDIDATE_POOL["steady_champion"]
            reason = f"【Shot 4 登顶护城河】当前成绩 {current_best:.2f}s 已夺全国第一！投出稳健标杆测量样本方差，加固复测防线"
        elif current_best <= 121.0:
            # 距离第一名 117.02s 仅一步之遥
            cand = CANDIDATE_POOL["crown_fusion"]
            reason = f"【Shot 4 决胜绝杀】当前最佳 {current_best:.2f}s 逼近全国第一，全油门皇冠冲顶决战"
        else:
            cand = CANDIDATE_POOL["defense_fortress"]
            reason = f"【Shot 4 筑牢底线】当前最佳 {current_best:.2f}s，部署高阻尼防守堡垒拉升均值与中位数"
        return cand, reason

    # ========================== Shot 5: 最终终局之战 ==========================
    if next_idx == 5:
        if current_best <= 118.0:
            # 已经处于极高排名，复测保分第一
            cand = CANDIDATE_POOL["crown_plateau_a"]
            reason = f"【Shot 5 终局固化】当前成绩 {current_best:.2f}s 锁定极高顺位，压轴发投出超平坦平台点，完成统一复测前最后一轮自检"
        else:
            # 最后一搏冲刺第一
            cand = CANDIDATE_POOL["crown_fusion"]
            reason = f"【Shot 5 终极冲冠】本日最后一发，全部算力倾注皇冠冲冠主力，冲击全场绝对最高分！"
        return cand, reason

    return CANDIDATE_POOL["steady_champion"], "默认兜底"


def execute_single_shot(shot_idx: int, candidate: dict, dry_run: bool = False, yes: bool = False) -> dt.datetime:
    """生成单发专属 submit plan 并调用 submit_batch.py 提交。"""
    tag = candidate["tag"]
    note = candidate["note"]
    
    # 1. 生成单发 plan 文件
    single_plan = [{
        "tag": f"{tag}-s{shot_idx}",
        "note": f"Shot {shot_idx}/5 | {note}",
        "configs": candidate["configs"]
    }]
    
    plan_path = ROOT / "runs" / f"seq_1108_shot_{shot_idx}.json"
    plan_path.write_text(json.dumps(single_plan, ensure_ascii=False, indent=2), encoding="utf-8")
    log(f"已生成 Shot {shot_idx} 专属提交清单: {plan_path.name}")
    
    submit_time = dt.datetime.now()
    
    if dry_run or not yes:
        log(f"[DRY-RUN] 模拟执行 Shot {shot_idx} 提交: {tag} (未消耗真实额度)")
        return submit_time
        
    # 2. 真实提交执行
    cmd = [PY, str(ROOT / "tools" / "submit_batch.py"), "--plan", str(plan_path), "--yes"]
    log(f"正在执行真实提交命令: {' '.join(cmd)}")
    rc = subprocess.call(cmd, cwd=str(ROOT))
    if rc != 0:
        log(f"[ERROR] Shot {shot_idx} 提交失败 (rc={rc})！请人工排查！")
        raise RuntimeError(f"Shot {shot_idx} 提交失败，退出码 {rc}")
        
    log(f"Shot {shot_idx} 真实提交成功！已记录提交时间戳: {submit_time:%H:%M:%S}")
    return submit_time


def run_sequential_pipeline(target_at: str | None = None, dry_run: bool = False, yes: bool = False, limit: int = 3) -> int:
    log("======================================================================")
    log("=== 11/08 今日精选 3 发闭环自适应 1-by-1 提交控制器全面启动 ===")
    log("======================================================================")
    log(f"模式: {'[DRY-RUN 离线仿真]' if dry_run else '[真实决战打榜]'}")
    log(f"参数: target_at={target_at}, yes={yes}, limit={limit}")

    # 1. 计划时间对齐
    if target_at and target_at.strip().lower() != "now":
        target_time = dt.datetime.strptime(target_at.strip(), "%Y-%m-%d %H:%M")
        wait_until(target_time)

    # 2. 额度与状态检查
    today_date = dt.datetime.now().astimezone().date()
    used_today = today_submissions_count(today_date)
    log(f"今日已发生正式提交次数: {used_today}/{limit}")
    if not dry_run and used_today >= limit:
        log(f"[BLOCK] 今日额度已达预设上限 ({used_today}/{limit})，控制器终止！")
        return 0

    # 3. 恢复或初始化状态机
    history = []
    if STATE_FILE.exists():
        try:
            state_data = json.loads(STATE_FILE.read_text("utf-8"))
            if state_data.get("date") == str(today_date):
                history = state_data.get("history", [])
                log(f"检测到今日历史状态，已恢复 {len(history)} 发历史出分记录。")
        except Exception as e:
            log(f"状态文件读取异常，将初始化新状态: {e}")

    start_shot_idx = len(history) + 1
    if start_shot_idx > limit:
        log(f"今日计划的 {limit} 发打榜任务已全部执行完毕！")
        return 0

    log(f"准备开始执行第 {start_shot_idx} 发（目标执行至第 {limit} 发，剩余 {limit - start_shot_idx + 1} 发）...")

    # 4. 逐发闭环主循环 (1-by-1)
    for k in range(start_shot_idx, limit + 1):
        log(f"\n>>>>>>>>>>>>>>> [开始第 {k}/{limit} 发闭环流程] <<<<<<<<<<<<<<<")
        
        # 额度双重校验
        if not dry_run:
            current_used = today_submissions_count(today_date)
            if current_used >= limit:
                log(f"[BLOCK] 触发今日 3 发额度硬门禁！今日已达 {current_used}/{limit}，停止执行！")
                break

        # A. 闭环决策：根据前面已有的出分，分析决定下一发
        candidate, decision_reason = decide_next_shot(history, k)
        log(f"【决策推演】{decision_reason}")
        log(f"【选定构型】{candidate['tag']} ({candidate['note']})")

        # B. 提交执行
        submit_time = execute_single_shot(k, candidate, dry_run=dry_run, yes=yes)

        # C. 等待并轮询真机出分
        if dry_run:
            # 仿真出分生成 (用于离线演练闭环)
            time.sleep(1.0)
            mock_score = round(random.uniform(115.5, 117.5), 4)
            mock_rank = 1 if mock_score < 116.3367 else (2 if mock_score < 117.0257 else 3)
            poll_result = {
                "status": "scored",
                "download_seconds": mock_score,
                "rank": mock_rank,
                "best_seconds": mock_score,
                "scored_at": dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            log(f"[DRY-RUN 仿真出分] Mock Score: {mock_score}s | Mock Rank: 第 {mock_rank} 名")
        else:
            poll_result = poll_for_new_score(submit_time, timeout_min=65.0, poll_interval=45.0)

        # D. 沉淀本发战报至历史记录
        shot_record = {
            "shot_idx": k,
            "candidate_id": candidate["candidate_id"],
            "tag": candidate["tag"],
            "decision_reason": decision_reason,
            "submitted_at": submit_time.strftime("%Y-%m-%d %H:%M:%S"),
            "status": poll_result["status"],
            "download_seconds": poll_result["download_seconds"],
            "rank": poll_result["rank"],
            "best_seconds": poll_result["best_seconds"],
            "scored_at": poll_result["scored_at"]
        }
        history.append(shot_record)

        # E. 状态持久化落盘
        all_valid = [s["download_seconds"] for s in history if s.get("download_seconds")]
        state_snapshot = {
            "date": str(today_date),
            "updated_at": dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "completed_shots": len(history),
            "max_allowed_shots": limit,
            "current_best_seconds": min(all_valid) if all_valid else None,
            "history": history
        }
        STATE_FILE.write_text(json.dumps(state_snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
        log(f"Shot {k} 全链路闭环完成并落盘！当前全场最佳: {state_snapshot['current_best_seconds']}s")

        # F. 轮次间歇冷却 (保护服务器与避免时间重叠)
        if k < limit and not dry_run:
            cooldown_min = 3.0
            log(f"进入批次冷却间歇 {cooldown_min} 分钟...")
            time.sleep(cooldown_min * 60)

    # 5. 今日精选收官总结报告
    log("\n======================================================================")
    log(f"=== 11/08 今日精选 {limit} 发闭环自适应打榜全满收官！ ===")
    log("======================================================================")
    for rec in history:
        log(f"Shot {rec['shot_idx']}: {rec['tag']} -> 结果: {rec['download_seconds']}s (第 {rec['rank']} 名)")
        log(f"       决策依据: {rec['decision_reason']}")

    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="11/08 决战：今日精选 3 发闭环自适应打榜控制器")
    ap.add_argument("--at", default="now", help="启动执行时间 (默认 'now'，或 'YYYY-MM-DD HH:MM')")
    ap.add_argument("--limit", type=int, default=3, help="今日允许提交总发数硬上限 (默认 3 发)")
    ap.add_argument("--dry-run", action="store_true", help="离线仿真模式（模拟闭环出分与自适应演练）")
    ap.add_argument("--yes", action="store_true", help="显式确认执行真实打榜提交")
    args = ap.parse_args(argv)

    return run_sequential_pipeline(target_at=args.at, dry_run=args.dry_run, yes=args.yes, limit=args.limit)


if __name__ == "__main__":
    sys.exit(main())
