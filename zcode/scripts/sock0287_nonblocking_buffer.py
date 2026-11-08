#!/usr/bin/env python3
"""
Task 0287: Client Network Non-Blocking Socket Buffer Throughput & Latency Test
Tests UDP non-blocking socket send/receive performance under 1200B MTU packet load.
Accounts for OS kernel transition baselines:
- Linux: syscall cost <= 1.8 us (AF_INET UDP)
- Windows: Winsock AFD.sys transition cost <= 10.0 us
"""

import sys
import time
import json
import socket
import threading
from pathlib import Path

def test_nonblocking_socket():
    receiver = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    receiver.bind(("127.0.0.1", 0))
    recv_port = receiver.getsockname()[1]

    receiver.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 2 * 1024 * 1024)
    receiver.setblocking(False)

    sender = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sender.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 1024 * 1024)
    sender.setblocking(False)

    n_batches = 100
    batch_size = 40 # Standard Pacing tick batch
    total_packets = n_batches * batch_size
    pkt_payload = b"X" * 1200 # 1200B MTU payload

    stop_event = threading.Event()
    received_count = 0

    def receiver_loop():
        nonlocal received_count
        while not stop_event.is_set():
            try:
                data, _ = receiver.recvfrom(2048)
                if data:
                    received_count += 1
            except BlockingIOError:
                time.sleep(0.0001)
            except Exception:
                break

    recv_thread = threading.Thread(target=receiver_loop)
    recv_thread.daemon = True
    recv_thread.start()

    per_packet_latencies_us = []
    enobufs_errors = 0
    successful_sends = 0
    target_addr = ("127.0.0.1", recv_port)

    # Pre-warm
    for _ in range(100):
        sender.sendto(pkt_payload, target_addr)
    time.sleep(0.01)

    for b in range(n_batches):
        t0 = time.perf_counter()
        for i in range(batch_size):
            try:
                sender.sendto(pkt_payload, target_addr)
                successful_sends += 1
            except BlockingIOError:
                enobufs_errors += 1
                time.sleep(0.0001)
            except Exception:
                enobufs_errors += 1
        dt_total_us = (time.perf_counter() - t0) * 1e6
        per_packet_latencies_us.append(dt_total_us / batch_size)
        time.sleep(0.003) # 3ms inter-batch spacing

    time.sleep(0.05)
    stop_event.set()
    recv_thread.join(timeout=1.0)

    sender.close()
    receiver.close()

    mean_per_packet_us = float(sum(per_packet_latencies_us) / len(per_packet_latencies_us))
    p95_per_packet_us = float(sorted(per_packet_latencies_us)[int(len(per_packet_latencies_us) * 0.95)])

    is_windows = sys.platform.startswith("win")
    target_max_latency = 10.0 if is_windows else 1.8
    pass_gate = bool(mean_per_packet_us <= target_max_latency and enobufs_errors == 0)

    result = {
        "task_id": "0287",
        "platform": sys.platform,
        "total_packets_sent": successful_sends,
        "enobufs_errors_count": enobufs_errors,
        "mean_send_syscall_latency_us": round(mean_per_packet_us, 2),
        "target_max_latency_us": target_max_latency,
        "p95_send_syscall_latency_us": round(p95_per_packet_us, 2),
        "packets_received_count": received_count,
        "pass_gate": pass_gate
    }

    out_file = Path("runs/sock0287_nonblocking_buffer.json")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(json.dumps(result, indent=2))
    return pass_gate

if __name__ == "__main__":
    passed = test_nonblocking_socket()
    if not passed:
        sys.exit(1)
