#!/usr/bin/env python3
"""sim_v2: mechanistic offline model of the iDSN Q1 evaluation (stdlib only).

Differences from local-eval/tools/offline_pacer_sim.py (v1):
- Background = TrafficGenerator: Poisson requests (lambda = bg_mbps / mean flow size) each served by its
  own TCP flow (slow start from IW10, cubic-like CA, beta 0.7), simulated per RTT round per flow.
- Bottleneck = drop-tail queue limited in packets (Q), served at 100 Mbps, 1 ms ticks, FIFO by class share.
- Download = 6 sequential QUIC connections (1.5 RTT before data), CC in {cubic, bbr}, ACK and loss
  feedback through a 70 ms delay line.
- Pacer modules follow local-eval/docs/official/03_pacer_modules.md. Periodic pacer actions (leak, token
  refill, rate-based release ticks) happen every max(interval, G) + lat microseconds (G = 4000 by default).

All structural unknowns are keyword arguments of simulate_run().
"""
from __future__ import annotations

import heapq
import math
import random

SIZES = [10e6, 20e6, 40e6, 80e6, 160e6, 320e6]
CDF_X = [0, 1e4, 2e4, 3e4, 5e4, 8e4, 2e5, 1e6, 2e6, 5e6, 1e7, 3e7]
CDF_F = [0, .15, .20, .30, .40, .53, .60, .70, .80, .90, .97, 1.0]
MEAN_FLOW = sum((CDF_F[i] - CDF_F[i - 1]) * (CDF_X[i] + CDF_X[i - 1]) / 2 for i in range(1, len(CDF_X)))
LINK_BPS = 100e6
BG_PKT = 1500.0          # wire bytes of a background TCP segment
BG_MSS = 1448.0


def sample_flow(rng):
    u = rng.random()
    for i in range(1, len(CDF_F)):
        if u <= CDF_F[i]:
            f = (u - CDF_F[i - 1]) / (CDF_F[i] - CDF_F[i - 1])
            return CDF_X[i - 1] + f * (CDF_X[i] - CDF_X[i - 1])
    return CDF_X[-1]


def poisson(rng, lam):
    if lam <= 0:
        return 0
    target = math.exp(-lam)
    k, p = 0, 1.0
    while True:
        p *= rng.random()
        if p <= target:
            return k
        k += 1


class Pacer:
    """Decides how many download packets leave the sender in a 1 ms tick.

    room   = packets the CC window allows to be scheduled now
    cc_pps = CC pacing rate in packets/s (used by rate-based modules as min(cc, configured))
    idle   = no packets in flight and nothing scheduled (enable_n_in_flight condition)
    """

    def __init__(self, module, p, pkt, G, lat_us):
        self.m = module
        self.p = p or {}
        self.pkt = pkt
        self.G = G
        self.lat = lat_us
        self.fill = 0.0          # leak bucket content / scheduled-not-sent
        self.tokens = float(self.p.get("tokens", 20))
        self.burst_left = float(self.p.get("burst_tokens", 10))
        self.next_fire = 0.0     # us
        self.next_send = 0.0     # us, rate-based schedule
        self.credit = 0.0

    def period(self, us):
        return max(us, self.G) + self.lat

    def scheduled(self):
        return self.fill

    def step(self, now_us, dt_us, room, cc_pps, idle, in_recovery):
        m, p = self.m, self.p
        if m == "leak_bucket":
            rate = p.get("leak_rate", 10)
            cap = p.get("bucket_cap", 30)
            per = self.period(p.get("leak_interval_us", 1000))
            self.fill += max(0.0, min(cap - self.fill, room))
            out = 0.0
            while now_us >= self.next_fire:
                b = min(rate, self.fill)
                self.fill -= b
                out += b
                self.next_fire += per
            return out
        if m == "token_bucket":
            per = self.period(p.get("token_refill_interval_us", 100))
            burst = p.get("burst", 40)
            while now_us >= self.next_fire:
                self.tokens = min(burst, self.tokens + p.get("token_refill_rate", 10))
                self.next_fire += per
            out = min(self.tokens, room)
            self.tokens -= out
            if out < 1 and idle and room >= 1 and p.get("enable_n_in_flight", 1):
                out = 1.0
            return out
        if m in ("coarse_grained_rate_based", "precise_rate_based", "origin"):
            if m == "origin":
                if idle:
                    # mechanism 3 lets the current packet go; mechanism 1 reset (not in recovery)
                    if not in_recovery:
                        self.burst_left = float(p.get("burst_tokens", 10))
                b = min(self.burst_left, room)
                if b > 0:
                    self.burst_left -= b
                    self.next_send = max(self.next_send, now_us)
                    return b
            elif idle and room >= 1 and p.get("enable_n_in_flight", 1):
                self.next_send = now_us
                return 1.0
            rate_bps = p.get("max_pacing_rate", 0)
            pps = cc_pps if rate_bps <= 0 else min(cc_pps, rate_bps / self.pkt)
            if pps <= 0 or pps == math.inf:
                return room
            gap = 1e6 / pps
            tol = p.get("clock_granularity", 1000)
            # engine only runs pacing checks on its tick grid (every G + lat); precise uses the real clock
            # inside the tick, coarse freezes the clock at tick start - with ticks every G they coincide.
            if now_us < self.next_fire:
                return 0.0
            self.next_fire = now_us + self.period(0)
            if self.next_send < now_us - 2 * self.period(0):
                self.next_send = now_us - 2 * self.period(0)   # app-limited: no unbounded catch-up
            horizon = now_us + tol
            if m == "precise_rate_based":
                horizon += 0.0
            n = 0.0
            while n < room and self.next_send <= horizon:
                n += 1
                self.next_send += gap
            return n
        return room


class Download:
    def __init__(self, cc, pkt, rtt_ticks, rng):
        self.cc = cc
        self.pkt = pkt
        self.D = rtt_ticks
        self.rng = rng

    def reset(self, size_bytes):
        self.total = math.ceil(size_bytes / (self.pkt - 50))   # ~50 B QUIC/UDP/IP overhead
        self.delivered = 0.0
        self.inflight = 0.0
        self.unsent = float(self.total)
        self.cwnd = 10.0
        self.ssthresh = math.inf
        self.wmax = 0.0
        self.epoch = None
        self.recovery_until = -1
        self.ack_line = [0.0] * (self.D + 1)
        self.loss_line = [0.0] * (self.D + 1)
        # bbr
        self.mode = "startup"
        self.btlbw = 0.0            # pkts per tick
        self.bw_samples = []
        self.full_bw = 0.0
        self.full_cnt = 0
        self.round_acked = 0.0
        self.round_start = 0
        self.min_rtt = float(self.D)
        self.min_rtt_stamp = 0
        self.cycle = 0
        self.probe_rtt_until = -1

    # --- congestion control -------------------------------------------------
    def cwnd_now(self):
        if self.cc == "bbr":
            if self.mode == "probe_rtt":
                return 4.0
            if self.btlbw <= 0:
                return max(self.cwnd, 10.0)
            gain = 2.885 if self.mode == "startup" else 2.0
            return max(4.0, gain * self.btlbw * self.min_rtt)
        return self.cwnd

    def pacing_pps(self):
        if self.cc == "bbr":
            if self.btlbw <= 0:
                return 2.885 * 10.0 / (self.D / 1000.0)
            gain = {"startup": 2.885, "drain": 1 / 2.885}.get(self.mode)
            if gain is None:
                gain = [1.25, 0.75, 1, 1, 1, 1, 1, 1][self.cycle] if self.mode == "probe_bw" else 1.0
            return gain * self.btlbw * 1000.0
        srtt_s = self.min_rtt / 1000.0
        return (2.0 if self.cwnd < self.ssthresh else 1.25) * self.cwnd / srtt_s

    def on_ack(self, t, acked, rtt_ticks):
        self.delivered += acked
        self.inflight -= acked
        if rtt_ticks < self.min_rtt or t - self.min_rtt_stamp > 10000:
            if self.cc != "bbr" or rtt_ticks < self.min_rtt:
                self.min_rtt = rtt_ticks
                self.min_rtt_stamp = t
        if self.cc == "bbr":
            self.round_acked += acked
            if t - self.round_start >= max(1, int(self.min_rtt)):
                sample = self.round_acked / (t - self.round_start)
                self.round_acked = 0.0
                self.round_start = t
                self.bw_samples.append(sample)
                if len(self.bw_samples) > 10:
                    self.bw_samples.pop(0)
                self.btlbw = max(self.bw_samples)
                if self.mode == "startup":
                    if self.btlbw >= self.full_bw * 1.25:
                        self.full_bw = self.btlbw
                        self.full_cnt = 0
                    else:
                        self.full_cnt += 1
                        if self.full_cnt >= 3:
                            self.mode = "drain"
                elif self.mode == "drain":
                    if self.inflight <= self.btlbw * self.min_rtt:
                        self.mode = "probe_bw"
                        self.cycle = self.rng.randrange(8)
                elif self.mode == "probe_bw":
                    self.cycle = (self.cycle + 1) % 8
                    if t - self.min_rtt_stamp > 10000:
                        self.mode = "probe_rtt"
                        self.probe_rtt_until = t + 200 + int(self.min_rtt)
                elif self.mode == "probe_rtt" and t >= self.probe_rtt_until:
                    self.min_rtt_stamp = t
                    self.mode = "probe_bw"
            return
        if acked <= 0:
            return
        if self.cwnd < self.ssthresh:
            self.cwnd += acked
            return
        # cubic congestion avoidance (C=0.4, beta=0.7), time in seconds
        if self.epoch is None:
            self.epoch = t
            self.k = ((self.wmax - self.cwnd) / 0.4) ** (1 / 3) if self.wmax > self.cwnd else 0.0
            self.w_origin = max(self.wmax, self.cwnd)
        ts = (t - self.epoch + self.min_rtt) / 1000.0
        target = self.w_origin + 0.4 * (ts - self.k) ** 3
        reno = self.cwnd + acked / self.cwnd
        if target > self.cwnd:
            self.cwnd = max(reno, min(target, self.cwnd + acked * 0.5))
        else:
            self.cwnd = reno

    def on_loss(self, t, lost):
        self.inflight -= lost
        self.unsent += lost
        if self.cc == "bbr":
            return
        if t < self.recovery_until:
            return
        self.recovery_until = t + int(self.min_rtt) + 1
        self.wmax = self.cwnd
        self.cwnd = max(2.0, self.cwnd * 0.7)
        self.ssthresh = self.cwnd
        self.epoch = None

    def in_recovery(self, t):
        return t < self.recovery_until


def simulate_run(cfg, seed, queue=100, cc="bbr", lat=0.0, G=4000.0, pkt=1250.0, bg_mbps=100.0,
                 warmup=5.0, gap=0.3, t_max=500.0, bg_iw=10, bg_beta=0.7, handshake_rtts=1.5,
                 bg_rto=1, jitter_seed=0, start_jitter_ms=0):
    rng_bg = random.Random(seed * 7919 + 11)          # TrafficGenerator: arrivals + sizes (fixed by -s)
    rng = random.Random((seed * 7919 + 11) * 1000003 + jitter_seed)   # everything else (system randomness)
    dt_us = 1000.0
    c_bytes = LINK_BPS / 8 * dt_us / 1e6        # bytes served per tick
    D = 70                                       # base RTT in ticks
    lam = bg_mbps * 1e6 / 8 / MEAN_FLOW * dt_us / 1e6
    # queue state (packets per class)
    qd = 0.0
    qb = 0.0
    # background flow table: id -> [rem_pkts, w, ssthresh, wmax, epoch_t, k, rate, round_start, sent_round]
    flows = {}
    heap = []
    pending = []                 # (activate_tick, size)
    fid = 0
    bg_rate = 0.0
    acc_arr = 0.0                # cumulative bg arrivals to queue (pkts)
    acc_drop = 0.0
    hist_arr = {}
    t = 0
    per_file = []

    def start_round(i, f, now):
        nonlocal bg_rate
        send = min(f[1], f[0])
        rt = D + int((qd * pkt + qb * BG_PKT) / c_bytes)
        f[6] = send / rt
        f[7] = now
        f[8] = send
        hist_arr[i] = (acc_arr, acc_drop)
        bg_rate += f[6]
        heapq.heappush(heap, (now + rt, i))

    def end_round(i, now):
        nonlocal bg_rate
        f = flows.get(i)
        if f is None:
            return
        bg_rate -= f[6]
        a0, d0 = hist_arr.pop(i)
        da = acc_arr - a0
        p = (acc_drop - d0) / da if da > 1e-9 else 0.0
        sent = f[8]
        lost = sent * p
        f[0] -= sent - lost
        if f[0] <= 0.5:
            del flows[i]
            return
        if f[10]:
            # retransmission timeout expired: restart from cwnd 1
            f[10] = 0
            f[1] = 1.0
            start_round(i, f, now)
            return
        lossy = p > 0 and rng.random() < 1.0 - (1.0 - p) ** max(1.0, sent)
        if lossy and bg_rto and rng.random() < min(1.0, bg_rto / max(1.0, sent)):
            # too few packets for 3 dup-ACKs: RTO with exponential backoff, flow goes silent
            f[2] = max(2.0, f[1] / 2)
            f[3] = f[1]
            f[9] = min(f[9] + 1, 6)
            f[10] = 1
            f[6] = 0.0
            f[8] = 0.0
            hist_arr[i] = (acc_arr, acc_drop)
            heapq.heappush(heap, (now + int(200 * 2 ** (f[9] - 1)), i))
            return
        if not lossy:
            f[9] = 0
        if lossy:
            f[3] = f[1]
            f[1] = max(2.0, f[1] * bg_beta)
            f[2] = f[1]
            f[4] = now
            f[5] = ((f[3] - f[1]) / 0.4) ** (1 / 3) if f[3] > f[1] else 0.0
        elif f[1] < f[2]:
            f[1] = min(f[1] * 2, max(2 * sent, 10))
        else:
            ts = (now - f[4]) / 1000.0
            target = f[3] + 0.4 * (ts - f[5]) ** 3
            f[1] = max(f[1] + 1, min(target, f[1] * 1.5)) if sent >= f[1] - 1 else f[1]
        start_round(i, f, now)

    def bg_tick():
        nonlocal fid
        for _ in range(poisson(rng_bg, lam)):
            pending.append((t + 35, sample_flow(rng_bg)))
        if pending:
            keep = []
            for at, size in pending:
                if at <= t:
                    fid += 1
                    f = [math.ceil(size / BG_MSS), float(bg_iw), math.inf, 0.0, t, 0.0, 0.0, t, 0.0, 0, 0]
                    flows[fid] = f
                    start_round(fid, f, t)
                else:
                    keep.append((at, size))
            pending[:] = keep
        while heap and heap[0][0] <= t:
            _, i = heapq.heappop(heap)
            end_round(i, t)

    def queue_tick(off_d, off_b):
        """returns (dep_d, drop_d, drop_b) and updates queue."""
        nonlocal qd, qb, acc_arr, acc_drop
        qbytes = qd * pkt + qb * BG_PKT
        serve = min(c_bytes, qbytes + off_d * pkt + off_b * BG_PKT)
        # FIFO approximation: departures drawn from current queue first, then from arrivals
        if qbytes > 0:
            from_q = min(serve, qbytes)
            fd = qd * pkt / qbytes
            dep_d = from_q * fd / pkt
            dep_b = from_q * (1 - fd) / BG_PKT
            left = serve - from_q
        else:
            dep_d = dep_b = 0.0
            left = serve
        arr_bytes = off_d * pkt + off_b * BG_PKT
        if left > 0 and arr_bytes > 0:
            fa = off_d * pkt / arr_bytes
            dep_d += left * fa / pkt
            dep_b += left * (1 - fa) / BG_PKT
        nqd = qd + off_d - dep_d
        nqb = qb + off_b - dep_b
        over = nqd + nqb - queue
        drop_d = drop_b = 0.0
        if over > 0:
            arr = off_d + off_b
            fd_arr = off_d / arr if arr > 0 else 0.0
            drop_d = min(nqd, over * fd_arr)
            drop_b = min(nqb, over - drop_d)
            nqd -= drop_d
            nqb -= drop_b
        qd, qb = max(0.0, nqd), max(0.0, nqb)
        acc_arr += off_b
        acc_drop += drop_b
        return dep_d, drop_d

    # warm-up: background only
    while t < int(warmup * 1000):
        t += 1
        bg_tick()
        queue_tick(0.0, bg_rate)

    dl = Download(cc, pkt, D, rng)
    prev = ("origin", {})
    for idx, size in enumerate(SIZES, 1):
        c = cfg.get(str(idx))
        if c:
            prev = (c[0], c[1] if len(c) > 1 else {})
        module, params = prev
        pacer = Pacer(module, params, pkt, G, lat)
        dl.reset(size)
        t_file0 = t
        hs = int(handshake_rtts * D) + (rng.randrange(start_jitter_ms + 1) if start_jitter_ms else 0)
        for _ in range(hs):
            t += 1
            bg_tick()
            queue_tick(0.0, bg_rate)
        pacer.next_fire = t * dt_us
        pacer.next_send = t * dt_us
        slot = 0
        while dl.delivered < dl.total - 0.5 and t < t_max * 1000:
            t += 1
            slot = (slot + 1) % (D + 1)
            bg_tick()
            acked = dl.ack_line[slot]
            lost = dl.loss_line[slot]
            dl.ack_line[slot] = 0.0
            dl.loss_line[slot] = 0.0
            qdelay = int((qd * pkt + qb * BG_PKT) / c_bytes)
            if acked:
                dl.on_ack(t, acked, D + qdelay)
            elif dl.cc == "bbr":
                dl.on_ack(t, 0.0, D + qdelay)
            if lost:
                dl.on_loss(t, lost)
            sched = pacer.scheduled()
            room = max(0.0, min(dl.cwnd_now() - dl.inflight - sched, dl.unsent - sched))
            idle = dl.inflight < 0.5 and sched < 0.5
            out = pacer.step(t * dt_us, dt_us, room, dl.pacing_pps(), idle, dl.in_recovery(t))
            out = min(out, dl.unsent)
            dl.unsent -= out
            dl.inflight += out
            dep_d, drop_d = queue_tick(out, bg_rate)
            # departures are acked one base RTT later (queueing already elapsed), drops detected likewise
            k = (slot + D) % (D + 1)
            dl.ack_line[k] += dep_d
            dl.loss_line[k] += drop_d
        per_file.append((t - t_file0) / 1000.0)
        if dl.delivered < dl.total - 0.5:
            return {"total": sum(per_file), "per_file": per_file + [0.0] * (6 - len(per_file)), "valid": False}
        for _ in range(int(gap * 1000)):
            t += 1
            bg_tick()
            queue_tick(0.0, bg_rate)
    return {"total": sum(per_file), "per_file": per_file, "valid": True, "bg_active_end": len(flows)}


if __name__ == "__main__":
    import json
    import sys
    import time
    cfg = {str(i): ["leak_bucket", {"leak_rate": 36, "bucket_cap": 40, "leak_interval_us": 4000}] for i in range(1, 7)}
    t0 = time.time()
    r = simulate_run(cfg, int(sys.argv[1]) if len(sys.argv) > 1 else 1)
    print(json.dumps(r), f"{time.time() - t0:.1f}s")
