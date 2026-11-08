# -*- coding: utf-8 -*-
"""0052 EVT 计算：基于 runs/results.jsonl 真实样本，拟合冠军构型下尾分布，
精确计算 n=5 抽样极小值的期望与 P(min5 in [107,118])，含本地->官方 δ 场景映射。
只读 runs/results.jsonl，不写任何 runs/ 文件。输出纯文本统计。"""
import json, math, statistics, itertools, random

RESULTS = r"E:\Download\iDSN\runs\results.jsonl"

def load_valid():
    rows = []
    with open(RESULTS, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
            except Exception:
                continue
            if d.get("valid") is True and not (d.get("tag") or "").startswith("load-"):
                rows.append(d)
    return rows

rows = load_valid()
champ = sorted(d["total_seconds"] for d in rows
               if "p100M" in d["tag"] and "p96M" in d["tag"])
strict = sorted(d["total_seconds"] for d in rows
                if d["tag"].startswith("test-hybrid-tb4-p100M-p96M-r"))
hybrid = sorted(d["total_seconds"] for d in rows
                if "hybrid" in d["tag"])

print("== data ==")
print("valid non-load rows:", len(rows))
print("champ family n=%d:" % len(champ), [round(v,3) for v in champ])
print("strict base repeats n=%d:" % len(strict), [round(v,3) for v in strict])
print("pooled hybrid n=%d" % len(hybrid))

def desc(v):
    return dict(n=len(v), mean=statistics.mean(v), median=statistics.median(v),
                std=statistics.stdev(v) if len(v) > 1 else 0.0,
                mn=v[0], mx=v[-1])

for name, v in [("champ10", champ), ("strict4", strict), ("hybrid58", hybrid)]:
    s = desc(v)
    print("%-9s n=%2d mean=%7.3f median=%7.3f std=%6.3f min=%7.3f max=%7.3f" %
          (name, s["n"], s["mean"], s["median"], s["std"], s["mn"], s["mx"]))

# ---------- exact best-of-5 on a discrete empirical distribution ----------
def exact_min5(values):
    """iid draws with replacement from `values`; exact E[min of 5] and CDF points."""
    uniq = sorted(set(values))
    n = len(values)
    p = {v: values.count(v) / n for v in uniq}
    F = 0.0  # P(X <= previous)
    Em = 0.0
    cdf = {}
    for v in uniq:
        Fv = F + p[v]                      # P(X <= v)
        Pmin_ge_v = (1.0 - F) ** 5         # P(min5 >= v) given min>=v means all >= v ... careful
        # P(min5 = v) = P(all >= v) - P(all > v) = (1-F(prev))**5 - (1-F(v))**5
        Pmin = (1.0 - F) ** 5 - (1.0 - Fv) ** 5
        Em += v * Pmin
        cdf[v] = 1.0 - (1.0 - Fv) ** 5     # P(min5 <= v)
        F = Fv
    return Em, cdf

def P_win(cdf, lo, hi):
    """P(min5 in [lo, hi]] = P(min<=hi) - P(min<lo)  (continuous approx on discrete)"""
    ks = [k for k in cdf]
    P_hi = 1 - (1 - sum(1 for x in [k for k in cdf if k <= hi]) / len(
        [1 for _ in cdf])) ** 0  # placeholder, replaced below
    return None

def P_min5_between(values, lo, hi):
    n = len(values)
    Fl = sum(1 for x in values if x <= lo) / n
    Fh = sum(1 for x in values if x <= hi) / n
    return (1 - Fl) ** 5 - (1 - Fh) ** 5   # P(min>lo) - P(min>hi) = P(lo < min <= hi)

for name, v in [("champ10", champ), ("strict4", strict), ("hybrid58", hybrid)]:
    Em, cdf = exact_min5(v)
    p_118 = 1 - (1 - sum(1 for x in v if x <= 118) / len(v)) ** 5
    p_band = P_min5_between(v, 107, 118)
    p_133 = 1 - (1 - sum(1 for x in v if x <= 133.086) / len(v)) ** 5
    print("%-9s exact E[min5]=%7.3f  P(min5<=118)=%.4f  P(107<min5<=118)=%.4f  P(min5<=133.086)=%.4f" %
          (name, Em, p_118, p_band, p_133))

# ---------- parametric fits ----------
def norm_P(x, mu, sg):
    return 0.5 * (1 + math.erf((x - mu) / (sg * math.sqrt(2))))

def norm_min5(mu, sg, lo=None, hi=None):
    out = {}
    if hi is not None:
        out["P<=%g" % hi] = 1 - (1 - norm_P(hi, mu, sg)) ** 5
    if lo is not None and hi is not None:
        out["P(%g,%g]" % (lo, hi)] = ((1 - norm_P(lo, mu, sg)) ** 5 -
                                      (1 - norm_P(hi, mu, sg)) ** 5)
    # E[min5] = mu - sigma * E[min of 5 std normals];  E[Z_(1)] for n=5 = -1.16296
    out["E[min5]"] = mu - 1.16296 * sg
    return out

def weibull_mle(xs):
    """2-param Weibull MLE by profile likelihood over shape k."""
    n = len(xs)
    logs = [math.log(x) for x in xs]
    def negll(k):
        m = sum(x ** k for x in xs) / n
        lam = m ** (1.0 / k)
        ll = (n * math.log(k) - n * k * math.log(lam)
              + (k - 1) * sum(logs) - sum((x / lam) ** k for x in xs))
        return -ll
    lo, hi = 0.2, 30.0
    gr = (math.sqrt(5) - 1) / 2
    a, b = lo, hi
    for _ in range(200):
        c, d = b - gr * (b - a), a + gr * (b - a)
        if negll(c) < negll(d):
            b = d
        else:
            a = c
    k = (a + b) / 2
    lam = (sum(x ** k for x in xs) / n) ** (1.0 / k)
    return k, lam

def wb_cdf(x, k, lam):
    if x <= 0: return 0.0
    return 1 - math.exp(-(x / lam) ** k)

def wb_min5(k, lam, lo, hi):
    Ph = 1 - (1 - wb_cdf(hi, k, lam)) ** 5
    Pl = 1 - (1 - wb_cdf(lo, k, lam)) ** 5
    return Ph, Ph - Pl

print("\n== normal fits (local) ==")
for name, v in [("champ10", champ), ("strict4", strict), ("hybrid58", hybrid)]:
    mu, sg = statistics.mean(v), statistics.stdev(v)
    r = norm_min5(mu, sg, 107, 118)
    r["P<=118"] = r.pop("P<=%g" % 118)
    print("%-9s mu=%7.3f sg=%6.3f  P(min5<=118)=%.4f  P(107,118]=%.4f  E[min5]=%7.3f" %
          (name, mu, sg, r["P<=118"], r["P(%g,%g]" % (107, 118)], r["E[min5]"]))

print("\n== Weibull MLE fits (local) ==")
for name, v in [("champ10", champ), ("strict4", strict), ("hybrid58", hybrid)]:
    k, lam = weibull_mle(v)
    Ph, Pband = wb_min5(k, lam, 107, 118)
    # E[min5] numeric integration over [0, 400]
    m = 400000
    step = 400.0 / m
    s = 0.0
    for i in range(m):
        t = (i + 0.5) * step
        s += (1 - wb_cdf(t, k, lam)) ** 5 * step
    print("%-9s k=%.4f lam=%.3f  P(min5<=118)=%.4f  P(107,118]=%.4f  E[min5]=%.3f" %
          (name, k, lam, Ph, Pband, s))

# ---------- official mapping scenarios ----------
print("\n== official-mapped scenarios (Y = X * (1+delta), submission = mean of 3 official repeats) ==")
# observed local->official pairs (hourly/2026-11-06_0700.md)
pairs = [
    ("24/60/4000", 123.13, 150.676),
    ("30/50/5000", 121.83, 140.479),
    ("27/40/4000", 123.41, 141.727),
    ("36/40/4000", 130.32, 133.086),
    ("40/60/4000", 126.75, 137.384),
    ("44/60/4000", 135.67, 142.784),
]
print("observed deltas:")
for tag, l, o in pairs:
    print("  %-12s local=%7.2f official=%7.3f delta=%+6.2f (%+5.1f%%)" %
          (tag, l, o, o - l, (o / l - 1) * 100))

E5_local_exact, _ = exact_min5(champ)
mu10, sg10 = statistics.mean(champ), statistics.stdev(champ)
print("\nchamp10: exact empirical E[min5](local)=%.3f  normal(mu=%.3f, sg=%.3f)" %
      (E5_local_exact, mu10, sg10))

Z1_5 = 1.16296  # E[-min of 5 std normals]
print("\nscenarios: E[official min5] = mu_off - Z*sg_off/sqrt(3);  P(min5<=118), P(107,118]")
hdr = "%-28s %8s %8s %10s %10s %10s" % ("scenario", "mu_off", "sg_off", "E[min5]", "P<=118", "P(107,118]")
print(hdr)
for dname, dl in [("+2.1% (best >=36 group)", 0.021),
                  ("+5.1% (>=36 group mean)", 0.051),
                  ("+8.4% (worst >=36 group)", 0.084),
                  ("delta=0 (perfect bypass)", 0.0)]:
    mu_off = mu10 * (1 + dl)
    for sg_off in (0.3, 1.0, 4.0):
        sg_sub = sg_off / math.sqrt(3)
        E5 = mu_off - Z1_5 * sg_sub
        p118 = 1 - (1 - norm_P(118, mu_off, sg_sub)) ** 5
        pband = ((1 - norm_P(107, mu_off, sg_sub)) ** 5 -
                 (1 - norm_P(118, mu_off, sg_sub)) ** 5)
        print("%-28s %8.3f %8.3f %10.3f %10.2e %10.2e" % (dname, mu_off, sg_sub, E5, p118, pband))
# extreme-optimistic: full local noise transfers to official AND delta=0
sg_sub = sg10 / math.sqrt(1)  # upper bound: no averaging benefit
p118 = 1 - (1 - norm_P(118, mu10, sg_sub)) ** 5
pband = ((1 - norm_P(107, mu10, sg_sub)) ** 5 - (1 - norm_P(118, mu10, sg_sub)) ** 5)
print("%-28s %8.3f %8.3f %10.3f %10.4f %10.4f" %
      ("UB: delta=0, sg=local full", mu10, sg_sub, mu10 - Z1_5 * sg_sub, p118, pband))

# ---------- bootstrap CI ----------
print("\n== bootstrap CI for E[min5] (champ10 empirical, B=20000, seed=2052) ==")
rng = random.Random(2052)
B = 20000
stats = []
for _ in range(B):
    res = [champ[rng.randrange(len(champ))] for _ in range(len(champ))]
    Em, _ = exact_min5(res)
    stats.append(Em)
stats.sort()
lo95, hi95 = stats[int(0.025 * B)], stats[int(0.975 * B)]
print("E[min5] local: point=%.3f  95%% CI=(%.3f, %.3f)" % (E5_local_exact, lo95, hi95))

# ---------- convergence-rate illustration ----------
print("\n== asymptotic dividend |E[min_n]-mu| for standard normal (exact two-sided integral) ==")
for n in (1, 3, 5, 10, 50):
    m = 400000
    hi_b, lo_b = 6.0, -8.0
    step = (hi_b - lo_b) / m
    s = 0.0
    for i in range(m):
        t = lo_b + (i + 0.5) * step
        p = norm_P(t, 0, 1)
        # E[min] = int_0^inf (1-F^n) dt - int_{-inf}^0 F^n dt  (in std-normal units)
        v = (1 - p ** n) if t >= 0 else -p ** n
        s += v * step
    print("  n=%2d  E[min_n]-mu = %+7.4f s" % (n, s))
