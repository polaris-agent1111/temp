# -*- coding: utf-8 -*-
"""
Task 0471: Distributed Asynchronous Alternating Direction Method of Multipliers (ADMM)
- Global consensus formulation for 6-stage QUIC pacing under shallow buffer constraints
- Asynchronous local agent updates with random communication delays
- Target: Primal residual < 1e-5, Dual residual < 1e-5, Convergence rate 100.0%
"""

import sys
import json
import numpy as np

class AsynchronousADMMConsensus:
    def __init__(self, N=6, C_cap=45.0, rho=1.0, seed=42):
        np.random.seed(seed)
        self.N = N
        self.C_cap = C_cap
        self.rho = rho
        
        # Local objective parameters: f_i(x_i) = 0.5 * a_i * (x_i - d_i)^2
        self.a = np.random.uniform(0.5, 2.0, size=N)
        self.d = np.random.uniform(20.0, 50.0, size=N)
        
        # Primal and dual variables
        self.x = np.random.uniform(10.0, 30.0, size=N)
        self.z = np.mean(self.x)
        self.u = np.zeros(N)
        
    def solve_local_x(self, i):
        # min 0.5 * a_i * (x_i - d_i)^2 + u_i * (x_i - z) + 0.5 * rho * (x_i - z)^2
        # FOC: a_i * (x_i - d_i) + u_i + rho * (x_i - z) = 0
        # x_i * (a_i + rho) = a_i * d_i - u_i + rho * z
        return (self.a[i] * self.d[i] - self.u[i] + self.rho * self.z) / (self.a[i] + self.rho)
    
    def solve_global_z(self):
        # z = clip( mean(x_i + u_i / rho), 0, C_cap )
        z_unc = np.mean(self.x + self.u / self.rho)
        return np.clip(z_unc, 0.0, self.C_cap)
    
    def run_optimization(self, max_iter=3000, tol=1e-5):
        for k in range(max_iter):
            # Asynchronous activation: random subset of nodes update
            # At least half the nodes update in any round
            active_nodes = np.random.choice(self.N, size=np.random.randint(self.N // 2, self.N + 1), replace=False)
            for i in active_nodes:
                self.x[i] = self.solve_local_x(i)
                
            z_old = self.z
            self.z = self.solve_global_z()
            
            # Dual update for active nodes
            for i in active_nodes:
                self.u[i] += self.rho * (self.x[i] - self.z)
                
            # Residuals
            r_pri = float(np.linalg.norm(self.x - self.z))
            r_dual = float(self.rho * np.sqrt(self.N) * abs(self.z - z_old))
            
            if r_pri < tol and r_dual < tol:
                return {
                    "converged": True,
                    "iterations": k + 1,
                    "primal_residual": r_pri,
                    "dual_residual": r_dual,
                    "consensus_z": float(self.z)
                }
                
        return {
            "converged": False,
            "iterations": max_iter,
            "primal_residual": r_pri,
            "dual_residual": r_dual,
            "consensus_z": float(self.z)
        }

def main():
    print("=== Task 0471: Distributed Asynchronous ADMM Consensus ===")
    
    runs = 30
    success_count = 0
    pri_residuals = []
    dual_residuals = []
    
    for r in range(runs):
        admm = AsynchronousADMMConsensus(N=6, C_cap=45.0, rho=2.0, seed=100 + r)
        res = admm.run_optimization(max_iter=3000, tol=1e-5)
        pri_residuals.append(res["primal_residual"])
        dual_residuals.append(res["dual_residual"])
        if res["converged"] and (res["primal_residual"] < 1e-5) and (res["dual_residual"] < 1e-5):
            success_count += 1
            
    convergence_rate = (success_count / runs) * 100.0
    max_pri = float(np.max(pri_residuals))
    max_dual = float(np.max(dual_residuals))
    
    passed = (convergence_rate == 100.0) and (max_pri < 1e-5) and (max_dual < 1e-5)
    
    summary = {
        "runs": runs,
        "success_count": success_count,
        "convergence_rate": convergence_rate,
        "max_primal_residual": max_pri,
        "max_dual_residual": max_dual,
        "target_threshold": 1e-5,
        "passed": bool(passed)
    }
    
    print(json.dumps(summary, indent=2))
    if not passed:
        sys.exit(1)

if __name__ == "__main__":
    main()
