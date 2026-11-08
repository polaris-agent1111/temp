# -*- coding: utf-8 -*-
"""0094 — 11/08 阶段二后续 5 发提交构型的先验决策矩阵与多步贝叶斯推演.

数据链（全部只读）：
  - runs/results.jsonl：候选构型本地样本（valid=true 且非 load-*）；
  - 0084 分层贝叶斯校准：官方单发 = θ_c + Δ，Δ = μ_B + b_day + ε_d，
    μ_B=+2.49 (95%CI −5.1~+9.5 → sd 3.7)、τ_b=4.51、σ_d=7.02；
  - 官方锚点：光明未来 117.0257（第1）、hashkimi 120.2670（第3线）、我方 124.3683（Shot 2）。

模型：
  θ_c 先验 = 本地样本的 t 后验（Jeffreys：θ|y ~ t_{n-1}(ȳ, s²/n)）；
  单发预测 sd = sqrt(s²/n + u_B² + τ_b² + σ_d²)；
  世界采样：μ_B ~ N(μ_B0, 3.7²)，b ~ N(0, 4.51²)，θ_c ~ 本地后验；
  出分 S = θ_c + μ_B + b + N(0, σ_d²)；发后共轭更新 θ_c（Δ̂ 以 μ_B0 代入， disclosed 近似）。

策略（每策略 5 发，串行）：
  A_lead     ：pert → crown → micro → 分支(platform|crown_pert40on2) → 重复当日最好构型
  B_crown3   ：crown ×3 → pert → 重复当日最好构型
  C_platform ：platform ×2 → crown ×2 → 重复当日最好构型
  D_thompson ：按当前后验 argmax P(S<T) 选 4 发 → 重复当日最好构型
  E_explore  ：pert/crown/micro/platform/crown_pert40on2 各 1 发
"""
import math
import json
import numpy as np

rng = np.random.default_rng(42)

# ---------- 常量（0084/官方锚点） ----------
MU_B0 = 2.49
U_B = 3.7          # μ_B 不确定度（0084 CI 半宽/1.96）
TAU_B = 4.51       # 跨日漂移
SIGMA_D = 7.02     # 官方单发噪声
T1 = 117.0257      # 光明未来（第1）
T3 = 120.2670      # hashkimi（第3线）
T_US = 124.3683    # 我方现最好（Shot 2）

# ---------- 本地样本（只读 runs/results.jsonl） ----------
def load_stats():
    recs = [json.loads(l) for l in open('runs/results.jsonl', encoding='utf-8') if l.strip()]
    tags = {
        'crown':    'test-leak-asym-41x2-40-37-36x2',
        'pert':     'test-anchor-shot2-pert-40x3-37-36-36',
        'platform': 'test-leak-asym-40-40-37-37',
        'crown40':  'test-crown-pert-40on2',
        'anchor':   'test-anchor-shot2-leak-40x3-36x3',
        'micro':    'test-leak-asym-41x2-40x2-36x2',
        'asym4140': 'test-leak-asym-41-40-37-36',
        'flash38':  'test-leak-asym-40-40-38-36',
    }
    out = {}
    for k, tag in tags.items():
        s = [r['total_seconds'] for r in recs
             if r.get('tag', '').startswith(tag) and r.get('valid') and 'load-' not in r.get('tag', '')]
        a = np.array(s)
        out[k] = dict(n=len(a), mean=float(a.mean()), sd=float(a.std(ddof=1)) if len(a) > 1 else 0.0,
                      med=float(np.median(a)), tag=tag)
    return out

STATS = load_stats()


def sample_theta(stats, n_draw):
    """Jeffreys t 后验采样：θ|y ~ ȳ + (s/√n)·t_{n-1}。"""
    n = stats['n']
    if n == 0:
        raise ValueError('NO_LOCAL_SAMPLE')
    t = rng.standard_t(df=max(n - 1, 1), size=n_draw)
    return stats['mean'] + stats['sd'] / math.sqrt(n) * t


CFG_ORDER = ['crown', 'pert', 'micro', 'platform', 'crown40', 'anchor', 'asym4140', 'flash38']
# 策略池：剔除门禁旗标构型（flash38 n=2 LOW_N+HIGH_CV，且 t 后验 df=1 无限方差不入策略）
POOL = ['crown', 'pert', 'micro', 'platform', 'crown40', 'anchor', 'asym4140']
CN = {'crown': '皇冠 41x2-40-37-36x2', 'pert': '稳健 40x3-37-36-36',
      'micro': '微攻 41x2-40x2-36x2', 'platform': '平台 40-40-37-37',
      'crown40': '冠扰 40on2', 'anchor': 'Shot2 锚 40x3-36x3',
      'asym4140': 'asym 41-40-37-36', 'flash38': '闪点 40-40-38-36[门禁禁]'}


def predictive(stats, mu_b=MU_B0):
    se = stats['sd'] / math.sqrt(max(stats['n'], 1))
    tot = math.sqrt(se ** 2 + U_B ** 2 + TAU_B ** 2 + SIGMA_D ** 2)
    m = stats['mean'] + mu_b
    phi = lambda x: 0.5 * (1 + math.erf(x / math.sqrt(2)))
    return m, tot, phi((T1 - m) / tot), phi((T3 - m) / tot), phi((T_US - m) / tot)


def run_world(policy, mu_b0=MU_B0, n_worlds=30000):
    """返回 day-best 数组（策略池 = POOL，已剔除门禁禁投构型）。"""
    means = np.array([STATS[c]['mean'] for c in POOL])
    sds = np.array([STATS[c]['sd'] for c in POOL])
    ns = np.array([STATS[c]['n'] for c in POOL])
    bests = np.empty(n_worlds)
    for w in range(n_worlds):
        mu_b = rng.normal(mu_b0, U_B)
        b = rng.normal(0, TAU_B)
        theta = means + sds / np.sqrt(ns) * rng.standard_t(np.maximum(ns - 1, 1))
        # 共轭后验（m, v）初始 = 本地采样后验（正态近似）
        m = means.copy()
        v = (sds ** 2) / ns
        delta_hat = mu_b0
        scores = np.full(5, np.nan)
        chosen = []
        obs_best_cfg = None
        obs_best_val = np.inf
        for i in range(5):
            c_idx = policy(i, m, v, scores, chosen, obs_best_cfg, theta, mu_b + b)
            s = theta[c_idx] + mu_b + b + rng.normal(0, SIGMA_D)
            scores[i] = s
            chosen.append(c_idx)
            if s < obs_best_val:
                obs_best_val = s
                obs_best_cfg = c_idx
            # 共轭更新 θ_c（把 S−Δ̂ 当似然观测）：v' = 1/(1/v+1/σ²)，m' = v'(m/v + (S−Δ̂)/σ²)
            v_old = v[c_idx]
            prec = 1 / v_old + 1 / SIGMA_D ** 2
            v_new = 1 / prec
            m_new = v_new * (m[c_idx] / v_old + (s - delta_hat) / SIGMA_D ** 2)
            v[c_idx] = v_new
            m[c_idx] = m_new
        bests[w] = np.nanmin(scores)
    return bests


def pol_lead(i, m, v, scores, chosen, obs_best_cfg, theta, day_shift):
    if i == 0: return POOL.index('pert')
    if i == 1: return POOL.index('crown')
    if i == 2: return POOL.index('micro')
    if i == 3:
        done = scores[:3]
        # 分支 A 的 40x3-38-37-36 无本地样本（NO_LOCAL_SAMPLE，门禁禁止）→ 以已测构型替代
        return POOL.index('platform') if np.nanmin(done) > 126 else POOL.index('crown40')
    return obs_best_cfg


def pol_crown3(i, m, v, scores, chosen, obs_best_cfg, theta, day_shift):
    if i < 3: return POOL.index('crown')
    if i == 3: return POOL.index('pert')
    return obs_best_cfg


def pol_platform(i, m, v, scores, chosen, obs_best_cfg, theta, day_shift):
    if i < 2: return POOL.index('platform')
    if i < 4: return POOL.index('crown')
    return obs_best_cfg


def pol_thompson(i, m, v, scores, chosen, obs_best_cfg, theta, day_shift):
    if i < 4:
        phi = lambda x: 0.5 * (1 + math.erf(x / math.sqrt(2)))
        p = [phi((T1 - (m[k] + MU_B0)) / math.sqrt(v[k] + SIGMA_D ** 2)) for k in range(len(POOL))]
        return int(np.argmax(p))
    return obs_best_cfg


def pol_explore(i, m, v, scores, chosen, obs_best_cfg, theta, day_shift):
    seq = ['pert', 'crown', 'micro', 'platform', 'crown40']
    return POOL.index(seq[i])


POLICIES = {
    'A_lead(定稿序列·分支替换)': pol_lead,
    'B_crown3(皇冠×3冲刺)': pol_crown3,
    'C_platform(平台打底)': pol_platform,
    'D_thompson(后验贪心)': pol_thompson,
    'E_explore(五构型等额)': pol_explore,
}


def main():
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    out = []
    out.append('=== 0094 先验决策矩阵与多步贝叶斯推演（seed=42, 30000 worlds）===')
    out.append(f'锚点: 第1={T1}(光明未来) 第3线={T3}(hashkimi) 我方={T_US}(Shot2)')
    out.append(f'校准(0084): μ_B={MU_B0}±{U_B} τ_b={TAU_B} σ_d={SIGMA_D}')
    out.append('')

    out.append('--- 1. 本地候选池（results.jsonl 全量重算，valid & 非 load-*） ---')
    out.append(f"{'构型':<24}{'tag':<40}{'n':>3}{'均值':>9}{'sd':>7}{'中位':>9}")
    for k in CFG_ORDER:
        s = STATS[k]
        out.append(f"{CN[k]:<24}{s['tag']:<40}{s['n']:>3}{s['mean']:>9.2f}{s['sd']:>7.2f}{s['med']:>9.2f}")
    out.append('门禁旗：flash38 n=2 LOW_N+HIGH_CV；asym4140 min 117.23 与均值差 19.4s(MIN_FAR_BELOW_MEAN 风险)；')
    out.append('        分支A「40x3-38-37-36」无本地样本(NO_LOCAL_SAMPLE)，策略中已用 platform/crown40 替代。')
    out.append('')

    out.append('--- 2. 先验决策矩阵：单发预测（基准校准 μ_B=+2.49） ---')
    out.append(f"{'构型':<24}{'官方预测均值':>12}{'预测sd':>8}{'P(<117.03)':>11}{'P(<120.27)':>11}{'P(<124.37)':>11}")
    for k in CFG_ORDER:
        m, t, p1, p3, pu = predictive(STATS[k])
        out.append(f'{CN[k]:<24}{m:>12.1f}{t:>8.1f}{p1*100:>10.2f}%{p3*100:>10.2f}%{pu*100:>10.2f}%')
    out.append('')

    out.append('--- 3. Shot2 锚点的官方信息更新（anchor 构型以官方 124.3683 作为一次观测回灌） ---')
    a = STATS['anchor']
    se2 = a['sd'] ** 2 / a['n']
    prec = 1 / se2 + 1 / (U_B ** 2 + SIGMA_D ** 2)
    v_post = 1 / prec
    m_post = v_post * (a['mean'] / se2 + (T_US - MU_B0) / (U_B ** 2 + SIGMA_D ** 2))
    tot = math.sqrt(v_post + U_B ** 2 + TAU_B ** 2 + SIGMA_D ** 2)
    phi = lambda x: 0.5 * (1 + math.erf(x / math.sqrt(2)))
    out.append(f'anchor θ 后验: {m_post:.1f}±{math.sqrt(v_post):.1f}（本地先验 {a["mean"]:.1f}±{a["sd"]/math.sqrt(a["n"]):.1f}）')
    out.append(f'11/08 再投 anchor 的单发预测: {m_post+MU_B0:.1f}±{tot:.1f}')
    out.append(f'P(复现 <124.37)={phi((T_US-(m_post+MU_B0))/tot)*100:.1f}%  P(<117.03)={phi((T1-(m_post+MU_B0))/tot)*100:.2f}%')
    out.append('解读：124.3683 是该构型预测分布的 −1σ 抽签，重复投稿大概率回归 128–136 区间。')
    out.append('')

    out.append('--- 4. 多步贝叶斯推演：5 发策略比较（基准校准，day-best 口径） ---')
    out.append(f"{'策略':<28}{'E[best]':>9}{'P(best<T1)':>11}{'P(best<T3)':>11}{'P(best<T我方)':>13}"
               f"{'P5':>8}{'P50':>8}{'P95':>8}")
    res = {}
    for name, pol in POLICIES.items():
        b = run_world(pol)
        res[name] = b
        out.append(f'{name:<28}{b.mean():>9.1f}{(b<T1).mean()*100:>10.2f}%{(b<T3).mean()*100:>10.2f}%'
                   f'{(b<T_US).mean()*100:>12.2f}%{np.percentile(b,5):>8.1f}{np.percentile(b,50):>8.1f}'
                   f'{np.percentile(b,95):>8.1f}')
    out.append('')

    out.append('--- 5. 校准面稳健性：P(day-best < 117.03) 在四种 μ_B 场景下 ---')
    out.append(f"{'策略':<28}{'μ_B=+2.5(0084)':>14}{'μ_B=0':>10}{'μ_B=+4.7(历史对)':>16}{'μ_B=−13.4(中位图)':>18}")
    for name, pol in POLICIES.items():
        row = []
        for mu in (2.49, 0.0, 4.7, -13.39):
            b = run_world(pol, mu_b0=mu, n_worlds=8000)
            row.append((b < T1).mean() * 100)
        out.append(f'{name:<28}{row[0]:>13.2f}%{row[1]:>9.2f}%{row[2]:>15.2f}%{row[3]:>17.2f}%')
    out.append('')

    out.append('--- 5b. 零排名对照：所有构型真 θ 设为池均值（检验 D 的优势来源） ---')
    pool_mean = float(np.mean([STATS[c]['mean'] for c in POOL]))
    saved_means = {c: STATS[c]['mean'] for c in POOL}
    for c in POOL:
        STATS[c]['mean'] = pool_mean
    for name in ('A_lead(定稿序列·分支替换)', 'D_thompson(后验贪心)', 'E_explore(五构型等额)'):
        b = run_world(POLICIES[name], n_worlds=8000)
        out.append(f'{name:<28} 零排名下 E[best]={b.mean():.1f}  P(best<T1)={(b<T1).mean()*100:.2f}%')
    for c in POOL:
        STATS[c]['mean'] = saved_means[c]
    out.append('解读：零排名下各策略应收敛到同一水平——与 §4 的差距即「构型排名信息」的贡献；')
    out.append('      0091 证明 n≈10 的本地排名在 <10s 差异上不可分辨，故该优势需打折看待。')
    out.append('')

    out.append('--- 6. 阈值敏感性（对手 11/08 也可能进步；基准校准, 策略 A/B） ---')
    out.append(f"{'阈值 T':>8}{'A_lead P(best<T)':>18}{'B_crown3 P(best<T)':>20}")
    for T in (115.0, 117.0257, 119.0, 120.2670, 122.0):
        bA, bB = res['A_lead(定稿序列·分支替换)'], res['B_crown3(皇冠×3冲刺)']
        out.append(f'{T:>8.2f}{(bA<T).mean()*100:>17.2f}%{(bB<T).mean()*100:>19.2f}%')
    out.append('')

    out.append('--- 7. 校准图的分歧桥接（为何 116.5s 是乐观读数） ---')
    out.append('Shot2 对: 官方 124.37 vs 本地均值 134.53(n=5)/中位 137.76。')
    out.append('  均值图(0084): 预测官方 = 134.53+2.49 = 137.0±8.9 → 实测 124.37 为 −1.42σ（15 发里 1 个 −1.4σ 外点，正常）。')
    out.append('  中位图(hourly): 官方≈本地中位−13.4 → 该图由单发 −1.4σ 外点外推，隐含把运气当中心。')
    out.append(f'  皇冠构型中心预期(均值图) = {STATS["crown"]["mean"]+MU_B0:.1f}±'
              f'{math.sqrt(STATS["crown"]["sd"]**2/STATS["crown"]["n"]+U_B**2+TAU_B**2+SIGMA_D**2):.1f}s；')
    out.append('  「官方预期 116.5s」= 中位图读数，仅在与 Shot2 同等运气(−1.4σ)时成立。')
    print('\n'.join(out))


if __name__ == '__main__':
    main()
