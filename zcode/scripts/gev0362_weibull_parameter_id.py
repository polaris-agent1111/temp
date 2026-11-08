# -*- coding: utf-8 -*-
"""
0362: 极值分布威布尔吸引域精确参数辨识
Generalized Extreme Value (GEV) Weibull Domain of Attraction & Bounded Support Identification
"""
import numpy as np
import json
from pathlib import Path
from scipy.stats import genextreme

def main():
    np.random.seed(362)
    
    # 模拟 10,000 组极小值观测样本 (对应多轮流量整形的极限低分)
    true_bound = 114.85 # s 物理瓶颈理论下确界
    raw_samples = true_bound + np.random.weibull(a=2.2, size=10000) * 1.80
    
    # 根据 Fisher-Tippett-Gnedenko 定理:
    # 极小值分布 min(X) = -max(-X)
    # 对 -X 进行 GEV 拟合
    c_fit, loc_fit, scale_fit = genextreme.fit(-raw_samples)
    xi_evt = float(-c_fit) # 标准 EVT 形状参数定义: xi = -c < 0 代表威布尔吸引域 (有限支撑集)
    
    # 计算估计的物理极值下界
    # -X 的上确界为 loc + scale / c (若 c > 0)
    # 故 X 的物理下确界为 -(loc + scale / c)
    est_upper_neg = loc_fit + scale_fit / c_fit if c_fit > 0 else np.max(-raw_samples)
    estimated_lower_bound = float(-est_upper_neg)
    
    bound_error = float(abs(estimated_lower_bound - true_bound))
    
    print(f"Fitted Scipy Shape c:      {c_fit:.4f}")
    print(f"EVT Shape Parameter xi:    {xi_evt:.4f} (Gate: xi < 0)")
    print(f"True Physical Lower Bound: {true_bound:.4f} s")
    print(f"Estimated Lower Bound:     {estimated_lower_bound:.4f} s")
    print(f"Lower Bound Error:         {bound_error:.4f} s (Gate: <= 0.5 s)")
    
    assert xi_evt < 0.0, f"EVT shape xi {xi_evt:.4f} not negative"
    assert bound_error <= 0.50, f"Bound error {bound_error:.4f}s above 0.5s"
    
    result = {
        "status": "PASS",
        "xi_evt": xi_evt,
        "scipy_c": float(c_fit),
        "loc": float(loc_fit),
        "scale": float(scale_fit),
        "estimated_lower_bound": estimated_lower_bound,
        "true_bound": true_bound,
        "bound_error": bound_error
    }
    
    out_path = Path("zcode/reports/0362_result.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print("SUCCESS: 0362 verification completed.")

if __name__ == "__main__":
    main()
