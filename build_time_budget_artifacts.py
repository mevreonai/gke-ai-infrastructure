#!/usr/bin/env python3
"""
build_time_budget_artifacts.py
Creates time_budget/ directory, copies PNG charts, and writes CSV files matching §6 & §7.
"""

import os, shutil

os.makedirs("time_budget", exist_ok=True)

# Copy PNG charts into time_budget/
png_files = [
    "wall_time_budget_first_token.png",
    "wall_time_budget_first_token_under_load.png",
    "wall_time_budget_decode_token.png",
    "wall_time_budget_decode_token_under_load.png"
]

for pf in png_files:
    if os.path.exists(pf):
        shutil.copy2(pf, os.path.join("time_budget", pf))
        print(f"Copied {pf} to time_budget/{pf}")

# 1. prefill_composition_128k_by_layout.csv
prefill_comp_csv = """layout,ranks,full_attention,gemm,moe,kda,allreduce,sendrecv,other,eager_mode
TP4/PP1,1,23.4,7.8,14.3,3.2,46.0,0.0,5.2,true
TP8/PP1,1,16.2,5.1,14.6,2.2,58.0,0.0,3.9,true
TP4/PP2,8,19.5,7.0,12.5,2.9,43.8,5.5,8.8,true
TP8/PP2,15,12.5,4.2,11.9,1.7,54.8,5.1,9.9,true
TP4/PP4,16,14.7,5.3,9.5,2.2,43.1,14.9,10.2,true
TP16/PP1,12,4.8,2.1,8.9,1.1,77.6,0.0,5.4,true
TP4/PP4_512k,16,43.8,5.3,6.9,1.7,22.4,12.8,7.2,true
"""
with open("time_budget/prefill_composition_128k_by_layout.csv", "w", encoding="utf-8") as f:
    f.write(prefill_comp_csv)
print("Wrote time_budget/prefill_composition_128k_by_layout.csv")

# 2. wall_time_budget_first_token.csv
first_token_csv = """operating_point,split_source,first_token_ttft_s,queue_wait_pct,prefill_collectives_pct,pipeline_waits_pct,prefill_kernels_pct,shared_step_pct,overhead_pct
TP4/PP1 · 8K,measured,0.22,0,54,0,40,0,6
TP8/PP1 · 8K,modelled,0.26,0,57,0,37,0,6
TP4/PP1 · 128K,measured,4.53,0,42,0,54,0,4
TP8/PP1 · 128K,measured,4.81,0,50,0,46,0,4
TP4/PP2 · 128K,measured,2.65,0,41,5,47,0,7
TP8/PP2 · 128K,measured,2.79,0,51,5,37,0,7
TP4/PP4 · 128K,measured,1.71,0,38,13,37,0,11
TP16/PP1 · 128K,measured,6.42,0,75,0,22,0,3
TP4/PP1 · 512K,modelled,31.92,0,24,0,74,0,2
TP8/PP1 · 512K,modelled,28.09,0,34,0,63,0,3
TP4/PP2 · 512K,modelled,17.95,0,21,6,69,0,4
TP8/PP2 · 512K,modelled,15.58,0,31,6,59,0,5
TP4/PP4 · 512K,measured,10.22,0,21,12,60,0,7
TP16/PP1 · 512K,modelled,29.62,0,53,0,44,0,2
TP4/PP1 · 1M,modelled,93.25,0,16,0,83,0,1
TP8/PP1 · 1M,modelled,74.69,0,25,0,74,0,2
TP4/PP2 · 1M,modelled,52.53,0,14,5,78,0,3
TP8/PP2 · 1M,modelled,41.51,0,22,5,69,0,3
TP4/PP4 · 1M,modelled,28.57,0,21,12,61,0,5
TP16/PP1 · 1M,modelled,68.20,0,44,0,54,0,2
TP4/PP1 · 8K · open loop 1.0x,measured,0.98,26,12,0,9,36,17
TP4/PP1 · 8K · c32,measured,1.62,48,7,0,5,25,14
TP4/PP1 · 128K · c4,measured,10.31,50,19,0,24,5,3
TP4/PP1 · 1M · c4,modelled,231.27,58,6,0,33,1,2
"""
with open("time_budget/wall_time_budget_first_token.csv", "w", encoding="utf-8") as f:
    f.write(first_token_csv)
print("Wrote time_budget/wall_time_budget_first_token.csv")

# 3. wall_time_budget_decode_token.csv
decode_token_csv = """operating_point,split_source,decode_tpot_ms,collectives_ar_pct,pipeline_hops_pct,memory_floor_pct,kernels_above_floor_pct,waiting_behind_prefills_pct
TP4/PP1 · 8K,measured,4.5,24,0,21,55,0
TP8/PP1 · 8K,measured,6.4,52,0,8,41,0
TP4/PP1 · 128K,modelled,5.1,21,0,30,49,0
TP8/PP1 · 128K,modelled,7.1,46,0,15,39,0
TP4/PP2 · 128K,modelled,5.5,19,7,27,46,0
TP8/PP2 · 128K,modelled,7.5,44,6,14,36,0
TP4/PP4 · 128K,modelled,5.6,19,9,27,45,0
TP16/PP1 · 128K,modelled,14.9,77,0,6,18,0
TP4/PP1 · 512K,modelled,7.6,14,0,44,41,0
TP8/PP1 · 512K,modelled,9.5,35,0,31,34,0
TP4/PP2 · 512K,modelled,7.9,14,4,43,40,0
TP8/PP2 · 512K,modelled,9.9,33,4,29,33,0
TP4/PP4 · 512K,modelled,8.0,14,6,43,37,0
TP16/PP1 · 512K,modelled,17.5,65,0,13,22,0
TP4/PP1 · 1M,modelled,10.2,10,0,54,36,0
TP8/PP1 · 1M,modelled,12.1,27,0,43,30,0
TP4/PP2 · 1M,modelled,10.5,10,3,53,34,0
TP8/PP2 · 1M,modelled,12.5,26,3,41,30,0
TP4/PP4 · 1M,modelled,10.7,10,5,52,33,0
TP16/PP1 · 1M,modelled,20.1,57,0,23,20,0
TP4/PP1 · 8K · open loop 1.0x,measured,23.1,5,0,4,11,80
TP4/PP1 · 8K · c32,measured,34.5,3,0,3,7,87
TP4/PP1 · 128K · c4,measured,141.3,1,0,1,2,96
TP4/PP1 · 1M · c4,modelled,267.4,1,0,2,2,95
"""
with open("time_budget/wall_time_budget_decode_token.csv", "w", encoding="utf-8") as f:
    f.write(decode_token_csv)
print("Wrote time_budget/wall_time_budget_decode_token.csv")
