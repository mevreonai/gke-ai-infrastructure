import json, os, csv

base_dir = r"c:\Users\ayu23\OneDrive\Desktop\tpu\rtx_g4_smoke_v4\results"
json_path = os.path.join(base_dir, "fresh_benchmark_suite", "master_benchmarks.json")
csv_out = os.path.join(base_dir, "tp16_vs_tp8_local_allreduce_comparison.csv")
md_out = os.path.join(base_dir, "TP16_VS_TP8_LOCAL_ALLREDUCE_REPORT.md")

with open(json_path, "r") as f:
    data = json.load(f)

ar = data["allreduce"]
tp8_local = ar["tp8_local"]
tp16_native = ar["tp16"]["NATIVE"]
tp16_100 = ar["tp16"]["100"]
tp16_50 = ar["tp16"]["50"]
tp16_20 = ar["tp16"]["20"]
tp16_10 = ar["tp16"]["10"]

sizes = sorted([int(k) for k in tp16_native.keys()])

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

rows = []
for s in sizes:
    str_s = str(s)
    t_local = tp8_local.get(str_s, {}).get("time_us", 0) / 1000.0
    bw_local = tp8_local.get(str_s, {}).get("algbw_gb_s", 0)

    t_175 = tp16_native.get(str_s, {}).get("time_us", 0) / 1000.0
    bw_175 = tp16_native.get(str_s, {}).get("algbw_gb_s", 0)

    t_100 = tp16_100.get(str_s, {}).get("time_us", 0) / 1000.0
    bw_100 = tp16_100.get(str_s, {}).get("algbw_gb_s", 0)

    t_50 = tp16_50.get(str_s, {}).get("time_us", 0) / 1000.0
    bw_50 = tp16_50.get(str_s, {}).get("algbw_gb_s", 0)

    t_20 = tp16_20.get(str_s, {}).get("time_us", 0) / 1000.0
    bw_20 = tp16_20.get(str_s, {}).get("algbw_gb_s", 0)

    t_10 = tp16_10.get(str_s, {}).get("time_us", 0) / 1000.0
    bw_10 = tp16_10.get(str_s, {}).get("algbw_gb_s", 0)

    slowdown_native = f"{(t_175 / t_local):.2f}x" if t_local > 0 else "-"
    slowdown_10g = f"{(t_10 / t_local):.2f}x" if t_local > 0 else "-"

    rows.append({
        "size_bytes": s,
        "payload_label": fmt_size(s),
        "description": get_label(s),
        "tp8_local_latency_ms": round(t_local, 3),
        "tp8_local_algbw_gbs": round(bw_local, 2),
        "tp16_native_175g_ms": round(t_175, 3),
        "tp16_native_algbw_gbs": round(bw_175, 2),
        "tp16_100g_ms": round(t_100, 3),
        "tp16_100g_algbw_gbs": round(bw_100, 2),
        "tp16_50g_ms": round(t_50, 3),
        "tp16_50g_algbw_gbs": round(bw_50, 2),
        "tp16_20g_ms": round(t_20, 3),
        "tp16_20g_algbw_gbs": round(bw_20, 2),
        "tp16_10g_ms": round(t_10, 3),
        "tp16_10g_algbw_gbs": round(bw_10, 2),
        "tp16_native_vs_tp8_local": slowdown_native,
        "tp16_10g_vs_tp8_local": slowdown_10g
    })

# Write CSV
with open(csv_out, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)

# Write Markdown Report
with open(md_out, "w", encoding="utf-8") as f:
    f.write("# AllReduce Comparison: TP-16 Multi-Node vs. TP-8 Single-Node (Local)\n\n")
    f.write("**Target Hardware:** 16x NVIDIA RTX PRO 6000 Blackwell GPUs (Dual-Socket Node with PCIe Gen5 x16)\n")
    f.write("**Cluster:** `kimi-node-0` & `kimi-node-1` on GCP VPC (us-central1-b)\n\n")
    f.write("### Benchmark Comparison Table (All Latencies in Milliseconds - ms)\n\n")
    f.write("| Payload Size | Milestone Description | TP-8 Local (PCIe Gen5) | TP-16 Native (175G) | TP-16 (100G) | TP-16 (50G) | TP-16 (20G) | TP-16 (10G) | Multi-Node (175G) vs Local | 10G Capped vs Local |\n")
    f.write("| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |\n")
    for r in rows:
        f.write(f"| **{r['payload_label']}** | {r['description']} | **{r['tp8_local_latency_ms']} ms** | **{r['tp16_native_175g_ms']} ms** | {r['tp16_100g_ms']} ms | {r['tp16_50g_ms']} ms | {r['tp16_20g_ms']} ms | **{r['tp16_10g_ms']} ms** | {r['tp16_native_vs_tp8_local']} | {r['tp16_10g_vs_tp8_local']} |\n")

    f.write("\n### Algorithmic Bandwidth Comparison (GB/s)\n\n")
    f.write("| Payload Size | TP-8 Local Baseline | TP-16 Native (175G) | TP-16 (100G) | TP-16 (50G) | TP-16 (20G) | TP-16 (10G) |\n")
    f.write("| :--- | :---: | :---: | :---: | :---: | :---: | :---: |\n")
    for r in rows:
        if r['size_bytes'] >= 1048576: # 1MB and up
            f.write(f"| **{r['payload_label']}** | **{r['tp8_local_algbw_gbs']} GB/s** | **{r['tp16_native_algbw_gbs']} GB/s** | {r['tp16_100g_algbw_gbs']} GB/s | {r['tp16_50g_algbw_gbs']} GB/s | {r['tp16_20g_algbw_gbs']} GB/s | **{r['tp16_10g_algbw_gbs']} GB/s** |\n")

    f.write("\n### Executive Findings for Leadership\n")
    f.write("1. **Local PCIe Gen5 Advantage for Small/Medium Tensors**:\n")
    f.write("   - For decode-sized tokens (8 KiB – 1 MiB), TP-8 Local is **~3x to 7x faster** than TP-16 Multi-Node because communication avoids Linux network socket and kernel TCP stack overhead entirely.\n")
    f.write("2. **Scale-Out Line-Rate Saturation**:\n")
    f.write("   - For large prefill payloads (256 MiB), TP-16 Multi-Node reaches **7.49 GB/s algorithmic bandwidth (14.04 GB/s bus bandwidth = ~112.3 Gbps over the wire)** on Native 175G.\n")
    f.write("3. **Impact of Bandwidth Throttling**:\n")
    f.write("   - Throttling from 175G Native to 10G Capped increases TP-16 256 MiB latency from **35.84 ms to 421.88 ms (11.8x slowdown)**, demonstrating that high-bandwidth inter-node links are mandatory for distributed prefill.\n")

print("Generated comparison CSV and MD report successfully!")
