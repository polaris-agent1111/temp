# -*- coding: utf-8 -*-
"""0067 - opponent counterattack theoretical lower bounds and a tiered
counter-strategy library.

Data provenance (read-only):
  intel/raw/leaderboard_20261106T1515.json  (newest snapshot, 11-06 15:15)
  docs/analysis/opponent-tracks.md          (full attempt sequences to 11-05 23:01)
  runs/sequential_adaptive_log.jsonl        (our 11-07 five-shot official scores)

Key facts (as of snapshot 2026-11-06 15:15):
  1 Catnet   119.8293 (n=14, last 11-05 22:35) - evening-activity team, 3 breakthroughs/14
  2 hashkimi 120.2670 (n=7,  last 11-06 11:42) - ONE family jump -32.3747s on 11-06
  3 我不想写实验报告 121.5217 (n=6)
  4 大肥鱼   122.4027 (n=15)  5 光明未来 122.7073 (n=13)
  6 ResearchSN 125.0620 (n=2, new 11-06)      7 无法导入 131.2653
  8 赛博coder (us) 133.086 on snapshot; 11-07 five shots lifted our best to 124.3683.

Model: per-opponent Monte Carlo path simulation over the remaining window
(11-07 .. 11-16 23:59, 10 days, max 5 attempts/day):
  - breakthrough attempt-level hit probability p_hit (empirical per team),
  - step size mixture: 'refinement' (empirical safe-zone steps, median -2.4s)
    vs 'family jump' (empirical jump pool incl. hashkimi -32.37, Catnet -7.14,
    blueman -39.89 trap-exit excluded from competent-team pool but kept as
    hashkimi-tail scenario), mixture weight w_jump,
  - floor F_team ~ Normal(F_mu, F_sd) truncating improvement,
  - record only improves (leaderboard keeps best).
Outputs: distribution of each opponent's final best; P(final <= threshold)
for thresholds 119.8293 / 118 / 117 / 115 / our 124.3683.

Compliance: analysis only; no platform access, no submission, no probing.
Run: python -I zcode/scripts/strategy0067_counterplay.py
"""
import math
import random
import statistics as st

# ---------------------------------------------------------------- data
SNAPSHOT = "intel/raw/leaderboard_20261106T1515.json (11-06 15:15)"
OPPONENTS = {
    # name: dict(best, n_attempts, p_hit, w_jump, refinement_steps, jump_steps, floor_mu, floor_sd)
    "Catnet": dict(
        best=119.8293, n=14, p_hit=3 / 14, w_jump=0.15,
        refine=[-2.2690, -1.2820, -0.62, -1.33],      # + all-team refinement pool below
        jump=[-7.1354, -9.3960, -7.6400],             # competent-team family jumps
        floor_mu=112.0, floor_sd=2.0),
    "hashkimi": dict(
        best=120.2670, n=7, p_hit=1 / 7, w_jump=0.30,  # demonstrated -32.37 jump capability
        refine=[-2.4100],
        jump=[-32.3747, -7.1354, -9.3960, -19.7050],
        floor_mu=113.0, floor_sd=2.5),
    "woxiangxie": dict(   # 我不想写实验报告
        best=121.5217, n=6, p_hit=2 / 6, w_jump=0.20,
        refine=[-9.3960, -4.0487, -1.60],
        jump=[-7.6400, -9.3960],
        floor_mu=112.5, floor_sd=2.2),
}
ALL_REFINE = [-2.2690, -1.2820, -0.62, -1.33, -0.58, -0.85, -0.62, -2.41, -0.65,
              -1.40, -0.99, -2.02, -3.48, -9.40, -4.05, -1.60, -2.81]
DAYS_LEFT = 10          # 11-07 .. 11-16 (competition ends 11-16 23:59)
ATTEMPTS_PER_DAY = 5
NREP = 20_000
THRESHOLDS = (124.3683, 119.8293, 118.0, 117.0, 115.0)
OUR_RECORD = 124.3683


def trunc_norm(rng, mu, sd, hi):
    """Draw a floor value in (-inf, hi) from N(mu, sd) by rejection."""
    for _ in range(100):
        x = rng.gauss(mu, sd)
        if x < hi:
            return x
    return mu


def sim_team(name, spec, seed):
    rng = random.Random(seed)
    finals = []
    refine = spec["refine"] + ALL_REFINE
    jump = spec["jump"]
    for _ in range(NREP):
        best = spec["best"]
        floor = trunc_norm(rng, spec["floor_mu"], spec["floor_sd"], best)
        for _day in range(DAYS_LEFT):
            # daily activity: teams do not necessarily spend all 5 attempts
            n_att = min(5, max(0, int(rng.gauss(3.0, 1.4))))
            for _a in range(n_att):
                if best <= floor:
                    break
                if rng.random() < spec["p_hit"]:
                    step = rng.choice(jump) if rng.random() < spec["w_jump"] else rng.choice(refine)
                    best = max(floor, best + step)   # step negative
        finals.append(best)
    finals.sort()
    q = lambda p: finals[min(len(finals) - 1, int(p * len(finals)))]
    probs = {t: sum(1 for x in finals if x <= t) / len(finals) for t in THRESHOLDS}
    return {"mean": st.fmean(finals), "q05": q(0.05), "q50": q(0.50), "q95": q(0.95),
            "probs": probs}


def main():
    print("== A. opponent state (snapshot %s) ==" % SNAPSHOT)
    for name, s in OPPONENTS.items():
        print("  %-10s best=%.4f n=%2d p_hit=%.3f w_jump=%.2f floor~N(%.1f, %.1f)"
              % (name, s["best"], s["n"], s["p_hit"], s["w_jump"], s["floor_mu"], s["floor_sd"]))
    print("  window: 11-07..11-16 (%d days x <=5 attempts), %d MC reps/team" % (DAYS_LEFT, NREP))

    print("\n== B. final-best distribution per opponent (%d reps) ==" % NREP)
    results = {}
    for i, (name, spec) in enumerate(OPPONENTS.items()):
        r = sim_team(name, spec, seed=20261107 + i)
        results[name] = r
        print("  %-10s final best: mean=%.2f  q05=%.2f  q50=%.2f  q95=%.2f" %
              (name, r["mean"], r["q05"], r["q50"], r["q95"]))
        print("             " + "  ".join("P(<= %.4f)=%.3f" % (t, r["probs"][t]) for t in THRESHOLDS))

    print("\n== C. theoretical lower-bound synthesis ==")
    print("  global physical envelope (all teams, from repo canon): 106.597 s")
    print("  env floor estimate F (opponent-tracks S5.4): 112 +- 4 s")
    for name, spec in OPPONENTS.items():
        r = results[name]
        print("  %-10s max-theoretical floor = %.1f (envelope-capped); model q05 = %.2f;"
              " P(reach <=115) = %.3f" % (name, spec["floor_mu"], r["q05"], r["probs"][115.0]))

    print("\n== D. counter-strategy tiers (what we must hold) ==")
    rows = [
        ("T0 hold vs status quo", "opponents stall near current bests",
         "our record 124.3683 keeps rank 4-6; no action"),
        ("T1 defend vs 119.83 held", "Catnet 119.8293 stands all window",
         "need official <= 119.82 once: record-family micro-drop (39/39, 40/40) or p96 champ family"),
        ("T2 defend vs 117-118", "one more Catnet/hashkimi refinement (-2.4 median)",
         "need official <= 116.9: p96 champ family (local 116.542, official n=1 = 124.37 -> delta risk high)"),
        ("T3 defend vs 112-115", "family-jump cascade (hashkimi demonstrated -32.37)",
         "need official <= 111.9: requires NEW family below local 112.30 floor or variance lottery (min-of-5, sigma>=6: P~53%%)"),
    ]
    for tier, trig, resp in rows:
        print("  %-24s | %-42s | %s" % (tier, trig, resp))

    print("\n== E. retest-regression overlay (from 0065 MC) ==")
    print("  under uniform retest, a min-of-N record regresses: Catnet mu_true ~ 122.4-124.4")
    print("  (sigma 1.5-2.68) vs our config-n=1 record 124.37 + no selection correction;")
    print("  => the retest-comparable gap vs Catnet is ~0-2 s, NOT 4.5 s. Defense should")
    print("  target low-mu AND low-sigma configs (pacing-only 5/6.bin, burst<=60, no 950us tick).")


if __name__ == "__main__":
    main()
