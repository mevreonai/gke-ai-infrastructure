import glob
import json
import os

topologies = ["tp4_pp2_dist", "tp8_pp2_dist", "tp4_pp4_dist", "tp16_pp1_dist"]
base_dir = "rtx_g4_smoke_v5/v6_suite/results/multi_node"

summary_rows = []

for topo in topologies:
    topo_dir = os.path.join(base_dir, topo, topo)
    if not os.path.exists(topo_dir):
        print(f"Warning: Directory not found: {topo_dir}")
        continue
    
    # Check benchmarks
    bench_dirs = sorted([d for d in os.listdir(topo_dir) if os.path.isdir(os.path.join(topo_dir, d))])
    for bname in bench_dirs:
        bpath = os.path.join(topo_dir, bname, f"{bname}.json")
        if os.path.exists(bpath):
            with open(bpath, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            num_prompts = data.get("num_prompts", 0)
            completed = data.get("completed", 0)
            failed = data.get("failed", 0)
            in_lens = data.get("input_lens", [])
            in_len = in_lens[0] if in_lens else "N/A"
            out_lens = data.get("output_lens", [])
            out_len = out_lens[0] if out_lens else "N/A"
            mean_ttft = data.get("mean_ttft_ms")
            p50_ttft = data.get("p50_ttft_ms")
            p95_ttft = data.get("p95_ttft_ms")
            p99_ttft = data.get("p99_ttft_ms")
            mean_tpot = data.get("mean_tpot_ms")
            p50_tpot = data.get("p50_tpot_ms")
            mean_itl = data.get("mean_itl_ms")
            out_throughput = data.get("output_throughput")
            tot_throughput = data.get("total_token_throughput")
            
            summary_rows.append({
                "topology": topo,
                "benchmark": bname,
                "input_len": in_len,
                "output_len": out_len,
                "completed": completed,
                "failed": failed,
                "mean_ttft_ms": mean_ttft,
                "p50_ttft_ms": p50_ttft,
                "p95_ttft_ms": p95_ttft,
                "p99_ttft_ms": p99_ttft,
                "mean_tpot_ms": mean_tpot,
                "p50_tpot_ms": p50_tpot,
                "mean_itl_ms": mean_itl,
                "output_throughput": out_throughput,
                "total_token_throughput": tot_throughput
            })

print(f"Parsed {len(summary_rows)} multi-node benchmark runs:")
print(f"{'Topology':<16} | {'Bench':<10} | {'In Len':<8} | {'TTFT (ms)':<10} | {'TPOT (ms)':<10} | {'Throughput':<12}")
print("-" * 75)
for r in summary_rows:
    ttft_str = f"{r['mean_ttft_ms']:.1f}" if r['mean_ttft_ms'] is not None else "N/A"
    tpot_str = f"{r['mean_tpot_ms']:.2f}" if r['mean_tpot_ms'] is not None else "N/A"
    tps_str = f"{r['output_throughput']:.1f} tok/s" if r['output_throughput'] is not None else "N/A"
    print(f"{r['topology']:<16} | {r['benchmark']:<10} | {str(r['input_len']):<8} | {ttft_str:<10} | {tpot_str:<10} | {tps_str:<12}")

# Write to markdown and CSV
md_path = "rtx_g4_smoke_v5/v6_suite/results/MULTI_NODE_SUMMARY.md"
with open(md_path, "w", encoding="utf-8") as f:
    f.write("# V6 Multi-Node (16 x RTX 6000 Ada) Distributed Benchmark Results\n\n")
    f.write("Evaluation of `moonshotai/Kimi-Linear-48B-A3B-Instruct` across 2 nodes (8x RTX 6000 Ada each, 16 GPUs total) interconnected via GCP VPC.\n\n")
    f.write("## Empirical Benchmark Table\n\n")
    f.write("| Topology | Benchmark | In Len | Out Len | Completed | Mean TTFT (ms) | P50 TTFT (ms) | P95 TTFT (ms) | Mean TPOT (ms) | Output Throughput (tok/s) | Total Tok/s |\n")
    f.write("|---|---|---|---|---|---|---|---|---|---|---|\n")
    for r in summary_rows:
        f.write(f"| `{r['topology']}` | `{r['benchmark']}` | {r['input_len']} | {r['output_len']} | {r['completed']}/{r['completed']+r['failed']} | {r['mean_ttft_ms']:.2f} | {r['p50_ttft_ms']:.2f} | {r['p95_ttft_ms']:.2f} | {r['mean_tpot_ms']:.2f} | {r['output_throughput']:.2f} | {r['total_token_throughput']:.2f} |\n")

print(f"\nWritten to {md_path}")
