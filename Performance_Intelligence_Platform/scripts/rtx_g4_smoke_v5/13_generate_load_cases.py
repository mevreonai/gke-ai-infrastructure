#!/usr/bin/env python3
"""Generate evidence-based open-loop load cases from measured closed-loop throughput.
No absolute RPS is invented: rates are fractions of the highest measured successful request throughput for each context.
"""
from __future__ import annotations
import argparse, json, math
from pathlib import Path

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--summary-json",required=True,help="vllm_runs.json from 15_summarize_vllm.py")
    ap.add_argument("--base-cases",default=str(Path(__file__).with_name("10_vllm_surrogate_cases.json")))
    ap.add_argument("--out",default="10c_vllm_generated_load_cases.json")
    ap.add_argument("--contexts",default="8192,131072")
    ap.add_argument("--fractions",default="0.25,0.5,0.75,0.9,1.0,1.1,1.25")
    ap.add_argument("--burstiness",type=float,default=1.0)
    ap.add_argument("--target-seconds",type=float,default=60.0)
    ap.add_argument("--include-probe",action="store_true",help="Add one long-prefill interference case if 512K baseline exists.")
    args=ap.parse_args()
    rows=json.loads(Path(args.summary_json).read_text()); base=json.loads(Path(args.base_cases).read_text())
    contexts=[int(x) for x in args.contexts.split(',') if x.strip()]; fracs=[float(x) for x in args.fractions.split(',') if x.strip()]
    best={}
    for r in rows:
        if r.get("bench_exit_code") not in (0,"0"): continue
        n=r.get("actual_input_mean") or r.get("input_tokens")
        try: n=int(round(float(n)))
        except Exception: continue
        rt=r.get("request_throughput")
        try: rt=float(rt)
        except Exception: continue
        if rt>best.get(n,0): best[n]=rt
    cases=[]
    for n in contexts:
        if n not in best:
            print(f"WARN: no successful measured request throughput for context={n}; skipping")
            continue
        cap=best[n]
        maxseq=64 if n<=8192 else 32 if n<=131072 else 8
        maxconc=maxseq
        benches=[]
        for f in fracs:
            rate=cap*f; prompts=max(24,min(512,int(math.ceil(rate*args.target_seconds))))
            benches.append({"name":f"rps_{f:.2f}x","input":n,"output":256 if n<=131072 else 64,"concurrency":maxconc,
                            "prompts":prompts,"warmups":0,"request_rate":round(rate,6),"burstiness":args.burstiness,
                            "rate_basis_request_throughput":cap,"rate_fraction":f})
        cases.append({"name":f"tp4_openloop_{n}","groups":["open_loop","generated_load"],
                      "purpose":"Open-loop Poisson/gamma arrival sweep derived from measured closed-loop service rate; not an absolute capacity claim.",
                      "tp":4,"pp":1,"gpu_indices":[0,1,2,3],"max_num_batched_tokens":8192,"max_num_seqs":maxseq,
                      "prefix_caching":False,"offload_gib":0,"benchmarks":benches})
    if args.include_probe and 524288 in best and 8192 in best:
        main_rate=best[524288]*0.5; probe_rate=best[8192]*0.05
        cases.append({"name":"tp4_512k_interference_probe","groups":["open_loop","interference"],
                      "purpose":"Long-prefill main load plus low-rate single-token probe traffic; rates derived from measured service rates.",
                      "tp":4,"pp":1,"gpu_indices":[0,1,2,3],"max_num_batched_tokens":8192,"max_num_seqs":16,
                      "prefix_caching":False,"offload_gib":0,"benchmarks":[{
                        "name":"512k_main_plus_probe","input":524288,"output":32,"concurrency":16,"prompts":max(8,int(math.ceil(main_rate*args.target_seconds))),
                        "warmups":0,"request_rate":round(main_rate,6),"burstiness":1.0,"probe_request_rate":round(probe_rate,6),
                        "main_rate_basis":best[524288],"probe_rate_basis_8k":best[8192]}]})
    out={k:v for k,v in base.items() if k!="cases"}; out["generated_from_summary"]=str(Path(args.summary_json).resolve()); out["cases"]=cases
    Path(args.out).write_text(json.dumps(out,indent=2)); print(f"Wrote {args.out} with {len(cases)} cases")
if __name__=="__main__": main()
