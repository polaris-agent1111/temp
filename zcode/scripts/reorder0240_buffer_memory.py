#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Task 0240: QUIC Reassembly Buffer Memory Limit Test under Out-of-Order Packets.
Simulates QUIC stream reassembly under extreme packet reordering:
  - 100 out-of-order packets (gap at packet 0)
  - STREAM frame offset range tracking: [offset, offset + length)
  - Memory consumption of received buffer: payload bytes + interval tree metadata
  - Stream drain latency upon arrival of the missing head packet
Validates that peak memory increase is strictly <= 128.0 KB.
"""
import sys
import time
import numpy as np

class StreamReassemblyBuffer:
    def __init__(self):
        # Maps offset -> bytearray chunk
        self.chunks = {}
        self.next_expected_offset = 0
        self.peak_memory_bytes = 0
        
    def receive_chunk(self, offset, data):
        self.chunks[offset] = data
        # Estimate total memory = raw payload bytes + dict entry overhead (approx 72B per entry)
        current_mem = sum(len(d) for d in self.chunks.values()) + len(self.chunks) * 72
        if current_mem > self.peak_memory_bytes:
            self.peak_memory_bytes = current_mem
            
    def drain_contiguous(self):
        drained_bytes = 0
        while self.next_expected_offset in self.chunks:
            chunk = self.chunks.pop(self.next_expected_offset)
            drained_bytes += len(chunk)
            self.next_expected_offset += len(chunk)
        return drained_bytes

def benchmark_reassembly_memory():
    np.random.seed(42)
    packet_size = 1140  # Standard QUIC STREAM frame payload
    reorder_depth = 100 # 100 packets out of order
    
    # Missing head packet is index 0
    # Packets 1 to 100 arrive in random scrambled order
    indices = list(range(1, reorder_depth + 1))
    np.random.shuffle(indices)
    
    buf = StreamReassemblyBuffer()
    
    # 1. Feed 100 scrambled packets
    for idx in indices:
        offset = idx * packet_size
        payload = b"X" * packet_size
        buf.receive_chunk(offset, payload)
        
    peak_mem_kb = buf.peak_memory_bytes / 1024.0
    
    # 2. Finally receive packet 0 (missing head)
    t0 = time.perf_counter()
    buf.receive_chunk(0, b"X" * packet_size)
    drained = buf.drain_contiguous()
    drain_time_ms = (time.perf_counter() - t0) * 1000.0
    
    remaining_chunks = len(buf.chunks)
    gate_passed = bool(peak_mem_kb <= 128.0 and remaining_chunks == 0)
    
    print("=== Task 0240: QUIC Reassembly Buffer Memory Limit Test ===")
    print(f"Scrambled Packets Count:    {reorder_depth}")
    print(f"Per-Packet Payload Size:    {packet_size} bytes")
    print(f"Peak Reassembly Buffer Mem: {peak_mem_kb:.2f} KB (Gate: <= 128.0 KB)")
    print(f"Head Arrival Drain Time:    {drain_time_ms:.4f} ms")
    print(f"Post-Drain Remaining Chunks:{remaining_chunks} (Gate: == 0)")
    print(f"Memory Safety Assessment:   {'PASS' if gate_passed else 'FAIL'}")
    
    return {
        "peak_mem_kb": peak_mem_kb,
        "drain_time_ms": drain_time_ms,
        "gate_passed": gate_passed
    }

if __name__ == "__main__":
    benchmark_reassembly_memory()
