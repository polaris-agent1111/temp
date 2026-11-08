# -*- coding: utf-8 -*-
"""0086 临时调试：单种子轨迹追踪（非交付物，仅验证仿真守恒与闭环轨迹）。"""
import sys
import numpy as np

sys.stdout.reconfigure(encoding="utf-8")

C_BPS = 12.5e6
MSS = 1200.0
MU = C_BPS / MSS
RTT = 0.070
B = 40.0
G = 9000.0
IW = 10.0
CMIN = 2.0

rng = np.random.default_rng(7)
n = 1
q = np.zeros(n)
cw = np.full(n, IW)
ss = np.ones(n, bool)
rb = np.zeros(n)
delivered = np.zeros(n)
target = 160e6
dt = RTT
sat0, rho_after = 2.40, 0.44
sat = np.full(n, sat0)
rb = np.where(sat > 0, MU, 0.0)
t = 0.0
print(" t(s)   cw     ss  rb      q     delivered_MB  loss")
for step in range(1200):
    in_sat = sat > 0
    rb_eff = np.where(in_sat, MU, rho_after * MU)
    off_o = np.minimum(G, cw / RTT) * dt
    off_b = rb_eff * dt
    tot = off_o + off_b
    cap = MU * dt + np.maximum(0.0, B - q)
    overflow = np.maximum(0.0, tot - cap)
    accepted = tot - overflow
    share = accepted / np.maximum(tot, 1e-12)
    acc_o = off_o * share
    q = np.clip(q + accepted - MU * dt, 0.0, B)
    loss_o = bool((overflow > 1e-12) & (off_o > 0))
    cw = np.where(loss_o & ~ss, np.maximum(CMIN, cw * 0.5), cw)
    ss = ~(ss & loss_o)
    ss = ss & (cw < 2.0 * G * RTT)
    cw = np.where(ss & ~loss_o, cw * 2.0, cw)
    cw = np.where(~ss & ~loss_o, cw + 1.0, cw)  # reno
    delivered += acc_o * MSS
    t += dt
    sat = np.maximum(0.0, sat - dt)
    if step % 50 == 0 or (delivered[0] >= target):
        print(f"{t:6.2f} {cw[0]:7.1f} {int(ss[0])} {rb_eff[0]:8.0f} {q[0]:6.1f} {delivered[0]/1e6:10.2f}  {loss_o}")
    if delivered[0] >= target:
        print("DONE at", t)
        break
