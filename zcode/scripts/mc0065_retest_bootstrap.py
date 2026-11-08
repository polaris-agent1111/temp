# -*- coding: utf-8 -*-
"""0065 - official unified-retest sampling distribution: 100k-replicate Monte Carlo
bootstrap and 99.9% CI stability check.

Protocol framing (task 0065):
  Official scoring: each submission is evaluated 3 times on the official machine and
  the average is recorded as the official score S. Leaderboard keeps the best score
  per team. Fairness clause: "top submissions on the leaderboard will be uniformly
  retested to prevent overfitting to specific random seeds".
  Retest model: a retest produces another official score R drawn from the same
  per-config official-score distribution D(mu, sigma). Since observed scores are
  already 3-run means, sigma estimated from same-config pairs/triples of official
  scores is the std of the 3-run-mean itself; equivalently single-run std is
  sigma_run = sigma * sqrt(3), and a retest R = mean of 3 single runs has std sigma.

Data provenance (all read-only sources, no credentials):
  G1  v1 / v1b          byte-identical re-submission, 11-05 13:25/14:23
                        runs/official_results.jsonl        -> [245.9950, 243.9583]
  G2  hr-44-60-4000 x3  same config, 11-06 00:56:29/35/40
                        runs/official_results.jsonl        -> [137.091, 137.384, 142.7837]
  G3  shot4 / shot5     SHA-256 identical tree f2707ede93138b6e, 11-07 00:56/01:06
                        runs/sequential_adaptive_log.jsonl -> [140.0247, 155.1607]
  G4  (external, Lead intel doc) dafeiyu same-config 4 shots 11-06:
                        [122.40, 122.51, 122.18, 122.45]   (CV 0.29%, sigma ~= 0.37)

Honesty note: the task asks to "verify retest-mean upper bound strictly < 119.8293s".
This script TESTS the proposition; it does not assume it. The verdict is printed and
must be reported as-is (AGENTS.md anti-overfitting discipline; 0058 precedent).

stdlib-only, deterministic seeds. Run:  python -I zcode/scripts/mc0065_retest_bootstrap.py
"""
import math
import random
import statistics as st

TARGET = 119.8293          # Catnet rank-1 score (retest proposition threshold)
OUR_RECORD = 124.3683      # our best official score (shot2, 11-07, n=1 for this config)
Z999 = 3.090232306167813   # Phi^{-1}(0.999)
Z95 = 1.6448536269514722   # Phi^{-1}(0.95) one-sided

# ---------------------------------------------------------------- data
GROUPS = {
    "G1_v1_v1b":        [245.9950, 243.9583],
    "G2_hr44_60_x3":    [137.091, 137.384, 142.7837],
    "G3_shot4_shot5":   [140.0247, 155.1607],
    "G4_dafeiyu_ext":   [122.40, 122.51, 122.18, 122.45],
}

Phi = lambda z: 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def regime_table():
    print("== A. same-config official-score regimes ==")
    rows = []
    for name, xs in GROUPS.items():
        mu = st.mean(xs)
        sd = st.stdev(xs) if len(xs) > 1 else float("nan")
        # 95% CI for sigma from chi-square (normal approx), df = n-1
        n = len(xs)
        lo = hi = float("nan")
        if n > 1:
            df = n - 1
            # exact chi-square quantiles for df=1..3 (all our group sizes), WH else
            _chi = {(1, 0.025): 0.0009821, (1, 0.975): 5.02389,
                    (2, 0.025): 0.0506356, (2, 0.975): 7.37776,
                    (3, 0.025): 0.215795, (3, 0.975): 9.34840}
            def chi2_inv(p, df):
                if (df, p) in _chi:
                    return _chi[(df, p)]
                z = {0.025: -1.959964, 0.975: 1.959964}[p]
                return df * (1 - 2 / (9 * df) + z * math.sqrt(2 / (9 * df))) ** 3
            lo = sd * math.sqrt(df / chi2_inv(0.975, df))
            hi = sd * math.sqrt(df / chi2_inv(0.025, df))
        rows.append((name, n, mu, sd, lo, hi))
        print("  %-16s n=%d mean=%9.4f sigma=%7.4f  95%%CI sigma=[%.3f, %.3f]"
              % (name, n, mu, sd, lo, hi))
    return rows


def retest_draw(rng, mu, sigma_score, n_runs=3, sigma_uncert=None):
    """One retest official score = mean of n_runs single evaluations.
    sigma_score  = std of an official 3-run-mean (as estimated from data)
    sigma_run    = sigma_score * sqrt(n_runs)
    sigma_uncert = optional (k, theta): draw a Gamma(k, theta) multiplier on
                   sigma_run per replicate to propagate small-n estimation
                   uncertainty of sigma (double Monte Carlo)."""
    s_run = sigma_score * math.sqrt(n_runs)
    if sigma_uncert is not None:
        k, theta = sigma_uncert
        s_run *= rng.gammavariate(k, theta)
    return mu + st.fmean(rng.gauss(0.0, s_run) for _ in range(n_runs)) / 1.0


def quantile(sorted_xs, q):
    idx = q * (len(sorted_xs) - 1)
    lo = int(math.floor(idx)); hi = min(lo + 1, len(sorted_xs) - 1)
    return sorted_xs[lo] + (sorted_xs[hi] - sorted_xs[lo]) * (idx - lo)


def mc_parametric(mu, sigma_score, n_rep=100_000, seed=20261107, sigma_uncert=None):
    rng = random.Random(seed)
    acc = []
    for _ in range(n_rep):
        acc.append(retest_draw(rng, mu, sigma_score, sigma_uncert=sigma_uncert))
    acc.sort()
    p_le_target = sum(1 for x in acc if x <= TARGET) / len(acc)
    return {
        "mean": st.fmean(acc),
        "q50": quantile(acc, 0.50),
        "q95": quantile(acc, 0.95),
        "q99": quantile(acc, 0.99),
        "q999": quantile(acc, 0.999),
        "P_le_target": p_le_target,
    }


def mc_nonparametric(mu, pool, n_rep=100_000, seed=20261107):
    """Resample one within-group deviation (observed official score minus its
    group mean) as one retest official score. Deviations are level-free by
    construction and already embed the 3-run averaging."""
    rng = random.Random(seed + 1)
    acc = []
    for _ in range(n_rep):
        acc.append(mu + rng.choice(pool))
    acc.sort()
    p_le_target = sum(1 for x in acc if x <= TARGET) / len(acc)
    return {
        "mean": st.fmean(acc),
        "q50": quantile(acc, 0.50),
        "q95": quantile(acc, 0.95),
        "q99": quantile(acc, 0.99),
        "q999": quantile(acc, 0.999),
        "P_le_target": p_le_target,
    }


def main():
    rows = regime_table()

    # deviation pools (observed official score minus own-group mean)
    pool_ours, pool_all = [], []
    for name, xs in GROUPS.items():
        m = st.mean(xs)
        dev = [x - m for x in xs]
        pool_all.extend(dev)
        if name != "G4_dafeiyu_ext":
            pool_ours.extend(dev)
    print("  deviation pool: ours n=%d  full n=%d" % (len(pool_ours), len(pool_all)))

    # ---------------------------------------------- B. proposition test at mu = OUR_RECORD
    print("\n== B. retest distribution at mu=%.4f (our record config, only observation) ==" % OUR_RECORD)
    print("   regime                 P(R<=119.8293)   mean(R)    q95     q99     q99.9")
    for name, n, mu, sd, lo, hi in rows:
        if n < 2:
            continue
        r = mc_parametric(OUR_RECORD, sd, n_rep=100_000, seed=20261107)
        print("  %-18s sigma=%6.3f  %10.4f  %8.2f %8.2f %8.2f %8.2f"
              % (name, sd, r["P_le_target"], r["mean"], r["q95"], r["q99"], r["q999"]))
    rp = mc_nonparametric(OUR_RECORD, pool_ours)
    print("  nonparam (ours dev pool, n=%d): P=%.4f mean=%.2f q95=%.2f q999=%.2f"
          % (len(pool_ours), rp["P_le_target"], rp["mean"], rp["q95"], rp["q999"]))
    rp2 = mc_nonparametric(OUR_RECORD, pool_all)
    print("  nonparam (full dev pool, n=%d): P=%.4f mean=%.2f q95=%.2f q999=%.2f"
          % (len(pool_all), rp2["P_le_target"], rp2["mean"], rp2["q95"], rp2["q999"]))
    # double MC: propagate sigma estimation uncertainty (worst regime G3, n=2)
    sd_g3 = st.stdev(GROUPS["G3_shot4_shot5"])
    # gamma matching a chi-square_1 scaled uncertainty on sigma^2 (n=2 -> df=1)
    rd = mc_parametric(OUR_RECORD, sd_g3, n_rep=100_000, seed=20261107,
                       sigma_uncert=(0.5, 2.0))
    print("  double-MC (G3 sigma uncertainty, df=1): P=%.4f q95=%.2f q999=%.2f"
          % (rd["P_le_target"], rd["q95"], rd["q999"]))

    # ---------------------------------------------- C. required mu for the proposition
    print("\n== C. required mu so that P99.9(retest mean) < 119.8293 ==")
    print("   analytic: mu_max = 119.8293 - z_0.999 * sigma ; MC check at that mu")
    for name, n, mu, sd, lo, hi in rows:
        if n < 2:
            continue
        mu_max = TARGET - Z999 * sd
        chk = mc_parametric(mu_max, sd, n_rep=100_000, seed=20261108)
        # fraction of replicates above target should be ~0.001 by construction
        print("  %-18s sigma=%6.3f  mu_max=%8.4f   MC P(R>target)=%.5f (nominal 0.001)"
              % (name, sd, mu_max, 1 - chk["P_le_target"]))
    print("  => gap from OUR_RECORD=%.4f to mu_max:" % OUR_RECORD)
    for name, n, mu, sd, lo, hi in rows:
        if n < 2:
            continue
        print("     sigma=%6.3f: gap %6.2f s" % (sd, OUR_RECORD - (TARGET - Z999 * sd)))

    # ---------------------------------------------- D. 99.9% quantile stability across seeds
    print("\n== D. 99.9%%-quantile estimator stability (3 seeds x 100k) ==")
    for name, n, mu, sd, lo, hi in rows:
        if n < 2:
            continue
        q999s = []
        p999s = []
        for seed in (1, 2, 3):
            r = mc_parametric(OUR_RECORD, sd, n_rep=100_000, seed=seed)
            q999s.append(r["q999"]); p999s.append(r["P_le_target"])
        spread = max(q999s) - min(q999s)
        pspread = max(p999s) - min(p999s)
        # analytic MC standard error of a tail quantile ~ sqrt(p(1-p)/n)/f(q)
        print("  %-18s sigma=%6.3f  q999 seeds=%s  spread=%.3f s ; P seeds=%s spread=%.5f"
              % (name, sd, ["%.2f" % x for x in q999s], spread,
                 ["%.4f" % x for x in p999s], pspread))

    # ---------------------------------------------- E. incumbent (Catnet) retest regression
    print("\n== E. incumbent retest risk (selection regression of a min-of-N record) ==")
    print("   recorded best = min of n draws from N(mu_true, sigma); E[min_n] = mu_true + m_n*sigma")
    # E[Z_(1)] for standard normal order statistic, n=14 (Catnet attempts with scores)
    m14 = -1.699   # expected minimum of 14 standard normals (numerical table value)
    for sig in (1.50, 2.15, 2.68):
        mu_true = TARGET - m14 * sig      # = 119.8293 + 1.699*sigma
        se = sig / math.sqrt(3.0)         # retest = another 3-run mean
        p_le = Phi((TARGET - mu_true) / se)
        p_le121 = Phi((121.0 - mu_true) / se)
        p_le123 = Phi((123.0 - mu_true) / se)
        print("  sigma=%4.2f -> mu_true~%.2f  P(retest<=119.83)=%.4f  P(<=121)=%.4f  P(<=123)=%.4f"
              % (sig, mu_true, p_le, p_le121, p_le123))

    # ---------------------------------------------- F. our own retest regression context
    print("\n== F. our record 124.3683 under retest (config n=1, so no selection correction" 
          " within config; but min over 15 mixed-config official scores) ==")
    for sig in (1.44, 3.20, 10.70):
        se = sig / math.sqrt(3.0)
        print("  sigma=%5.2f: P(single fresh draw <=119.83)=%.4f ; P(retest mean<=119.83)=%.4f"
              % (sig, Phi((TARGET - OUR_RECORD) / sig), Phi((TARGET - OUR_RECORD) / se)))

    print("\nVERDICT: proposition 'retest-mean 99.9%% upper bound < %.4f' is NOT verified"
          % TARGET)
    print("  under any empirical sigma regime at the demonstrated mu=%.4f;" % OUR_RECORD)
    print("  it becomes true only if mu_off <= mu_max table (regime C), i.e. a further")
    print("  5.7s (sigma=0.37, calmest external regime) to 37.6s (sigma=10.7) improvement.")


if __name__ == "__main__":
    main()
