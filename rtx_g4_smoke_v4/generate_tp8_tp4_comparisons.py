import json, os, csv

base_dir = r"c:\Users\ayu23\OneDrive\Desktop\tpu\rtx_g4_smoke_v4\results"
json_path = os.path.join(base_dir, "fresh_benchmark_suite", "master_benchmarks.json")

with open(json_path, "r") as f:
    data = json.load(f)

collectives = {
    "allreduce": "AllReduce",
    "allgather": "AllGather",
    "reducescatter": "ReduceScatter"
}

def fmt_size(b):
    kb = b / 1024
    mb = b / (1024 * 1024)
    if mb >= 1:
        return f"{int(mb)} MiB" if mb % 1 == 0 else f"{mb:.1f} MiB"
    return f"{int(kb)} KiB" if kb % 1 == 0 else f"{kb:.1f} KiB"

def get_label(b):
    if b == 8192: return "Min Size Floor"
    if b == 16384: return "Batch-1 Token Decode"
    if b == 131072: return "Small Activation"
    if b == 1048576: return "1 MiB Tensor"
    if b == 16777216: return "16 MiB Activation"
    if b == 67108864: return "64 MiB Chunk"
    if b == 134217728: return "8K Prefill Chunk (128 MiB)"
    if b == 268435456: return "Large Prefill (256 MiB)"
    return fmt_size(b)

all_rows_master = []

for tp_cfg, tp_title, local_key, local_desc in [
    ("tp8", "TP=8", "tp8_local", "Node-Local Dual-Socket"),
    ("tp4", "TP=4", "tp4_local", "Socket-Local Single-NUMA")
]:
    for coll_key, coll_name in collectives.items():
        coll_data = data[coll_key]
        local_data = coll_data[local_key]
        multi_data = coll_data[tp_cfg]

        sizes = sorted([int(k) for k in multi_data["NATIVE"].keys()])

        rows = []
        for s in sizes:
            str_s = str(s)
            t_local = local_data.get(str_s, {}).get("time_us", 0) / 1000.0
            bw_local = local_data.get(str_s, {}).get("algbw_gb_s", 0)

            t_175 = multi_data["NATIVE"].get(str_s, {}).get("time_us", 0) / 1000.0
            bw_175 = multi_data["NATIVE"].get(str_s, {}).get("algbw_gb_s", 0)

            t_100 = multi_data["100"].get(str_s, {}).get("time_us", 0) / 1000.0
            bw_100 = multi_data["100"].get(str_s, {}).get("algbw_gb_s", 0)

            t_50 = multi_data["50"].get(str_s, {}).get("time_us", 0) / 1000.0
            bw_50 = multi_data["50"].get(str_s, {}).get("algbw_gb_s", 0)

            t_20 = multi_data["20"].get(str_s, {}).get("time_us", 0) / 1000.0
            bw_20 = multi_data["20"].get(str_s, {}).get("algbw_gb_s", 0)

            t_10 = multi_data["10"].get(str_s, {}).get("time_us", 0) / 1000.0
            bw_10 = multi_data["10"].get(str_s, {}).get("algbw_gb_s", 0)

            slowdown_native = f"{(t_175 / t_local):.2f}x" if t_local > 0 else "-"
            slowdown_10g = f"{(t_10 / t_local):.2f}x" if t_local > 0 else "-"

            row = {
                "topology": tp_title,
                "local_baseline_type": local_desc,
                "collective": coll_name,
                "size_bytes": s,
                "payload_label": fmt_size(s),
                "description": get_label(s),
                "local_latency_ms": round(t_local, 3),
                "local_algbw_gbs": round(bw_local, 2),
                "multi_native_175g_ms": round(t_175, 3),
                "multi_native_algbw_gbs": round(bw_175, 2),
                "multi_100g_ms": round(t_100, 3),
                "multi_100g_algbw_gbs": round(bw_100, 2),
                "multi_50g_ms": round(t_50, 3),
                "multi_50g_algbw_gbs": round(bw_50, 2),
                "multi_20g_ms": round(t_20, 3),
                "multi_20g_algbw_gbs": round(bw_20, 2),
                "multi_10g_ms": round(t_10, 3),
                "multi_10g_algbw_gbs": round(bw_10, 2),
                "multi_native_vs_local": slowdown_native,
                "multi_10g_vs_local": slowdown_10g
            }
            rows.append(row)
            all_rows_master.append(row)

        # Write individual collective CSV for this TP
        csv_path = os.path.join(base_dir, f"{tp_cfg}_multinode_vs_local_{coll_key}_comparison.csv")
        with open(csv_path, "w", newline="") as f:
            fieldnames = [k for k in rows[0].keys()]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

# Write Master All-in-One CSV
master_csv = os.path.join(base_dir, "tp8_and_tp4_local_vs_multinode_comparison_master.csv")
with open(master_csv, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=all_rows_master[0].keys())
    writer.writeheader()
    writer.writerows(all_rows_master)

# Write Comprehensive Markdown Report for Boss
md_path = os.path.join(base_dir, "TP8_AND_TP4_LOCAL_VS_MULTINODE_REPORT.md")
with open(md_path, "w", encoding="utf-8") as f:
    f.write("# Distributed Network Sweeps: TP-8 & TP-4 Local vs. Multi-Node\n\n")
    f.write("**Hardware Platform:** 16x NVIDIA RTX PRO 6000 Blackwell GPUs (Dual-Socket Node with PCIe Gen5 x16)\n")
    f.write("**Cluster:** `kimi-node-0` (10.128.0.39) & `kimi-node-1` (10.128.0.40) on GCP VPC (us-central1-b)\n")
    f.write("**Configurations Covered:**\n")
    f.write("- **TP-8 Local (Single-Node Dual-Socket PCIe Gen5)** vs. **TP-8 Multi-Node (4 ranks/node across 2 nodes)**\n")
    f.write("- **TP-4 Local (Single-Node Single-NUMA Socket-Local)** vs. **TP-4 Multi-Node (2 ranks/node across 2 nodes)**\n")
    f.write("- **Network Rates:** 175G Native (173.6 Gbps), 100G, 50G, 20G, 10G Egress Caps\n\n")

    f.write("## 1. Executive Summary: 256 MiB Large Prefill Across All Topologies & Rates\n\n")
    f.write("| Topology | Collective | Local Baseline | Multi-Node (175G) | Multi-Node (100G) | Multi-Node (50G) | Multi-Node (20G) | Multi-Node (10G) | Slowdown (175G vs Loc) | Slowdown (10G vs Loc) |\n")
    f.write("| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |\n")

    for tp_cfg, tp_title in [("tp8", "TP=8"), ("tp4", "TP=4")]:
        for coll_key, coll_name in collectives.items():
            sub = [r for r in all_rows_master if r["topology"] == tp_title and r["collective"] == coll_name and r["size_bytes"] == 268435456][0]
            loc_t = sub["local_latency_ms"]
            t175 = sub["multi_native_175g_ms"]
            t100 = sub["multi_100g_ms"]
            t50 = sub["multi_50g_ms"]
            t20 = sub["multi_20g_ms"]
            t10 = sub["multi_10g_ms"]
            sd_nat = sub["multi_native_vs_local"]
            sd_10g = sub["multi_10g_vs_local"]
            f.write(f"| **{tp_title}** | {coll_name} | **{loc_t} ms** | **{t175} ms** | {t100} ms | {t50} ms | {t20} ms | **{t10} ms** | **{sd_nat}** | **{sd_10g}** |\n")

    f.write("\n---\n\n")

    for tp_cfg, tp_title, local_desc in [
        ("tp8", "TP=8", "Node-Local Dual-Socket PCIe Gen5"),
        ("tp4", "TP=4", "Socket-Local Single-NUMA PCIe Gen5")
    ]:
        f.write(f"## 2. Detailed Breakdown: {tp_title} Multi-Node vs. {tp_title} Local ({local_desc})\n\n")
        for coll_key, coll_name in collectives.items():
            f.write(f"### {coll_name} ({tp_title})\n\n")
            f.write(f"| Payload Size | Milestone Description | {tp_title} Local | Multi-Node (175G) | Multi-Node (100G) | Multi-Node (50G) | Multi-Node (20G) | Multi-Node (10G) | Slowdown (175G vs Loc) | Slowdown (10G vs Loc) |\n")
            f.write("| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |\n")
            coll_rows = [r for r in all_rows_master if r["topology"] == tp_title and r["collective"] == coll_name]
            for r in coll_rows:
                f.write(f"| **{r['payload_label']}** | {r['description']} | **{r['local_latency_ms']} ms** | **{r['multi_native_175g_ms']} ms** | {r['multi_100g_ms']} ms | {r['multi_50g_ms']} ms | {r['multi_20g_ms']} ms | **{r['multi_10g_ms']} ms** | {r['multi_native_vs_local']} | {r['multi_10g_vs_local']} |\n")
            f.write("\n")

    f.write("## 3. Key Architecture & Sizing Takeaways for Leadership\n\n")
    f.write("1. **Local NUMA / PCIe Scaling Efficiency**:\n")
    f.write("   - **TP-4 Local (Single-NUMA socket)** completes a 256 MiB AllReduce in **15.38 ms**, while **TP-8 Local (Dual-socket node)** completes it in **18.01 ms**. Both vastly outperform multi-node communication due to direct PCIe Gen5 x16 host interconnects without network packetization.\n")
    f.write("2. **Multi-Node Scaling Behavior (TP-8 & TP-4 Across Hosts)**:\n")
    f.write("   - When splitting TP-8 across two hosts (4 GPUs on Node 0 + 4 GPUs on Node 1), 256 MiB AllReduce takes **52.55 ms** on 175G Native VPC, scaling linearly with network throttling up to **393.86 ms** on a 10G link (~7.5x slower).\n")
    f.write("   - When splitting TP-4 across two hosts (2 GPUs on Node 0 + 2 GPUs on Node 1), 256 MiB AllReduce takes **41.38 ms** on 175G Native VPC, scaling to **337.76 ms** on a 10G link.\n")
    f.write("3. **Network Sensitivity Threshold**:\n")
    f.write("   - In both TP-8 and TP-4 multi-node distributed setups, bandwidth throttling below 50 Gbps causes an immediate linear degradation in throughput: dropping from 50G to 10G increases prefill allreduce latency by exactly **5.0x** (from ~67-79 ms to ~337-393 ms), directly bounding large-batch inference throughput.\n")

print("Generated all TP-8 and TP-4 comparisons successfully!")
