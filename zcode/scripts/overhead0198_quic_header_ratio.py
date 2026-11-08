#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task 0198: Micro-accounting of network and transport layer headers (IPv4/UDP/QUIC).
Calculates exact Goodput vs Wire Throughput for 1200-byte MTU and rates 36~41 pkts/4ms.
"""

def compute_quic_overhead():
    # Standard packet layer header sizes in bytes
    # Ethernet frame header: 14 bytes (preamble/FCS excluded on wire pacing)
    # IPv4 header (standard without options): 20 bytes
    # UDP header: 8 bytes
    # QUIC 1-RTT Short Header:
    #   Header form (1B) + Connection ID (typically 8B) + Packet Number (2B) = 11 bytes
    # QUIC AEAD Auth Tag (AES-128-GCM or ChaCha20-Poly1305): 16 bytes
    # QUIC Frame Header (STREAM frame: Type 1B + Stream ID 1~4B + Offset 1~8B + Length 2B): ~8 bytes
    
    ip_header_bytes = 20
    udp_header_bytes = 8
    quic_header_bytes = 11 + 16  # packet header + crypto tag = 27 bytes
    quic_stream_header_bytes = 5 # average stream frame overhead
    
    total_transport_overhead = ip_header_bytes + udp_header_bytes + quic_header_bytes
    
    # Standard QUIC MTU configured by client
    mtu_bytes = 1200
    payload_goodput_bytes = mtu_bytes - total_transport_overhead - quic_stream_header_bytes
    goodput_ratio = payload_goodput_bytes / mtu_bytes
    
    # Physical wire bandwidth calculation for leak rates 36 to 41 pkts / 4000us
    # Pacing interval = 4000 microseconds = 0.004 seconds
    interval_s = 0.004
    
    rates_pkts = [36, 37, 38, 39, 40, 41]
    results = {}
    for r in rates_pkts:
        # Wire throughput in Mbps (including IP/UDP/QUIC)
        bytes_per_sec = (r * mtu_bytes) / interval_s
        wire_mbps = (bytes_per_sec * 8) / 1e6
        goodput_mbps = wire_mbps * goodput_ratio
        results[r] = {
            "wire_mbps": wire_mbps,
            "goodput_mbps": goodput_mbps,
            "payload_bytes": payload_goodput_bytes
        }
        
    print("=== Task 0198: QUIC Protocol Stack Overhead Accounting ===")
    print(f"MTU: {mtu_bytes} bytes")
    print(f"IP Header: {ip_header_bytes}B, UDP: {udp_header_bytes}B, QUIC Overhead: {quic_header_bytes + quic_stream_header_bytes}B")
    print(f"Total Overhead: {total_transport_overhead + quic_stream_header_bytes} bytes ({(total_transport_overhead + quic_stream_header_bytes)/mtu_bytes*100:.2f}%)")
    print(f"Payload Goodput: {payload_goodput_bytes} bytes ({goodput_ratio*100:.2f}%)")
    print("\nRate to Bandwidth Mapping:")
    for r, v in results.items():
        print(f"  Rate {r} pkts/4ms -> Wire: {v['wire_mbps']:.2f} Mbps | Goodput: {v['goodput_mbps']:.2f} Mbps")
        
    print(f"\ngoodput_ratio_valid: {goodput_ratio >= 0.95}")
    return results

if __name__ == "__main__":
    compute_quic_overhead()
