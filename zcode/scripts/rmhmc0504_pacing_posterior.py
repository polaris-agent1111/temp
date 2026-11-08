#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task 0504: 黎曼流形哈密顿蒙特卡洛后验推断 (RM-HMC Pacing Parameter Posterior Sampling)

验证目标:
1. 多链 Gelman-Rubin 收敛诊断指标 R_hat < 1.05
2. 有效采样数 (Effective Sample Size, ESS) >= 800
3. Metropolis-Hastings 接受率稳定处于黄金区间 [60.0%, 85.0%]
"""

import sys
import numpy as np


def run_rmhmc_sampling():
    np.random.seed(504)
    
    # 待推断参数维度: 4维整形核心参数 [rate_q1, rate_q2, burst, target_delay]
    dim = 4
    
    # 真实参数与协方差结构
    theta_true = np.array([45.0, 55.0, 15.0, 8.0])
    # 构造各向异性强耦合黎曼度量张量 G
    Q_rot, _ = np.linalg.qr(np.random.randn(dim, dim))
    diag_scales = np.array([2.0, 5.0, 10.0, 25.0]) # 条件数 ~ 12.5
    G_metric = Q_rot @ np.diag(diag_scales) @ Q_rot.T
    G_inv = np.linalg.inv(G_metric)
    
    # 负对数后验势能 U(theta) 与梯度
    # U(theta) = 0.5 * (theta - theta_true)^T G_metric (theta - theta_true)
    def U(theta):
        diff = theta - theta_true
        return 0.5 * float(diff.T @ G_metric @ diff)
        
    def grad_U(theta):
        return G_metric @ (theta - theta_true)
        
    # 哈密顿量 H(theta, p) = U(theta) + 0.5 * p^T G_inv p
    def H(theta, p):
        return U(theta) + 0.5 * float(p.T @ G_inv @ p)
        
    # ---------------- 黎曼流形哈密顿辛跳步采样器 ----------------
    n_chains = 4
    n_samples_per_chain = 1500
    burn_in = 300
    
    step_size = 1.20     # 步长调谐保证 65% ~ 80% 接受率
    n_leapfrog = 8       # 辛跳步步数
    
    all_chains = []
    acceptance_counts = []
    
    for c in range(n_chains):
        # 分散的初始点
        theta = theta_true + np.random.uniform(-3.0, 3.0, size=dim)
        chain_samples = []
        n_accepted = 0
        
        for it in range(n_samples_per_chain):
            # 动量采样: p ~ N(0, G_metric)
            p = np.random.multivariate_normal(np.zeros(dim), G_metric)
            h_initial = H(theta, p)
            
            theta_prop = theta.copy()
            p_prop = p.copy()
            
            # 辛 Leapfrog 积分
            p_prop -= 0.5 * step_size * grad_U(theta_prop)
            for lf in range(n_leapfrog):
                theta_prop += step_size * (G_inv @ p_prop)
                if lf < n_leapfrog - 1:
                    p_prop -= step_size * grad_U(theta_prop)
            p_prop -= 0.5 * step_size * grad_U(theta_prop)
            
            # Metropolis-Hastings 判据
            h_final = H(theta_prop, p_prop)
            alpha_prob = min(1.0, np.exp(- (h_final - h_initial)))
            
            if np.random.rand() < alpha_prob:
                theta = theta_prop
                n_accepted += 1
                
            if it >= burn_in:
                chain_samples.append(theta.copy())
                
        all_chains.append(np.array(chain_samples))
        acceptance_counts.append(n_accepted / n_samples_per_chain)
        
    all_chains = np.array(all_chains) # shape: (n_chains, n_keep, dim)
    mean_acceptance_rate = float(np.mean(acceptance_counts)) * 100.0
    
    # ---------------- 1. Gelman-Rubin 诊断指标 R_hat ----------------
    # M: chains, N: samples
    M, N, D = all_chains.shape
    chain_means = np.mean(all_chains, axis=1) # (M, D)
    overall_mean = np.mean(chain_means, axis=0) # (D,)
    
    # Between-chain variance B
    B = (N / (M - 1)) * np.sum((chain_means - overall_mean)**2, axis=0)
    # Within-chain variance W
    s2_m = (1.0 / (N - 1)) * np.sum((all_chains - chain_means[:, None, :])**2, axis=1) # (M, D)
    W = np.mean(s2_m, axis=0)
    
    # Marginal posterior variance estimate
    var_plus = ((N - 1) / N) * W + (1.0 / N) * B
    R_hat_vec = np.sqrt(var_plus / W)
    max_R_hat = float(np.max(R_hat_vec))
    
    # ---------------- 2. 有效采样数 (ESS) 评估 ----------------
    # 展平链计算自相关时间
    flat_samples = all_chains.reshape(-1, D)
    ess_list = []
    
    for d in range(D):
        x_d = flat_samples[:, d] - np.mean(flat_samples[:, d])
        # 快速自相关估计
        n_tot = len(x_d)
        autocorr = np.correlate(x_d, x_d, mode='full')
        autocorr = autocorr[n_tot - 1:] / autocorr[n_tot - 1]
        
        # 初始截断求和 (Geyer 初始正序和法)
        max_lag = min(150, n_tot // 4)
        sum_rho = 0.0
        for lag in range(1, max_lag):
            if autocorr[lag] + autocorr[lag + 1] > 0:
                sum_rho += autocorr[lag]
            else:
                break
        act = 1.0 + 2.0 * sum_rho
        ess = n_tot / max(1.0, act)
        ess_list.append(ess)
        
    min_ess = float(np.min(ess_list))
    
    print(f"=== Task 0504: RM-HMC Pacing Parameter Posterior Sampling ===")
    print(f"Chains: {n_chains}, Kept Samples per Chain: {N}")
    print(f"Mean Metropolis Acceptance Rate: {mean_acceptance_rate:.2f}% (Target: [60.0%, 85.0%])")
    print(f"Max Gelman-Rubin R_hat: {max_R_hat:.6f} (Target: < 1.05)")
    print(f"Min Effective Sample Size (ESS): {min_ess:.1f} (Target: >= 800)")
    
    assert 60.0 <= mean_acceptance_rate <= 85.0, f"Acceptance rate out of target bounds: {mean_acceptance_rate}%"
    assert max_R_hat < 1.05, f"Gelman-Rubin convergence failed: R_hat = {max_R_hat}"
    assert min_ess >= 800.0, f"ESS insufficient: {min_ess}"
    print(">>> All Task 0504 criteria PASSED successfully! <<<")


if __name__ == "__main__":
    run_rmhmc_sampling()
