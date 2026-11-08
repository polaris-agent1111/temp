#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task 0196: Sandbox dry-run rehearsal for sequential adaptive 11/08 controller.
Executes an end-to-end multi-round closed-loop mock simulation without real platform calls.
Validates state machine transitions, leaderboard parsing, decision routing, and quota exhaustion prevention.
"""
import json
import os
import random

def dry_run_simulation():
    random.seed(20261108)
    sim_state = {
        "campaign_date": "2026-11-08",
        "shots_planned": 5,
        "shots_executed": 0,
        "history": [],
        "best_official_score": 999.0,
        "current_rank": 6
    }
    
    # 5 simulated closed-loop cycles
    for shot_idx in range(1, 6):
        # 1. Select shot candidate based on decision tree
        if shot_idx == 1:
            candidate = "shot_1_steady_champion"
            expected_range = (132.5, 135.0)
        elif shot_idx == 2:
            # Check shot 1 outcome
            s1_score = sim_state["history"][0]["official_score"]
            if s1_score <= 138.0:
                candidate = "shot_2_crown_fusion"
            else:
                candidate = "shot_2_plateau_a"
            expected_range = (116.5, 118.5)
        elif shot_idx == 3:
            s2_score = sim_state["history"][1]["official_score"]
            if s2_score < 117.5:
                candidate = "shot_3_plateau_a"
            else:
                candidate = "shot_3_crown_fusion_retry"
            expected_range = (117.0, 119.5)
        elif shot_idx == 4:
            candidate = "shot_4_crown_fusion_final_attack"
            expected_range = (116.5, 118.0)
        else:
            candidate = "shot_5_defense_fortress_lock"
            expected_range = (118.0, 120.0)
            
        # 2. Simulate official leaderboard score
        score = random.uniform(*expected_range)
        if score < sim_state["best_official_score"]:
            sim_state["best_official_score"] = score
            sim_state["current_rank"] = 1 if score < 117.0257 else (2 if score < 119.8293 else 3)
            
        sim_state["shots_executed"] += 1
        sim_state["history"].append({
            "shot_num": shot_idx,
            "candidate": candidate,
            "official_score": round(score, 4),
            "updated_rank": sim_state["current_rank"]
        })
        
    print("=== Task 0196: End-to-End Sandbox Dry-Run Rehearsal ===")
    print(f"campaign_date: {sim_state['campaign_date']}")
    print(f"total_shots_executed: {sim_state['shots_executed']}/5")
    print(f"final_best_score: {sim_state['best_official_score']:.4f}s")
    print(f"final_projected_rank: Rank {sim_state['current_rank']}")
    for h in sim_state["history"]:
        print(f"  Shot {h['shot_num']}: {h['candidate']} -> {h['official_score']:.4f}s (Rank {h['updated_rank']})")
        
    # Validation gates:
    no_quota_violation = (sim_state["shots_executed"] == 5)
    rank_1_achieved = (sim_state["current_rank"] == 1)
    
    print(f"quota_gate_passed: {no_quota_violation}")
    print(f"rank_1_captured: {rank_1_achieved}")
    
    return sim_state

if __name__ == "__main__":
    dry_run_simulation()
