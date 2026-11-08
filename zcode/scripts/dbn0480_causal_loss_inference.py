# -*- coding: utf-8 -*-
"""
Task 0480: Dynamic Bayesian Network (DBN) Hidden Loss Causal Inference
- Differentiate between shallow buffer overflow congestion loss vs random bit-error dropout
- Hidden states S_t in {0: Normal, 1: Congestion Loss, 2: Random Dropout}
- Vectorized Gaussian forward-backward belief propagation
- Target: Posterior inference accuracy >= 98.0%, Belief propagation convergence rate 100.0%
"""

import sys
import json
import numpy as np

def fast_gaussian_pdf(x, mu, sigma):
    return (1.0 / (np.sqrt(2.0 * np.pi) * sigma)) * np.exp(-0.5 * (((x - mu) / sigma) ** 2))

class LossInferenceDBN:
    def __init__(self):
        self.num_states = 3
        
        # State transition probability matrix P(S_t | S_{t-1})
        self.A = np.array([
            [0.94, 0.04, 0.02],  # Normal -> [Normal, Congestion, Random]
            [0.12, 0.86, 0.02],  # Congestion -> [Normal, Congestion, Random]
            [0.35, 0.05, 0.60]   # Random -> [Normal, Congestion, Random]
        ])
        
        self.pi = np.array([0.90, 0.06, 0.04])
        
        # Delay D_t ~ N(mu_d, sigma_d^2)
        # Normal: 2.0ms; Congestion: 14.0ms; Random: 2.0ms
        self.delay_mu = np.array([2.0, 14.0, 2.0])
        self.delay_sigma = np.array([0.4, 1.2, 0.4])
        
        # Delivery Throughput Rate T_t ~ N(mu_t, sigma_t^2)
        # Normal: 95 Mbps; Congestion: 38 Mbps; Random: 92 Mbps
        self.thru_mu = np.array([95.0, 38.0, 92.0])
        self.thru_sigma = np.array([2.5, 4.0, 3.0])
        
        # Loss probability P(L_t = 1 | S_t)
        self.loss_prob = np.array([0.001, 0.60, 0.55])
        
    def forward_backward_inference(self, loss_seq, delay_seq, thru_seq):
        T = len(loss_seq)
        
        # Vectorized emission matrix B of shape (T, 3)
        p_delay = np.column_stack([
            fast_gaussian_pdf(delay_seq, self.delay_mu[s], self.delay_sigma[s])
            for s in range(self.num_states)
        ])
        p_thru = np.column_stack([
            fast_gaussian_pdf(thru_seq, self.thru_mu[s], self.thru_sigma[s])
            for s in range(self.num_states)
        ])
        p_loss = np.column_stack([
            np.where(loss_seq == 1, self.loss_prob[s], 1.0 - self.loss_prob[s])
            for s in range(self.num_states)
        ])
        
        B = p_delay * p_thru * p_loss + 1e-15
        
        alpha = np.zeros((T, self.num_states))
        c = np.zeros(T)
        
        # Forward pass
        alpha[0] = self.pi * B[0]
        c[0] = np.sum(alpha[0])
        alpha[0] /= max(1e-15, c[0])
        
        for t in range(1, T):
            alpha[t] = (alpha[t - 1] @ self.A) * B[t]
            c[t] = np.sum(alpha[t])
            alpha[t] /= max(1e-15, c[t])
            
        # Backward pass
        beta = np.zeros((T, self.num_states))
        beta[-1] = 1.0
        
        for t in range(T - 2, -1, -1):
            beta[t] = self.A @ (B[t + 1] * beta[t + 1])
            beta[t] /= max(1e-15, c[t + 1])
            
        gamma = alpha * beta
        gamma /= np.sum(gamma, axis=1, keepdims=True)
        return gamma

def generate_telemetry_dataset(T=2000, seed=42):
    np.random.seed(seed)
    dbn = LossInferenceDBN()
    
    states = [np.random.choice(3, p=dbn.pi)]
    for _ in range(1, T):
        prev = states[-1]
        curr = np.random.choice(3, p=dbn.A[prev])
        states.append(curr)
        
    states = np.array(states)
    loss_obs = []
    delay_obs = []
    thru_obs = []
    
    for s in states:
        l = int(np.random.rand() < dbn.loss_prob[s])
        d = float(np.random.normal(loc=dbn.delay_mu[s], scale=dbn.delay_sigma[s]))
        t_rate = float(np.random.normal(loc=dbn.thru_mu[s], scale=dbn.thru_sigma[s]))
        loss_obs.append(l)
        delay_obs.append(d)
        thru_obs.append(t_rate)
        
    return states, np.array(loss_obs), np.array(delay_obs), np.array(thru_obs)

def main():
    print("=== Task 0480: DBN Hidden Loss Causal Inference ===")
    
    runs = 20
    accuracies = []
    loss_accuracies = []
    convergence_flags = []
    
    dbn = LossInferenceDBN()
    
    for r in range(runs):
        y_true, loss_seq, delay_seq, thru_seq = generate_telemetry_dataset(T=2000, seed=100 + r)
        gamma = dbn.forward_backward_inference(loss_seq, delay_seq, thru_seq)
        
        converged = bool(np.all(np.isfinite(gamma)) and np.allclose(np.sum(gamma, axis=1), 1.0))
        convergence_flags.append(converged)
        
        y_pred = np.argmax(gamma, axis=1)
        acc = float(np.mean(y_pred == y_true)) * 100.0
        accuracies.append(acc)
        
        loss_idx = np.where(loss_seq == 1)[0]
        if len(loss_idx) > 0:
            loss_acc = float(np.mean(y_pred[loss_idx] == y_true[loss_idx])) * 100.0
            loss_accuracies.append(loss_acc)
            
    mean_acc = float(np.mean(accuracies))
    min_acc = float(np.min(accuracies))
    mean_loss_acc = float(np.mean(loss_accuracies))
    conv_rate = (sum(convergence_flags) / runs) * 100.0
    
    passed = (mean_acc >= 98.0) and (conv_rate == 100.0)
    
    summary = {
        "runs": runs,
        "mean_posterior_accuracy_percent": mean_acc,
        "min_posterior_accuracy_percent": min_acc,
        "mean_loss_event_accuracy_percent": mean_loss_acc,
        "target_accuracy_threshold_percent": 98.0,
        "belief_propagation_convergence_rate": conv_rate,
        "passed": bool(passed)
    }
    
    print(json.dumps(summary, indent=2))
    if not passed:
        sys.exit(1)

if __name__ == "__main__":
    main()
