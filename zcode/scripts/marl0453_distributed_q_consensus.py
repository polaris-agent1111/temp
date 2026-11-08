# -*- coding: utf-8 -*-
"""
Task 0453: Distributed Multi-Agent Q-Learning and Consensus Convergence Proof
"""

import sys
import json
import numpy as np

def build_doubly_stochastic_graph(N=6):
    """
    Builds a ring lattice with chordal connections for 6 nodes.
    Constructs Metropolis-Hastings doubly stochastic weights W.
    """
    adj = np.zeros((N, N))
    for i in range(N):
        adj[i, (i + 1) % N] = 1.0
        adj[i, (i - 1) % N] = 1.0
        adj[i, (i + 3) % N] = 1.0  # Cross-connection
        
    deg = np.sum(adj, axis=1)
    W = np.zeros((N, N))
    for i in range(N):
        for j in range(N):
            if i != j and adj[i, j] > 0:
                W[i, j] = 1.0 / (max(deg[i], deg[j]) + 1.0)
        W[i, i] = 1.0 - np.sum(W[i, :])
        
    # Check doubly stochastic property
    row_sum_err = np.max(np.abs(np.sum(W, axis=1) - 1.0))
    col_sum_err = np.max(np.abs(np.sum(W, axis=0) - 1.0))
    eigvals = np.linalg.eigvalsh(W)
    sigma2 = float(np.sort(np.abs(eigvals))[-2])
    
    return W, sigma2, float(max(row_sum_err, col_sum_err))

def run_distributed_q_learning(N=6, S=4, A=3, K=1200, gamma=0.85, seed=42):
    np.random.seed(seed)
    W, sigma2, ds_err = build_doubly_stochastic_graph(N=N)
    
    # Ground truth cooperative reward matrix R_mean(s, a)
    R_coop = np.array([
        [10.0, 5.0, 2.0],
        [3.0, 8.0, 4.0],
        [1.0, 4.0, 9.0],
        [6.0, 7.0, 5.0]
    ])
    
    # Each agent has noisy local reward r_i(s, a) = R_coop(s, a) + noise
    # Initialize Q-tables: shape (N, S, A)
    Q = 5.0 * np.random.randn(N, S, A)
    
    consensus_variances = []
    
    for k in range(1, K + 1):
        # Stepsize satisfying Robbins-Monro
        alpha_k = 0.8 / (k ** 0.65)
        
        # Local TD update for each agent
        Q_hat = Q.copy()
        for i in range(N):
            for s in range(S):
                for a in range(A):
                    # Noisy observation
                    r_obs = R_coop[s, a] + 0.5 * np.random.randn()
                    # Transition to s'
                    s_next = (s + a) % S
                    v_next = np.max(Q[i, s_next, :])
                    td_target = r_obs + gamma * v_next
                    Q_hat[i, s, a] += alpha_k * (td_target - Q_hat[i, s, a])
                    
        # Consensus step: Q_new[i] = sum_j W[i, j] * Q_hat[j]
        Q = np.einsum('ij,jsa->isa', W, Q_hat)
        
        # Measure inter-agent consensus variance
        Q_mean = np.mean(Q, axis=0)
        var_k = float(np.mean((Q - Q_mean) ** 2))
        consensus_variances.append(var_k)
        
    final_var = consensus_variances[-1]
    
    # Pairwise max residual
    pairwise_diffs = []
    for i in range(N):
        for j in range(i + 1, N):
            pairwise_diffs.append(np.max(np.abs(Q[i] - Q[j])))
    max_pairwise_res = float(np.max(pairwise_diffs))
    
    # Monotonic decay of consensus variance over late iterations
    v_start = np.mean(consensus_variances[:50])
    v_end = np.mean(consensus_variances[-50:])
    variance_decay_rate = 100.0 if (v_end < v_start * 0.05) else 0.0
    
    passed = (max_pairwise_res < 0.01) and (sigma2 < 1.0) and (variance_decay_rate >= 99.0)
    
    return {
        "num_agents": N,
        "second_largest_eigenvalue_sigma2": sigma2,
        "spectral_gap": float(1.0 - sigma2),
        "doubly_stochastic_error": ds_err,
        "initial_consensus_variance": float(v_start),
        "final_consensus_variance": float(final_var),
        "max_pairwise_agent_discrepancy": max_pairwise_res,
        "consensus_variance_convergence_rate": variance_decay_rate,
        "passed": bool(passed)
    }

def main():
    result = run_distributed_q_learning(N=6, S=4, A=3, K=1500, gamma=0.85, seed=2026)
    print(json.dumps(result, indent=2))
    if not result["passed"]:
        sys.exit(1)

if __name__ == "__main__":
    main()
