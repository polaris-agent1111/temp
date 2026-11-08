# -*- coding: utf-8 -*-
"""
Task 0375 v2 补充验证：逃逸时间下界的严格界 vs 经验 CDF
- 严格界（反射原理/Doob）：对线性化不稳定方向 y_s = y0·e^{|λ|s} + M_s，
  M_s 为中心化高斯鞅，Var[M_t] = v(t) = (β⁻¹/|λ|)(e^{2|λ|t}−1)。
  若 ε·e^{|λ|t} < R/2，则 τ_R < t 要求 sup_{s≤t}|M_s| ≥ R/2 =: a，
  由 DDS 时间变换 + 反射原理：P(sup_{s≤t} M_s ≥ a) = 2(1−Φ(a/√v(t)))，
  双侧 ≤ 4(1−Φ(a/√v(t)))。
- 该界给出收敛时间下界：逃逸概率要在时刻 t 达到 1−δ，必须
  t ≥ (1/(2|λ|))·ln(1 + δ·R²·|λ|/(8β⁻¹))（由 Doob 版本导出，同阶）。
- 与 1,000 条种子固定轨迹的经验逃逸 CDF 对照（复用主脚本的种子与仿真）。
"""
import math
import sys
import os

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from langevin0375_saddle_escape_dynamics import simulate_langevin_trajectory  # noqa: E402

import numpy as np  # noqa: E402


def phi_tail(x):
    """1 - Φ(x), 正态尾部。"""
    return 0.5 * math.erfc(x / math.sqrt(2.0))


def main():
    lam = math.sqrt(1.04)  # 鞍点海森负特征值绝对值: H=[[-1,-0.2],[-0.2,1]] → λ=±√1.04
    beta_inv = 0.08
    R = 0.6
    eps = 5.0 * 1e-4  # 初始扰动 ~ N(0,1e-4²) 的 5σ 包络

    print("=== 0375 v2 逃逸时间下界验证 ===")
    print(f"|λ|={lam:.4f}, β⁻¹={beta_inv}, R={R}, ε={eps:.1e}")

    # 复现主仿真的轨迹集合（同种子 20261108、同初始分布、同积分参数）
    np.random.seed(20261108)
    N = 1000
    dt, steps = 0.01, 800
    escape_times = []
    for _ in range(N):
        init = np.random.normal(0.0, 1e-4, size=2)
        escaped, step, _ = simulate_langevin_trajectory(init)
        if escaped:
            escape_times.append((step + 1) * dt)
    escape_times = np.array(sorted(escape_times))

    print("\n t     P(τ<t) 理论上界   经验 P(τ<t)   界有效?")
    for t in (0.1, 0.2, 0.3, 0.5, 0.8, 1.0):
        v = (beta_inv / lam) * (math.exp(2 * lam * t) - 1)
        drift_ok = eps * math.exp(lam * t) < R / 2
        bound = 4.0 * phi_tail((R / 2) / math.sqrt(v)) if drift_ok else float("nan")
        emp = float(np.mean(escape_times < t))
        ok = drift_ok and bound < 1.0
        print(f" {t:.2f}   {bound:10.4f}      {emp:8.4f}     {'有效' if ok else ' vacuous/不适用'}")
        assert not ok or emp <= bound + 1e-9, f"经验 CDF 超出理论上界于 t={t}"

    # 收敛时间下界（达到逃逸概率 1−δ 所需最短时间）
    for delta in (0.5, 0.9, 0.99):
        t_min = (1.0 / (2 * lam)) * math.log(1.0 + delta * R * R * lam / (8 * beta_inv))
        emp_frac = float(np.mean(escape_times < t_min))
        print(f"P(τ<t_min)≥{delta:.2f} 需要 t_min ≥ {t_min:.4f}（经验占比 {emp_frac:.3f}，应 ≤ {delta:.2f}）")
        assert emp_frac <= delta + 1e-9

    print("\n[PASS] 经验逃逸 CDF 全部落在严格下界保证的范围之内（收敛时间下界成立）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
