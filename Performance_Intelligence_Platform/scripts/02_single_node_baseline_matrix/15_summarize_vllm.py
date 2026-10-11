#!/usr/bin/env python3
"""Aggregate V5 runs conservatively.
- Missing metrics remain None / NOT_CAPTURED.
- Validates actual input lengths from detailed JSON.
- Suppresses reliability claims for p95 when N<20 and p99 when N<100.
- Separates local/remote GPU telemetry.
"""
from __future__ import annotations
import argparse, csv, json, math, statistics
from pathlib import Path

def load_jsonl(p):
    out=[]
    if not p.exists(): return out
    for line in p.read_text(errors="ignore").splitlines():
        try: out.append(json.loads(line))
        except Exception: pass
    return out

def prom_snaps(recs): return [x for x in recs if x.get("kind")=="prometheus"]
def gpu_snaps(recs): return [x for x in recs if x.get("kind")=="gpu"]

def aggregate_series(snaps):
    rows=[]
    for s in snaps:
        d={"ts":s.get("ts")}; by={}
        for m in s.get("metrics",[]): by.setdefault(m.get("name"),[]).append(float(m.get("value",0)))
        for n,vs in by.items():
            if n in ("vllm:kv_cache_usage_perc","vllm:num_requests_running","vllm:num_requests_waiting"): d[n]=max(vs)
            else: d[n]=sum(vs)
        rows.append(d)
    return rows

def vals(series,name): return [r[name] for r in series if name in r and isinstance(r[name],(int,float)) and math.isfinite(r[name])]
def delta(series,name):
    x=vals(series,name); return x[-1]-x[0] if len(x)>=2 else None
def peak(series,name):
    x=vals(series,name); return max(x) if x else None
def mean_series(series,name):
    x=vals(series,name); return statistics.mean(x) if x else None
def hist_mean_delta(series,stem):
    s=delta(series,stem+"_sum"); c=delta(series,stem+"_count"); return s/c if s is not None and c not in (None,0) else None

def metric_delta_any(series,names):
    for n in names:
        x=delta(series,n)
        if x is not None: return x,n
    return None,None

def gpu_stats(snaps):
    by_node={}
    for s in snaps:
        node=s.get("node","unknown")
        z=by_node.setdefault(node,{"util":[],"memutil":[],"mem":[],"power":[],"clock":[]})
        for g in s.get("gpus",[]):
            if "error" in g: continue
            for dst,key in (("util","utilization.gpu"),("memutil","utilization.memory"),("mem","memory.used"),("power","power.draw"),("clock","clocks.sm")):
                try: z[dst].append(float(g[key]))
                except Exception: pass
    out={}
    for node,z in by_node.items():
        out[node]={
          "gpu_util_mean_pct":statistics.mean(z["util"]) if z["util"] else None,
          "gpu_util_peak_pct":max(z["util"]) if z["util"] else None,
          "gpu_mem_used_peak_mb":max(z["mem"]) if z["mem"] else None,
          "gpu_power_mean_w":statistics.mean(z["power"]) if z["power"] else None,
          "gpu_sm_clock_mean_mhz":statistics.mean(z["clock"]) if z["clock"] else None,
          "gpu_samples":len(z["util"])
        }
    return out

def parse_bench(p):
    if not p.exists(): return {"result_missing":True}
    try: d=json.loads(p.read_text())
    except Exception as e: return {"parse_error":repr(e)}
    keep={k:v for k,v in d.items() if k in {
      "duration","completed","failed","total_input_tokens","total_output_tokens","request_throughput","output_throughput","total_token_throughput",
      "mean_ttft_ms","median_ttft_ms","p50_ttft_ms","p95_ttft_ms","p99_ttft_ms","mean_tpot_ms","median_tpot_ms","p50_tpot_ms","p95_tpot_ms","p99_tpot_ms",
      "mean_itl_ms","median_itl_ms","p50_itl_ms","p95_itl_ms","p99_itl_ms","mean_e2el_ms","median_e2el_ms","p50_e2el_ms","p95_e2el_ms","p99_e2el_ms",
      "ttfts","input_lens","output_lens","errors","probe_metrics","goodput"}}
    return keep

def pct_rel(n): return {"p95_reliable": n is not None and n>=20, "p99_reliable": n is not None and n>=100}

def write_csv(path,rows):
    if not rows: path.write_text(""); return
    keys=[]
    for r in rows:
        for k in r:
            if k not in keys: keys.append(k)
    with path.open("w",newline="") as f: w=csv.DictWriter(f,fieldnames=keys); w.writeheader(); w.writerows(rows)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("root",type=Path); ap.add_argument("--out",type=Path,default=None); args=ap.parse_args()
    root=args.root.resolve(); out=(args.out or root/"summary_v6").resolve(); out.mkdir(parents=True,exist_ok=True)
    manifests=list(root.rglob("case_manifest.json")); rows=[]; coverage=[]
    for mp in manifests:
        try: case=json.loads(mp.read_text())
        except Exception: continue
        for b in case.get("benchmarks",[]):
            bdir=mp.parent/b["name"]; result_path=Path(b.get("result_json",bdir/f"{b['name']}.json"))
            bench=parse_bench(result_path)
            recs=[]
            for fn in ("metrics_gpu.jsonl","metrics_node0.jsonl","metrics_node1.jsonl"):
                recs += load_jsonl(bdir/fn)
            ps=prom_snaps(recs); gs=gpu_snaps(recs); series=aggregate_series(ps); gstats=gpu_stats(gs)
            completed=bench.get("completed")
            try: completed=int(completed)
            except Exception: completed=None
            inputs=bench.get("input_lens") or []; outputs=bench.get("output_lens") or []
            pre,pre_src=metric_delta_any(series,["vllm:num_preemptions_total","vllm:num_preemptions"])
            ph,ph_src=metric_delta_any(series,["vllm:prefix_cache_hits_total","vllm:prefix_cache_hits"])
            pq,pq_src=metric_delta_any(series,["vllm:prefix_cache_queries_total","vllm:prefix_cache_queries"])
            row={
              "case":case.get("name"),"groups":";".join(case.get("groups",[])),"purpose":case.get("purpose"),"tp":case.get("tp"),"pp":case.get("pp"),
              "network_provenance":case.get("network_provenance","SINGLE_NODE_LOCAL"),"network_mode":case.get("network_mode","local"),
              "configured_network_cap_gbps":case.get("configured_network_cap_gbps",0),"nccl_transport_provenance":case.get("nccl_transport_provenance"),
              "physical_gpu_indices":json.dumps(case.get("physical_gpu_indices",case.get("physical_gpu_indices_each_node"))),
              "max_num_batched_tokens":case.get("max_num_batched_tokens"),"max_num_seqs":case.get("max_num_seqs"),"max_num_active_seqs":case.get("max_num_active_seqs"),
              "kv_cache_dtype":case.get("kv_cache_dtype"),"kv_cache_memory_bytes":case.get("kv_cache_memory_bytes"),"offload_gib_total":case.get("offload_gib_total_across_tp",case.get("offload_gib")),
              "prefix_caching":case.get("prefix_caching"),"observability_profile":case.get("observability_profile"),"bench":b.get("name"),"status":b.get("status"),
              "requested_input_tokens":b.get("input") if b.get("dataset")!="prefix_repetition" else (b.get("prefix",0)+b.get("suffix",0)),
              "requested_output_tokens":b.get("output"),"concurrency":b.get("concurrency"),"prompts_requested":b.get("prompts"),"warmups":b.get("warmups",0),
              "request_rate":b.get("request_rate","inf"),"burstiness":b.get("burstiness"),"probe_request_rate":b.get("probe_request_rate"),"bench_exit_code":b.get("exit_code"),
              "completed":completed,"failed":bench.get("failed"),"duration":bench.get("duration"),"request_throughput":bench.get("request_throughput"),"output_throughput":bench.get("output_throughput"),
              "total_token_throughput":bench.get("total_token_throughput"),"mean_ttft_ms":bench.get("mean_ttft_ms"),"p50_ttft_ms":bench.get("p50_ttft_ms"),
              "p95_ttft_ms_raw":bench.get("p95_ttft_ms"),"p99_ttft_ms_raw":bench.get("p99_ttft_ms"),"mean_tpot_ms":bench.get("mean_tpot_ms"),"p50_tpot_ms":bench.get("p50_tpot_ms"),
              "p95_tpot_ms_raw":bench.get("p95_tpot_ms"),"p99_tpot_ms_raw":bench.get("p99_tpot_ms"),"mean_itl_ms":bench.get("mean_itl_ms"),"mean_e2el_ms":bench.get("mean_e2el_ms"),
              "actual_input_min":min(inputs) if inputs else None,"actual_input_max":max(inputs) if inputs else None,"actual_input_mean":statistics.mean(inputs) if inputs else None,
              "actual_output_min":min(outputs) if outputs else None,"actual_output_max":max(outputs) if outputs else None,"actual_output_mean":statistics.mean(outputs) if outputs else None,
              "input_len_exact_match":b.get("input_len_exact_match"),"metric_samples":len(ps),"peak_kv_usage":peak(series,"vllm:kv_cache_usage_perc"),
              "peak_running":peak(series,"vllm:num_requests_running"),"peak_waiting":peak(series,"vllm:num_requests_waiting"),"mean_running":mean_series(series,"vllm:num_requests_running"),"mean_waiting":mean_series(series,"vllm:num_requests_waiting"),
              "preemptions_delta":pre,"preemptions_metric":pre_src,"prefix_hits_delta":ph,"prefix_queries_delta":pq,"prefix_hit_metric":ph_src,"prefix_query_metric":pq_src,
              "offload_bytes_delta":delta(series,"vllm:kv_offload_total_bytes"),"offload_time_delta_s":delta(series,"vllm:kv_offload_total_time"),
              "queue_mean_s_from_hist":hist_mean_delta(series,"vllm:request_queue_time_seconds"),"prefill_mean_s_from_hist":hist_mean_delta(series,"vllm:request_prefill_time_seconds"),
              "decode_mean_s_from_hist":hist_mean_delta(series,"vllm:request_decode_time_seconds"),"inference_mean_s_from_hist":hist_mean_delta(series,"vllm:request_inference_time_seconds"),
              "gpu_node_stats_json":json.dumps(gstats,sort_keys=True),"metrics_capture_status":"CAPTURED" if ps else "NOT_CAPTURED",
              **pct_rel(completed)
            }
            # Only surface p95/p99 as trustworthy columns when enough completed samples exist.
            row["p95_ttft_ms"] = bench.get("p95_ttft_ms") if row["p95_reliable"] else None
            row["p99_ttft_ms"] = bench.get("p99_ttft_ms") if row["p99_reliable"] else None
            row["p95_tpot_ms"] = bench.get("p95_tpot_ms") if row["p95_reliable"] else None
            row["p99_tpot_ms"] = bench.get("p99_tpot_ms") if row["p99_reliable"] else None
            tt=bench.get("ttfts") or []
            if b.get("dataset")=="prefix_repetition" and tt:
                row["prefix_first_ttft_ms"]=float(tt[0])*1000 if float(tt[0])<100 else float(tt[0])
                rest=[float(x)*1000 if float(x)<100 else float(x) for x in tt[1:]]
                row["prefix_repeat_ttft_median_ms"]=statistics.median(rest) if rest else None
            rows.append(row)
            coverage.append({"case":case.get("name"),"bench":b.get("name"),"status":b.get("status"),"exit":b.get("exit_code"),"result_exists":result_path.exists(),"metrics":bool(ps)})

    write_csv(out/"vllm_runs.csv",rows); (out/"vllm_runs.json").write_text(json.dumps(rows,indent=2)); (out/"coverage.json").write_text(json.dumps(coverage,indent=2))
    def f(v,d=2):
        try: return f"{float(v):.{d}f}"
        except Exception: return ""
    md=["# V5 serving summary","","> **Evidence:** MEASURED-48B surrogate. Absolute latency/tok/s are not Kimi K3 predictions.",
        "> p95 is surfaced as trustworthy only when N>=20; p99 only when N>=100. Raw percentile fields remain in JSON/CSV.","",
        "| Case | Bench | Input | C | Req/s | TTFT mean ms | TPOT mean ms | Output tok/s | KV peak | Waiting peak | Preempt Δ | Metrics |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|"]
    for r in rows:
        md.append(f"| {r['case']} | {r['bench']} | {r.get('actual_input_mean') or r.get('requested_input_tokens') or ''} | {r.get('concurrency') or ''} | {f(r.get('request_throughput'))} | {f(r.get('mean_ttft_ms'))} | {f(r.get('mean_tpot_ms'))} | {f(r.get('output_throughput'))} | {f(r.get('peak_kv_usage'),3)} | {f(r.get('peak_waiting'),0)} | {f(r.get('preemptions_delta'),0)} | {r.get('metrics_capture_status')} |")
    (out/"VLLM_SUMMARY.md").write_text("\n".join(md)+"\n"); print(f"Wrote {out}")
if __name__=="__main__": main()
