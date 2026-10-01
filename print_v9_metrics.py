import json
from pathlib import Path

def main():
    p = Path("c:/Users/ayu23/OneDrive/Desktop/tpu/v9_full_result/final_validation/combined_vllm_runs.json")
    runs = json.loads(p.read_text(encoding="utf-8"))
    
    print("=== SCALE-OUT tp8_pp2_dist BENCHMARKS ===")
    for r in runs:
        if r.get("case") == "tp8_pp2_dist":
            print(f"Bench: {r.get('bench'):<12} | Status: {r.get('status')} | Input: {r.get('context_tokens', r.get('actual_input_mean')):<7} | TTFT: {r.get('mean_ttft_ms', 0):.2f} ms | TPOT: {r.get('mean_tpot_ms', 0):.2f} ms | Out tok/s: {r.get('output_throughput', 0):.2f} | Peak KV: {r.get('peak_kv_usage', 0)*100:.2f}%")
            
    print("\n=== SINGLE NODE tp4_context_baseline BENCHMARKS ===")
    for r in runs:
        if r.get("case") == "tp4_context_baseline":
            print(f"Bench: {r.get('bench'):<12} | Status: {r.get('status')} | Input: {r.get('context_tokens', r.get('actual_input_mean')):<7} | TTFT: {r.get('mean_ttft_ms', 0):.2f} ms | TPOT: {r.get('mean_tpot_ms', 0):.2f} ms | Out tok/s: {r.get('output_throughput', 0):.2f} | Peak KV: {r.get('peak_kv_usage', 0)*100:.2f}%")

if __name__ == "__main__":
    main()
