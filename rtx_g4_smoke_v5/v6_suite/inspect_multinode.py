import glob
import json
import os

print("Processing multi-node benchmark manifests...")
files = sorted(glob.glob("rtx_g4_smoke_v5/v6_suite/results/multi_node/*/vllm_surrogate_manifest.json"))
print(f"Found {len(files)} manifests:")

all_cases = []
for p in files:
    with open(p, "r", encoding="utf-8") as f:
        data = json.load(f)
    for c in data.get("cases", []):
        all_cases.append(c)
        print(f"\n==========================================")
        print(f"Case Name: {c.get('name')}")
        print(f"Server Exit Code: {c.get('server_exit_code')}")
        print(f"TP: {c.get('tp')} | PP: {c.get('pp')} | GPUs: {c.get('gpu_count', 'N/A')}")
        if c.get("error"):
            print(f"Error: {c.get('error')}")
        benchmarks = c.get("benchmarks", [])
        print(f"Total benchmarks: {len(benchmarks)}")
        for b in benchmarks:
            status = b.get("status")
            name = b.get("name")
            in_len = b.get("input_len")
            out_len = b.get("output_len")
            ttft = b.get("ttft_mean_ms")
            tpot = b.get("tpot_mean_ms")
            rps = b.get("request_throughput")
            tps = b.get("output_throughput")
            preempt = b.get("preemptions")
            print(f"  -> {name} [{status}]: In={in_len}, Out={out_len} | TTFT={ttft} ms | TPOT={tpot} ms | Throughput={tps} tok/s | Preemptions={preempt}")

print("\nSummary complete.")
