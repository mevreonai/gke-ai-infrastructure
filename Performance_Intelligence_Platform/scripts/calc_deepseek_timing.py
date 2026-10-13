import os
import json

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
metrics_file = os.path.join(base_dir, "data", "results", "moonshotai_Kimi-Linear-48B-A3B-Instruct", "extracted_dashboard_metrics.json")
if not os.path.exists(metrics_file):
    metrics_file = os.path.join(base_dir, "data", "results", "extracted_dashboard_metrics.json")

with open(metrics_file, "r", encoding="utf-8") as f:
    kimi_runs = json.load(f)

print("Kimi 48B empirical timings vs DeepSeek-V4.1-Flash projections:")
print(f"{'Case':10s} | {'Context':7s} | {'C':3s} | {'Prompts':7s} | {'Kimi Dur (s)':12s} | {'DS Proj Dur (s)':15s} | {'DS Factor':9s}")
print("-" * 75)

total_kimi = 0
total_ds = 0

ds_cases = []

for r in kimi_runs:
    b = r["bench"]
    ctx = r["context_category"]
    c = r["concurrency"]
    prompts = r["completed"]
    kimi_dur = r["duration_s"]
    total_kimi += kimi_dur
    
    # DeepSeek-V4.1-Flash projection factors:
    # 1. 40 layers vs 27 layers (1.48x layer depth)
    # 2. 384 routed MoE experts with MLA (Multi-Head Latent Attention) vs Linear Attention
    # 3. Inter-node PP boundary transfers over 20G: 40 layers (split 10,10,10,10) has similar pipeline stages (4 stages)
    #    but slightly higher activation dimensions (d_model = 5120/7168 vs 4096).
    # 4. Prefill compute factor: ~2.2x to 2.8x (quadratic MLA chunked vs pure linear state update)
    # 5. Decode compute factor: ~2.5x to 3.0x (14-16ms/tok vs 5.4ms/tok)
    
    if ctx == "1K":
        # Short context: decode dominated or small prefill
        factor = 2.4
    elif ctx == "8K":
        factor = 2.5
    elif ctx == "128K":
        # Mixed prefill & decode
        factor = 2.6
    elif ctx == "512K":
        # Heavy chunked prefill
        factor = 2.7
    elif ctx == "1M":
        # 1M prefill with 40 layers and MLA
        factor = 2.8
        
    ds_dur = round(kimi_dur * factor, 1)
    total_ds += ds_dur
    
    ds_cases.append({
        "bench": b,
        "ctx": ctx,
        "c": c,
        "prompts": prompts,
        "kimi_dur": kimi_dur,
        "ds_dur": ds_dur,
        "factor": factor
    })
    
    print(f"{b:10s} | {ctx:7s} | c{c:<2d} | {prompts:<7d} | {kimi_dur:<12.1f} | {ds_dur:<15.1f} | {factor:.1f}x")

print("-" * 75)
print(f"Total Workload Active Time: Kimi = {total_kimi/60:.2f} min ({total_kimi:.1f}s) | DeepSeek = {total_ds/60:.2f} min ({total_ds:.1f}s)")
print()
print("Wall-Clock Overhead Estimates:")
print("1. Model Weight Loading & Initialization:")
print("   - Kimi 48B (~90 GB weights): ~1.6 min (96s)")
print("   - DeepSeek-V4.1-Flash (475 GB weights): ~6 to 8 min (400-480s)")
print("2. Warmup Prompts & Ray Handshakes:")
print("   - Kimi 48B: ~10 min")
print("   - DeepSeek-V4.1-Flash: ~18 to 22 min")
print("3. Full 16-Case Wall-Clock Run Total:")
print(f"   - Kimi 48B Total Wall-Clock: ~26.8 min")
print(f"   - DeepSeek-V4.1-Flash Total Wall-Clock: ~65 to 75 min (~1.1 to 1.25 hours)")
