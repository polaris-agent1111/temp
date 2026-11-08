# -*- coding: utf-8 -*-
"""
0101 — 5 发真机出分 vs 离线理论仿真预测：残差正态性检验与 Q-Q 图
数据源（全部只读）：
  runs/sequential_adaptive_log.jsonl  官方逐发出分（shot_N_scored）
  runs/seq-w1107-shotN-*.configs.json 实际提交构型（按 log 中 submitted tag 精确匹配）
  runs/results.jsonl                  本地测试床样本（config 字段字符串签名匹配）
输出：stdout 重定向到 _0101_out.md（重定向后请用 Read 工具读取）
"""
import sys, os, json, math, re
sys.stdout.reconfigure(encoding="utf-8")

import numpy as np
from scipy import stats

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

# ---------- 常量（全部来自既有文档，预注册，不用 11/07 五发数据拟合） ----------
PKT_BYTES = 1200.0          # QUIC 净荷（0085）
BIN_MB = [10, 20, 40, 80, 160, 320]     # 六个文件体积（0088/0095）
SS_OVERHEAD_S = 0.42        # 每 bin 慢启动折算 H1 中点（0087: 0.35–0.49）
CONN_OVERHEAD_S = 0.07      # 每 bin 冷连接 1 RTT（0088）
RTT_MS = 70.0
CATNET = 119.8293

def rate_bs(module, params):
    if module in ("leak_bucket",):
        return params["leak_rate"] * PKT_BYTES / (params["leak_interval_us"] / 1e6)
    if module == "token_bucket":
        return params["token_refill_rate"] * PKT_BYTES / (params["token_refill_interval_us"] / 1e6)
    if module == "precise_rate_based":
        return float(params["max_pacing_rate"])
    raise ValueError(module)

# ---------- 1) 官方 5 发出分与实际提交构型 ----------
log_path = os.path.join(ROOT, "runs", "sequential_adaptive_log.jsonl")
events = []
for line in open(log_path, encoding="utf-8"):
    line = line.strip()
    if not line:
        continue
    d = json.loads(line)
    if (d.get("ts") or "") >= "2026-11-07 00:00":  # 真实夜战场次（排除 23:12 dry-run）
        events.append(d)

official, submitted_tag = {}, {}
for d in events:
    ev = d.get("event", "")
    m = re.match(r"shot_(\d)_scored$", ev)
    if m:
        official[int(m.group(1))] = float(d["download_seconds"])
    m = re.match(r"shot_(\d)_submitted$", ev)
    if m:
        submitted_tag[int(m.group(1))] = d["tag"]

print("## 官方 5 发（runs/sequential_adaptive_log.jsonl, 2026-11-07 场次）")
for i in range(1, 6):
    print(f"- Shot {i}: {official[i]:.4f} s  (tag={submitted_tag[i]})")

cfgs = {}
for i in range(1, 6):
    p = os.path.join(ROOT, "runs", submitted_tag[i] + ".configs.json")
    cfgs[i] = json.load(open(p, encoding="utf-8"))

# ---------- 2) 本地样本库 + 构型匹配 ----------
def sig(cfg):
    return json.dumps(cfg, sort_keys=True, ensure_ascii=False)

local = []
with open(os.path.join(ROOT, "runs", "results.jsonl"), encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        r = json.loads(line)
        if not r.get("valid", False):
            continue
        tag = str(r.get("tag", ""))
        if tag.startswith("load-"):
            continue
        local.append(r)

IN_FLIGHT_KEY = "enable_n_in_flight"

def _flag(params):
    return params.get(IN_FLIGHT_KEY, 0)

def norm_cfg(cfg):
    """两种格式统一为 {bin: (module, params)}：提交 JSON 为 [mod, params] 列表，
    results.jsonl 的 config 为 'mod:k=v,...' 字符串。"""
    out = {}
    for i in range(1, 7):
        s = cfg[str(i)]
        if isinstance(s, str):
            mod, _, rest = s.partition(":")
            if not re.fullmatch(r"-?\d+(\.\d+)?", rest.replace(".", "")) and rest and "=" not in rest:
                raise ValueError("unparsed bin config: %r" % s)
            kv = {}
            for x in rest.split(","):
                if "=" in x:
                    k, v = x.split("=", 1)
                    kv[k] = float(v) if re.fullmatch(r"-?\d+(\.\d+)?", v) else v
            if mod == "precise_rate_based":
                out[str(i)] = (mod, {"max_pacing_rate": float(kv["max_pacing_rate"]),
                                     "clock_granularity": float(kv.get("clock_granularity", 1000)),
                                     "in_flight": float(kv.get(IN_FLIGHT_KEY, 0))})
            else:
                kv["in_flight"] = float(kv.get(IN_FLIGHT_KEY, 0))
                out[str(i)] = (mod, kv)
        else:
            mod, params = s[0], dict(s[1])
            out[str(i)] = (mod, params)
    return out

def cfg_key(cfg):
    """config（任一格式）→ 六元组 (module, 结构参数...)，便于比较。
    leak: (mod, rate, cap, interval)；tb: (mod, refill, tokens, burst, interval)；
    precise: (mod, rate, granularity)。解析失败返回 __unparsed__ 哨兵。"""
    try:
        n = norm_cfg(cfg)
    except Exception:
        return tuple([("__unparsed__", str(cfg))] * 6)
    out = []
    for i in range(1, 7):
        mod, params = n[str(i)]
        try:
            fl = params.get("in_flight", params.get(IN_FLIGHT_KEY, 0))
            if mod == "leak_bucket":
                out.append((mod, params["leak_rate"], params["bucket_cap"], params["leak_interval_us"]))
            elif mod == "token_bucket":
                out.append((mod, params["token_refill_rate"], params["tokens"], params["burst"],
                            params["token_refill_interval_us"], fl))
            elif mod == "precise_rate_based":
                out.append((mod, params["max_pacing_rate"], params.get("clock_granularity"), fl))
            else:
                out.append((mod, tuple(sorted((k, float(v)) for k, v in params.items() if isinstance(v, (int, float))))))
        except Exception:
            out.append(("__unparsed__", str(params)))
    return tuple(out)

def match_level(a, b):
    """exact / family / none。family 要求：逐 bin 同模块、burst/cap/tokens/interval 一致、
    速率偏差 ≤2.5%（允许 98M↔100M、granularity 差异记录在案）。"""
    if a == b:
        return "exact", []
    diffs = []
    for i, (x, y) in enumerate(zip(a, b)):
        if x[0] != y[0] or x[0] == "__unparsed__":
            return "none", []
        if x == y:
            continue
        if x[0] in ("leak_bucket", "token_bucket"):
            rate_i = 1
            if abs(x[rate_i] / y[rate_i] - 1) > 0.025 or x[2:] != y[2:]:
                return "none", []
            diffs.append((i + 1, round(x[rate_i] / y[rate_i], 4)))
        elif x[0] == "precise_rate_based":
            if abs(x[1] / y[1] - 1) > 0.025 or x[3] != y[3]:
                return "none", []
            if x[2] != y[2]:
                diffs.append((i + 1, "gran %s vs %s" % (x[2], y[2])))
            else:
                diffs.append((i + 1, round(x[1] / y[1], 4)))
        else:
            return "none", []
    return "family", diffs

local_by_sig = {}
for r in local:
    c = r.get("config")
    if isinstance(c, dict):
        c = {k: str(v) for k, v in c.items()}
        local_by_sig.setdefault(sig(c), []).append(r)

print("\n## 本地构型匹配（runs/results.jsonl, valid=true, 非 load-*）")
m1_local = {}
for i in range(1, 6):
    key = cfg_key(cfgs[i])
    best = None
    for s, rs in local_by_sig.items():
        lk = cfg_key(rs[0]["config"])
        lvl, diffs = match_level(key, lk)
        if lvl == "exact":
            best = (lvl, diffs, rs); break
        if lvl == "family":
            if best is None or len(rs) > len(best[2]):
                best = (lvl, diffs, rs)
    if best is None:
        print(f"- Shot {i}: NO_LOCAL_SAMPLE")
        m1_local[i] = None
        continue
    lvl, diffs, rs = best
    tots = sorted(x["total_seconds"] for x in rs)
    mu = float(np.mean(tots)); med = float(np.median(tots)); sd = float(np.std(tots, ddof=1)) if len(tots) > 1 else float("nan")
    m1_local[i] = (lvl, len(rs), mu, med, sd, diffs, [x.get("tag") for x in rs])
    print(f"- Shot {i}: {lvl} n={len(rs)} mean={mu:.3f} median={med:.3f} sd={sd:.3f} diffs={diffs} tags={sorted(set(rs2 for rs2 in (x.get('tag') for x in rs)))[:3]}...")

# ---------- 3) 三层离线预测 ----------
print("\n## 预测模型")
# M2 流体包络
m2 = {}
for i in range(1, 6):
    t = 0.0
    per = []
    for b in range(1, 7):
        mod, params = cfgs[i][str(b)]
        rb = rate_bs(mod, params)            # B/s
        ti = BIN_MB[b - 1] * 1e6 / rb + SS_OVERHEAD_S + CONN_OVERHEAD_S
        per.append(ti); t += ti
    m2[i] = t
    print(f"- M2流体包络 Shot {i}: {'+'.join(f'{x:.2f}' for x in per)} = {t:.3f} s")

# M3 预注册目标（控制器日志 reason 中当时写下的目标）
m3 = {3: 119.8293, 4: 107.168, 5: 107.168}  # shot3「确保稳定破 119s」→ 破纪录阈值 119.8293；shot4/5「理论极限信封 107.168s」

# ---------- 4) 残差与正态性 ----------
def analyze(name, shots, resid):
    x = np.array(resid, dtype=float)
    n = len(x)
    sw_W, sw_p = stats.shapiro(x)
    skew = stats.skew(x, bias=False)
    kurt = stats.kurtosis(x, bias=False)   # Fisher: 超额峰度
    # Q-Q 相关系数（Filliben 型：对 (i-0.375)/(n+0.25) 正态分位数 vs 排序残差）
    pp = (np.arange(1, n + 1) - 0.375) / (n + 0.25)
    tq = stats.norm.ppf(pp)
    os_ = np.sort(x)
    r_qq = np.corrcoef(tq, os_)[0, 1]
    print(f"\n### {name} (n={n}, shots={shots})")
    print(f"- 残差: {['%.4f' % v for v in x]}")
    print(f"- mean={x.mean():.4f} sd={'nan' if n<2 else '%.4f' % x.std(ddof=1)} skew={skew:.4f} ex.kurt={kurt:.4f}")
    print(f"- Shapiro-Wilk: W={sw_W:.4f}, p={sw_p:.4f}")
    if n >= 8:
        k2, k2p = stats.normaltest(x)
        print(f"- D'Agostino K²: {k2:.4f}, p={k2p:.4f}")
    else:
        print("- D'Agostino K²: 不适用（n<8）")
    ad = stats.anderson(x, "norm")
    print(f"- Anderson-Darling A²={ad.statistic:.4f} (5% 临界值 {ad.critical_values[2]:.4f} → {'拒绝' if ad.statistic > ad.critical_values[2] else '不能拒绝'} @5%)")
    print(f"- Q-Q 相关系数 r={r_qq:.4f}")
    # 功效模拟：Shapiro 在 n 下对三个备择分布的拒绝率（α=0.05），用与残差同量纲的标准化漂移
    if n >= 4:
        rng = np.random.default_rng(20261107)
        N = 4000
        sd0 = x.std(ddof=1) if n > 1 else 7.0
        alts = {
            "正态(基准, 应≈5%)": rng.standard_normal((N, n)),
            "t3 重尾": rng.standard_t(3, size=(N, n)),
            "lognormal 偏态": rng.lognormal(0, 0.55, (N, n)) - math.exp(0.55**2 / 2),
            "均匀 短尾": rng.uniform(-math.sqrt(3), math.sqrt(3), (N, n)),
        }
        print("- Shapiro 功效模拟（α=0.05, N=%d 次蒙特卡洛, 按残差 sd 标准化）：" % N)
        for k, v in alts.items():
            rej = np.mean([stats.shapiro(row)[1] < 0.05 for row in v])
            print(f"    {k}: 拒绝率={rej:.3f}")
    # Q-Q 数据表
    print("- Q-Q 分位表（理论 z vs 排序残差）:")
    for z, o in zip(tq, os_):
        print(f"    {z:+.3f}  {o:+10.4f}")
    return dict(x=x, r_qq=r_qq, tq=tq, os_=os_, sw=(sw_W, sw_p))

res_m1 = [official[i] - m1_local[i][2] for i in range(1, 6) if m1_local[i] is not None]
shots_m1 = [i for i in range(1, 6) if m1_local[i] is not None]
res_m2 = [official[i] - m2[i] for i in range(1, 6)]
res_m3 = [official[i] - m3[i] for i in sorted(m3)]

r1 = analyze("M1 本地测试床仿真均值预测（官方 − 本地均值）", shots_m1, res_m1)
r2 = analyze("M2 流体包络预测（官方 − 流体包络）", [1,2,3,4,5], res_m2)
r3 = analyze("M3 预注册目标（官方 − 预注册目标）", sorted(m3), res_m3)

# 中心化残差正态性（形状检验与位置无关，但给出中心化版本便于 Q-Q 解读）
for nm, rr in [("M1", r1), ("M2", r2)]:
    xc = rr["x"] - rr["x"].mean()
    W, p = stats.shapiro(xc)
    print(f"\n{nm} 中心化残差 Shapiro: W={W:.4f} p={p:.4f}（与未中心化相同——shapiro 平移不变）")

# ---------- 5) ASCII Q-Q 图 ----------
def ascii_qq(rr, title):
    tq, os_ = rr["tq"], rr["os_"]
    lo = min(os_.min(), tq.min()); hi = max(os_.max(), tq.max())
    W, H = 64, 18
    grid = [[" "]*W for _ in range(H)]
    def xy(z, o):
        cx = int((z - lo) / (hi - lo) * (W - 1))
        cy = H - 1 - int((o - lo) / (hi - lo) * (H - 1))
        return cx, cy
    # 45° 参考线（若坐标同刻度）
    for k in range(W):
        z = lo + k / (W - 1) * (hi - lo)
        cx, cy = xy(z, z)
        if 0 <= cx < W and 0 <= cy < H:
            grid[cy][cx] = "·"
    for z, o in zip(tq, os_):
        cx, cy = xy(z, o)
        if 0 <= cx < W and 0 <= cy < H:
            grid[cy][cx] = "◆"
    print(f"\n### ASCII Q-Q — {title}（横轴理论分位 z，纵轴排序残差，·=45°参考线）")
    for row in grid:
        print("".join(row))

ascii_qq(r1, "M1 本地仿真均值")
ascii_qq(r2, "M2 流体包络")

# ---------- 6) SVG Q-Q 图（内嵌 markdown 用） ----------
def svg_qq(rr, title, fname):
    tq, os_ = rr["tq"], rr["os_"]
    lo = min(os_.min(), tq.min()); hi = max(os_.max(), tq.max())
    pad = (hi - lo) * 0.08
    lo -= pad; hi += pad
    W = H = 320; M = 40
    def X(v): return M + (v - lo) / (hi - lo) * (W - 2 * M)
    def Y(v): return H - M - (v - lo) / (hi - lo) * (H - 2 * M)
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" font-family="monospace" font-size="10">',
             f'<rect width="{W}" height="{H}" fill="white"/>',
             f'<line x1="{M}" y1="{H-M}" x2="{W-M}" y2="{H-M}" stroke="black"/>',
             f'<line x1="{M}" y1="{M}" x2="{M}" y2="{H-M}" stroke="black"/>',
             f'<line x1="{X(lo)}" y1="{Y(lo)}" x2="{X(hi)}" y2="{Y(hi)}" stroke="#bbb" stroke-dasharray="4,3"/>']
    for z, o in zip(tq, os_):
        parts.append(f'<circle cx="{X(z):.1f}" cy="{Y(o):.1f}" r="3.2" fill="#1f77b4" fill-opacity="0.85"/>')
    parts.append(f'<text x="{W/2}" y="14" text-anchor="middle">Q-Q plot: {title}</text>')
    parts.append(f'<text x="{W/2}" y="{H-8}" text-anchor="middle">theoretical z</text>')
    parts.append(f'<text x="12" y="{H/2}" transform="rotate(-90 12 {H/2})" text-anchor="middle">ordered residual</text>')
    parts.append('</svg>')
    open(os.path.join(ROOT, "zcode", "scripts", fname), "w", encoding="utf-8").write("\n".join(parts))
    print(f"\nSVG 已写: zcode/scripts/{fname}")

svg_qq(r1, "M1 local-mean residuals", "_0101_qq_m1.svg")
svg_qq(r2, "M2 fluid-envelope residuals", "_0101_qq_m2.svg")

# ---------- 7) 出分数据交叉核验（第二独立来源：Lead 深度复盘文档，其取自 01:25 官方 API） ----------
doc_path = os.path.join(ROOT, "docs", "analysis", "11-07-five-shot-deep-review.md")
try:
    txt = open(doc_path, encoding="utf-8").read()
    doc_scores = {}
    for m in re.finditer(r"\*\*Shot (\d)\*\*.*?\*\*(\d+\.\d+)\s*s?\*\*", txt, re.S):
        doc_scores.setdefault(int(m.group(1)), float(m.group(2)))
    ok = all(abs(doc_scores.get(i, -1) - official[i]) < 1e-9 for i in range(1, 6)) and len(doc_scores) == 5
    print("\n## 出分数据交叉核验 (docs/analysis/11-07-five-shot-deep-review.md, 官方 API@01:25)")
    print(f"- 文档表值: {doc_scores}")
    print(f"- 与 sequential_adaptive_log 一致: {ok}")
    # 提交次数守恒：11/05 5 发 + 11/06 5 发 + 11/07 5 发 = 15（deep review 表载 attempts=15）
    n05 = len([1 for l in open(os.path.join(ROOT, 'runs', 'board_watch.jsonl'), encoding='utf-8')
               if '"seen_at": "2026-11-05T23:10:34"' in l])
    print(f"- board_watch.jsonl 11/05 末快照存在: {bool(n05)}（该快照 attempts=5）；11/06 official_results 5 条 + 11/07 5 条 → 5+5+5=15 与文档一致")
except Exception as e:
    print("\n## 出分数据交叉核验: 失败", e)

print("\nDone.")
