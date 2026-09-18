import os, json, csv

base_dir = r"c:\Users\ayu23\OneDrive\Desktop\tpu\rtx_g4_smoke_v4\results"
json_path = os.path.join(base_dir, "master_benchmarks_all_collectives.json")

with open(json_path, 'r', encoding='utf-8') as f:
    master_data = json.load(f)

# 1. SENDRECV EXECUTIVE REPORT
sr = master_data.get('sendrecv', {})
sr_report_path = os.path.join(base_dir, "SENDRECV_EXECUTIVE_REPORT.md")
with open(sr_report_path, 'w', encoding='utf-8') as f:
    f.write("""# 2-Node P2P Send/Recv vs Intra-Node Baseline Characterization
**Target Hardware:** 2 Nodes × 8x NVIDIA RTX PRO 6000 Ada (Blackwell Generation Server Nodes)  
**Methodology:** Live NCCL `sendrecv_perf` benchmarks across all payload sizes (8 KiB to 256 MiB).  
**Evidence Level:** `MEASURED-GCP-HW` (100% Real Empirical VM Telemetry).

---

## 1. Executive Summary & Key Architectural Findings
1. **Decode Latency Floor (α-bound):**
   - Intra-NUMA (same socket): **0.0091 ms (9.1 µs)**.
   - Cross-NUMA (inter-socket UPI): **0.0092 ms (9.2 µs)**.
   - 2-Node P2P (175G Native TCP): **0.0801 ms (80.1 µs)**.
   - *Key Takeaway:* 2-Node network hop incurs an ~8.8x latency penalty over local PCIe on small decode tokens due to Linux network stack traversal.
2. **Prefill Throughput & Bandwidth (β-bound):**
   - At 256 MiB payload, 2-node P2P over 175G native fabric reaches **2.75 GB/s (97.54 ms)**.
   - Throttling to 10G caps bandwidth at **1.19 GB/s (~9.52 Gbps, saturating 10G link)**, pushing latency to **225.36 ms (31.4x slowdown over local PCIe)**.

---

## 2. Empirical Benchmark Table (All Units in Milliseconds - ms)
| Buffer Size | Payload Label | Local Intra-NUMA (ms) | Local Cross-NUMA (ms) | 2-Node 175G Native (ms) | 2-Node 100G (ms) | 2-Node 50G (ms) | 2-Node 20G (ms) | 2-Node 10G (ms) | 10G vs Local Intra |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
""")
    sizes = sorted(master_data['sendrecv']['NATIVE'].keys(), key=int)
    for s in sizes:
        sz = int(s)
        kb = sz / 1024.0
        mb = sz / (1024.0 * 1024.0)
        lbl = f"{int(mb) if mb.is_integer() else mb:.1f} MiB" if mb >= 1 else f"{int(kb) if kb.is_integer() else kb:.1f} KiB"
        intra = master_data['sendrecv']['local_intra'].get(s, {}).get('time_ms', 0)
        cross = master_data['sendrecv']['local_cross'].get(s, {}).get('time_ms', 0)
        nat = master_data['sendrecv']['NATIVE'].get(s, {}).get('time_ms', 0)
        t100 = master_data['sendrecv']['100'].get(s, {}).get('time_ms', 0)
        t50 = master_data['sendrecv']['50'].get(s, {}).get('time_ms', 0)
        t20 = master_data['sendrecv']['20'].get(s, {}).get('time_ms', 0)
        t10 = master_data['sendrecv']['10'].get(s, {}).get('time_ms', 0)
        pen = f"{(t10/intra):.2f}x" if intra > 0 else "-"
        f.write(f"| {sz} | **{lbl}** | {intra:.4f} ms | {cross:.4f} ms | {nat:.4f} ms | {t100:.4f} ms | {t50:.4f} ms | {t20:.4f} ms | **{t10:.4f} ms** | **{pen}** |\n")

print(f"Generated: {sr_report_path}")

# 2. ALLTOALL EXECUTIVE REPORT
a2a = master_data.get('alltoall', {})
a2a_report_path = os.path.join(base_dir, "ALLTOALL_EXECUTIVE_REPORT.md")
with open(a2a_report_path, 'w', encoding='utf-8') as f:
    f.write("""# AllToAll Distributed Characterization (TP16, TP8, TP4 vs Local)
**Target Hardware:** 2 Nodes × 8x NVIDIA RTX PRO 6000 Ada (16 GPUs Multi-Node)  
**Methodology:** Live NCCL `alltoall_perf` sweeps across 5 network bandwidth tiers (10G - 175G) and local intra-node baselines.  
**Evidence Level:** `MEASURED-GCP-HW` (100% Real Empirical VM Telemetry).

---

## 1. Executive Summary & All-to-All Fabric Stress Analysis
1. **All-to-All Cross-Traffic Congestion:**
   - In TP16 AllToAll, every GPU sends a separate slice to all 15 other GPUs ($16 \\times 15 = 240$ simultaneous traffic flows, 128 of which cross the physical network interface).
   - At 10G network cap, inter-node queueing explodes: 256 MiB AllToAll latency climbs to **1242.26 ms (1.24 seconds)**, compared to **11.01 ms** on single-node TP8 (**112.8x penalty!**).
2. **NUMA / Socket-Local TP4 Baseline:**
   - TP4 local AllToAll achieves **0.016 ms (16 µs)** latency floor and up to **24.5 GB/s** algorithmic bandwidth.
   - Multi-node TP4 (2 GPUs per node) incurs ~0.25 ms floor due to network sync.

---

## 2. Empirical Benchmark Table (TP16 vs Local TP8 Baseline)
| Buffer Size | Payload Label | TP8 Local (ms) | TP16 175G Native (ms) | TP16 100G (ms) | TP16 50G (ms) | TP16 20G (ms) | TP16 10G (ms) | 10G vs Local TP8 Penalty |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
""")
    sizes = sorted(master_data['alltoall']['tp16']['NATIVE'].keys(), key=int)
    for s in sizes:
        sz = int(s)
        kb = sz / 1024.0
        mb = sz / (1024.0 * 1024.0)
        lbl = f"{int(mb) if mb.is_integer() else mb:.1f} MiB" if mb >= 1 else f"{int(kb) if kb.is_integer() else kb:.1f} KiB"
        loc = master_data['alltoall']['tp8_local'].get(s, {}).get('time_ms', 0)
        nat = master_data['alltoall']['tp16']['NATIVE'].get(s, {}).get('time_ms', 0)
        t100 = master_data['alltoall']['tp16']['100'].get(s, {}).get('time_ms', 0)
        t50 = master_data['alltoall']['tp16']['50'].get(s, {}).get('time_ms', 0)
        t20 = master_data['alltoall']['tp16']['20'].get(s, {}).get('time_ms', 0)
        t10 = master_data['alltoall']['tp16']['10'].get(s, {}).get('time_ms', 0)
        pen = f"{(t10/loc):.2f}x" if loc > 0 else "-"
        f.write(f"| {sz} | **{lbl}** | {loc:.4f} ms | {nat:.4f} ms | {t100:.4f} ms | {t50:.4f} ms | {t20:.4f} ms | **{t10:.4f} ms** | **{pen}** |\n")

print(f"Generated: {a2a_report_path}")
