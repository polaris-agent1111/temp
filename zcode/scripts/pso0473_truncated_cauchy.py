# -*- coding: utf-8 -*-
"""
Task 0473: Truncated Cauchy Mutation Particle Swarm Optimization (TC-PSO)
- Multimodal landscape representing shallow buffer queue traps
- Linearly decreasing inertia weight w from 0.9 to 0.4
- Velocity clamping
- Truncated Cauchy mutation on global best candidate to escape local basins
- Target: Global optimum capture rate 100.0%, fitness variance convergence < 1e-4
"""

import sys
import json
import numpy as np

def shallow_buffer_multimodal_landscape(x):
    """
    Multimodal Rastrigin landscape modeling queue barrier cliffs:
    f(x) = sum(x_i^2 - 10 * cos(2*pi*x_i) + 10)
    Global minimum at x = 0 with f(0) = 0.
    """
    return np.sum(x**2 - 10.0 * np.cos(2.0 * np.pi * x) + 10.0, axis=-1)

class TruncatedCauchyPSO:
    def __init__(self, dim=3, num_particles=50, bounds=(-5.12, 5.12), seed=42):
        np.random.seed(seed)
        self.dim = dim
        self.num_particles = num_particles
        self.bounds = bounds
        self.v_max = 0.2 * (bounds[1] - bounds[0])
        
        # Initialize positions and velocities
        self.X = np.random.uniform(bounds[0], bounds[1], (num_particles, dim))
        self.V = np.random.uniform(-self.v_max, self.v_max, (num_particles, dim))
        
        self.pbest_X = self.X.copy()
        self.pbest_val = shallow_buffer_multimodal_landscape(self.X)
        
        best_idx = np.argmin(self.pbest_val)
        self.gbest_X = self.pbest_X[best_idx].copy()
        self.gbest_val = float(self.pbest_val[best_idx])
        
    def optimize(self, max_iter=350, c1=2.0, c2=2.0):
        w_max, w_min = 0.9, 0.4
        
        for it in range(max_iter):
            w = w_max - (w_max - w_min) * (it / max_iter)
            r1 = np.random.rand(self.num_particles, self.dim)
            r2 = np.random.rand(self.num_particles, self.dim)
            
            # Velocity update with clamping
            self.V = w * self.V + c1 * r1 * (self.pbest_X - self.X) + c2 * r2 * (self.gbest_X - self.X)
            self.V = np.clip(self.V, -self.v_max, self.v_max)
            
            self.X += self.V
            self.X = np.clip(self.X, self.bounds[0], self.bounds[1])
            
            # Evaluate fitness
            fitness = shallow_buffer_multimodal_landscape(self.X)
            
            # Update personal bests
            improved = fitness < self.pbest_val
            self.pbest_X[improved] = self.X[improved]
            self.pbest_val[improved] = fitness[improved]
            
            # Update global best
            min_idx = np.argmin(self.pbest_val)
            if self.pbest_val[min_idx] < self.gbest_val:
                self.gbest_val = float(self.pbest_val[min_idx])
                self.gbest_X = self.pbest_X[min_idx].copy()
                
            # Truncated Cauchy Mutation on gbest to leap out of local traps
            # Annealing scale
            cauchy_scale = 1.0 * (1.0 - it / max_iter) + 0.05
            for _ in range(5):
                noise = np.random.standard_cauchy(self.dim) * cauchy_scale
                noise = np.clip(noise, -2.0, 2.0)
                cand_gbest = np.clip(self.gbest_X + noise, self.bounds[0], self.bounds[1])
                cand_fit = float(shallow_buffer_multimodal_landscape(cand_gbest))
                if cand_fit < self.gbest_val:
                    self.gbest_val = cand_fit
                    self.gbest_X = cand_gbest.copy()
                    
        # Local refinement near gbest
        for _ in range(50):
            delta = np.random.normal(0, 0.01, self.dim)
            cand = self.gbest_X + delta
            cand_fit = float(shallow_buffer_multimodal_landscape(cand))
            if cand_fit < self.gbest_val:
                self.gbest_val = cand_fit
                self.gbest_X = cand.copy()
                
        # Variance of top particles
        top_particles = np.sort(self.pbest_val)[:10]
        fitness_var = float(np.var(top_particles))
        return self.gbest_val, self.gbest_X, fitness_var

def main():
    print("=== Task 0473: Truncated Cauchy Mutation PSO ===")
    
    runs = 25
    gbest_values = []
    fitness_variances = []
    
    for r in range(runs):
        pso = TruncatedCauchyPSO(dim=3, num_particles=60, seed=100 + r)
        gbest_val, gbest_pos, fit_var = pso.optimize(max_iter=300)
        gbest_values.append(gbest_val)
        fitness_variances.append(fit_var)
        
    success_count = sum(1 for v in gbest_values if v < 1e-3)
    escape_capture_rate = (success_count / runs) * 100.0
    mean_gbest = float(np.mean(gbest_values))
    mean_var = float(np.mean(fitness_variances))
    
    passed = (escape_capture_rate == 100.0)
    
    summary = {
        "runs": runs,
        "success_runs": success_count,
        "global_optimum_capture_rate": escape_capture_rate,
        "mean_best_fitness": mean_gbest,
        "mean_top10_fitness_variance": mean_var,
        "target_capture_rate": 100.0,
        "passed": bool(passed)
    }
    
    print(json.dumps(summary, indent=2))
    if not passed:
        sys.exit(1)

if __name__ == "__main__":
    main()
