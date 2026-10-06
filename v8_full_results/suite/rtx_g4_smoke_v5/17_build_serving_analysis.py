#!/usr/bin/env python3
"""Build decision-oriented analysis tables from summarized V5 data without inventing winners or SLOs."""
from __future__ import annotations
import argparse, json, math
from pathlib import Path

def ok(r): return r.get("bench_exit_code") in (0,"0") and r.get("status") not in ("FAILED","SKIPPED_BY_SAFETY_GATE","WARMUP_FAILED")
def num(v):
    try: return float(v)
    except Exception: return None

def ratio(a,b):
    a=num(a); b=num(b); return (a/b) if a is not None and b not in (None,0) else None

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("summary_json"); ap.add_argument("--out",default="serving_analysis"); args=ap.parse_args()
    rows=json.loads(Path(args.summary_json).read_text()); out=Path(args.out); out.mkdir(parents=True,exist_ok=True)
    valid=[r for r in rows if ok(r)]
    analysis={"coverage":{"rows_total":len(rows),"rows_successful":len(valid)},"tp4_vs_tp8":[],"chunking":[],"closed_loop":{},"open_loop":{},"prefix":[],"warnings":[]}

    # Matched TP4/TP8 by bench name and requested input/concurrency in qualification/baseline families.
    for a in valid:
        if int(a.get("tp") or 0)!=4: continue
        for b in valid:
            if int(b.get("tp") or 0)!=8: continue
            if a.get("bench")==b.get("bench") and a.get("requested_input_tokens")==b.get("requested_input_tokens") and a.get("concurrency")==b.get("concurrency"):
                if ("qualification" in str(a.get("groups")) and "qualification" in str(b.get("groups"))) or ("baseline" in str(a.get("groups")) and "baseline" in str(b.get("groups"))):
                    analysis["tp4_vs_tp8"].append({"bench":a.get("bench"),"input":a.get("requested_input_tokens"),"concurrency":a.get("concurrency"),
                        "ttft_tp4_ms":a.get("mean_ttft_ms"),"ttft_tp8_ms":b.get("mean_ttft_ms"),"ttft_tp8_over_tp4":ratio(b.get("mean_ttft_ms"),a.get("mean_ttft_ms")),
                        "tpot_tp4_ms":a.get("mean_tpot_ms"),"tpot_tp8_ms":b.get("mean_tpot_ms"),"tpot_tp8_over_tp4":ratio(b.get("mean_tpot_ms"),a.get("mean_tpot_ms")),
                        "out_tok_s_tp4":a.get("output_throughput"),"out_tok_s_tp8":b.get("output_throughput"),"throughput_tp8_over_tp4":ratio(b.get("output_throughput"),a.get("output_throughput"))})

    for r in valid:
        groups=str(r.get("groups") or "")
        if "chunking" in groups:
            analysis["chunking"].append({k:r.get(k) for k in ("case","bench","max_num_batched_tokens","requested_input_tokens","concurrency","mean_ttft_ms","mean_tpot_ms","output_throughput","peak_kv_usage","preemptions_delta")})
        if "closed_loop" in groups:
            key=str(r.get("requested_input_tokens")); analysis["closed_loop"].setdefault(key,[]).append({k:r.get(k) for k in ("bench","concurrency","request_throughput","output_throughput","mean_ttft_ms","mean_tpot_ms","peak_waiting","peak_kv_usage","preemptions_delta")})
        if "open_loop" in groups:
            key=str(r.get("requested_input_tokens")); analysis["open_loop"].setdefault(key,[]).append({k:r.get(k) for k in ("bench","request_rate","concurrency","request_throughput","output_throughput","mean_ttft_ms","mean_tpot_ms","queue_mean_s_from_hist","peak_waiting","peak_kv_usage","preemptions_delta")})
        if "prefix_cache" in groups:
            analysis["prefix"].append({k:r.get(k) for k in ("case","bench","prefix_first_ttft_ms","prefix_repeat_ttft_median_ms","prefix_hits_delta","prefix_queries_delta","peak_kv_usage")})

    for k in analysis["closed_loop"]: analysis["closed_loop"][k].sort(key=lambda x:int(x.get("concurrency") or 0))
    for k in analysis["open_loop"]: analysis["open_loop"][k].sort(key=lambda x:float(x.get("request_rate") or 0) if str(x.get("request_rate"))!="inf" else math.inf)
    (out/"serving_analysis.json").write_text(json.dumps(analysis,indent=2))

    md=["# V5 RTX PRO 6000 serving analysis","","> MEASURED-48B surrogate. No absolute K3 extrapolation.","",
        "## What this analysis can answer","- TP4 vs TP8 matched runtime deltas","- chunk-size tradeoffs","- closed-loop batching frontier","- open-loop queueing/capacity behavior when generated-load tests are run","- prefix cold-vs-repeat behavior","",
        "## TP4 vs TP8 matched points","","| Input | C | TTFT TP8/TP4 | TPOT TP8/TP4 | Throughput TP8/TP4 |","|---:|---:|---:|---:|---:|"]
    def f(v):
        try:return f"{float(v):.3f}"
        except:return ""
    for x in analysis["tp4_vs_tp8"]: md.append(f"| {x['input']} | {x['concurrency']} | {f(x['ttft_tp8_over_tp4'])} | {f(x['tpot_tp8_over_tp4'])} | {f(x['throughput_tp8_over_tp4'])} |")
    md += ["","## Closed-loop concurrency frontier","","This is a backlog/saturation test, not a production user-arrival model. Generate open-loop cases with `13_generate_load_cases.py` before claiming a capacity knee."]
    for ctx,pts in analysis["closed_loop"].items():
        md += ["",f"### Context {ctx}","| C | Req/s | Out tok/s | TTFT ms | TPOT ms | Wait peak | KV peak | Preempt |","|---:|---:|---:|---:|---:|---:|---:|---:|"]
        for x in pts: md.append(f"| {x.get('concurrency')} | {f(x.get('request_throughput'))} | {f(x.get('output_throughput'))} | {f(x.get('mean_ttft_ms'))} | {f(x.get('mean_tpot_ms'))} | {f(x.get('peak_waiting'))} | {f(x.get('peak_kv_usage'))} | {f(x.get('preemptions_delta'))} |")
    (out/"SERVING_ANALYSIS.md").write_text("\n".join(md)+"\n"); print(f"Wrote {out}")
if __name__=="__main__": main()
