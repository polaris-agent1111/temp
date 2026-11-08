#!/usr/bin/env python3
"""
Task 0276: QUIC Datagram Header Compression & CC Overhead Minimization
Quantifies bandwidth savings from 1-RTT Short Header & Truncated Packet Number Encoding
for 250MB stage and full 6-stage transfer under 1200B MTU constraint.
"""

import sys
import json
import math
from pathlib import Path

def evaluate_header_compression():
    file_size_bytes = 250 * 1024 * 1024 # 250 MB
    mtu = 1200 # bytes
    ip_udp_overhead = 20 + 8 # 28 bytes
    aead_tag = 16 # bytes (AES-128-GCM / ChaCha20-Poly1305)

    # 1. Long Header specification (RFC 9000)
    # Flags(1) + Version(4) + DCID_len(1)+DCID(8) + SCID_len(1)+SCID(8) + Length(2) + PN(4)
    long_header_bytes = 1 + 4 + 1 + 8 + 1 + 8 + 2 + 4 # 29 bytes
    max_payload_long = mtu - ip_udp_overhead - long_header_bytes - aead_tag # 1127 bytes
    pkts_needed_long = math.ceil(file_size_bytes / max_payload_long)
    total_wire_bytes_long = pkts_needed_long * mtu

    # 2. Short Header specification (RFC 9000 1-RTT)
    # Flags(1) + DCID(8) + Truncated PN(2 bytes on average with continuous ACK)
    short_header_bytes = 1 + 8 + 2 # 11 bytes
    max_payload_short = mtu - ip_udp_overhead - short_header_bytes - aead_tag # 1145 bytes
    pkts_needed_short = math.ceil(file_size_bytes / max_payload_short)
    total_wire_bytes_short = pkts_needed_short * mtu

    # Savings
    wire_diff_bytes = total_wire_bytes_long - total_wire_bytes_short
    wire_diff_mb = wire_diff_bytes / (1024 * 1024)
    packets_saved = pkts_needed_long - pkts_needed_short

    # 6-stage aggregate
    wire_diff_6stages_mb = wire_diff_mb * 6.0

    pass_gate = bool(wire_diff_mb >= 1.20)

    result = {
        "task_id": "0276",
        "file_size_mb": 250.0,
        "mtu_bytes": mtu,
        "long_header_bytes": long_header_bytes,
        "short_header_bytes": short_header_bytes,
        "header_reduction_per_pkt_bytes": long_header_bytes - short_header_bytes,
        "payload_per_pkt_long_bytes": max_payload_long,
        "payload_per_pkt_short_bytes": max_payload_short,
        "packets_needed_long": pkts_needed_long,
        "packets_needed_short": pkts_needed_short,
        "packets_eliminated_count": packets_saved,
        "net_bandwidth_saved_single_stage_mb": round(wire_diff_mb, 3),
        "target_savings_gate_mb": 1.20,
        "net_bandwidth_saved_6stages_mb": round(wire_diff_6stages_mb, 3),
        "pass_gate": pass_gate
    }

    out_file = Path("runs/quic0276_header_compression.json")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(json.dumps(result, indent=2))
    return pass_gate

if __name__ == "__main__":
    passed = evaluate_header_compression()
    if not passed:
        sys.exit(1)
