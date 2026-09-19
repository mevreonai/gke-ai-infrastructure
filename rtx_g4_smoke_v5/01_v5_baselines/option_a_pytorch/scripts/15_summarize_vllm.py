#!/usr/bin/env python3
"""
Summarize V5 Kimi-Linear surrogate data.

Rules:
- Per-benchmark metrics are sampled in an isolated time window.
- Missing metrics stay missing.
- Absolute 48B latency/tokens/s are never converted to K3 estimates.
"""
from __future__ import annotations
import argparse, csv, json, math, statistics
from pathlib import Path

def load_jsonl(p: Path):
    out=[]
    if not p.exists(): return out
    for line in p.read_text(errors="ignore").splitlines():
        try: out.append(json.loads(line))
        except Exception: pass
    return out

def prom_snaps(recs):
    return [x for x in recs if x.get("kind")=="prometheus"]

def gpu_snaps(recs):
    return [x for x in recs if x.get("kind")=="gpu"]

def aggregate_series(snaps,names):
    rows=[]
    for s in snaps:
        d={"ts":s["ts"]}
        by={}
        for m in s.get("metrics",[]):
            n=m.get("name")
            if n in names:
                by.setdefault(n,[]).append(float(m["value"]))
        for n,vs in by.items():
            if any(x in n for x in ("usage_perc","num_requests_running","num_requests_waiting")):
                d[n]=max(vs)
            else:
                d[n]=sum(vs)
        rows.append(d)
    return rows

def vals(series,name):
    return [r[name] for r in series if name in r and math.isfinite(r[name])]

def delta(series,name):
    x=vals(series,name)
    return x[-1]-x[0] if len(x)>=2 else None

def peak(series,name):
    x=vals(series,name); return max(x) if x else None

def hist_mean_delta(series,stem):
    s=delta(series,stem+"_sum"); c=delta(series,stem+"_count")
    return s/c if s is not None and c not in (None,0) else None

def labeled_counter_delta(snaps,name,label_key=None,label_value=None):
    seq=[]
    for s in snaps:
        total=0.0; found=False
        for m in s.get("metrics",[]):
            if m.get("name")!=name: continue
            labels=m.get("labels",{})
            if label_key is not None and labels.get(label_key)!=label_value: continue
            total+=float(m["value"]); found=True
        if found: seq.append(total)
    return seq[-1]-seq[0] if len(seq)>=2 else None

def gpu_stats(snaps):
    gu=[]; mu=[]; mem=[]; power=[]; smclk=[]
    for s in snaps:
        for g in s.get("gpus",[]):
            if "error" in g: continue
            def add(dst,key):
                try: dst.append(float(g[key]))
                except Exception: pass
            add(gu,"utilization.gpu"); add(mu,"utilization.memory")
            add(mem,"memory.used"); add(power,"power.draw"); add(smclk,"clocks.sm")
    def mean(x): return statistics.mean(x) if x else None
    def p95(x):
        if not x: return None
        y=sorted(x); return y[min(len(y)-1, max(0, math.ceil(.95*len(y))-1))]
    return {
        "gpu_util_mean_pct":mean(gu),"gpu_util_p95_pct":p95(gu),
        "gpu_mem_util_mean_pct":mean(mu),
        "gpu_mem_used_peak_mb":max(mem) if mem else None,
        "gpu_power_mean_w":mean(power),"gpu_sm_clock_mean_mhz":mean(smclk)
    }

def parse_bench(p:Path):
    try: d=json.loads(p.read_text())
    except Exception as e: return {"parse_error":repr(e)}
    keep={}
    for k,v in d.items():
        if k in {
            "duration","completed","failed","total_input_tokens","total_output_tokens",
            "request_throughput","output_throughput","total_token_throughput",
            "mean_ttft_ms","median_ttft_ms","p50_ttft_ms","p95_ttft_ms","p99_ttft_ms",
            "mean_tpot_ms","median_tpot_ms","p50_tpot_ms","p95_tpot_ms","p99_tpot_ms",
            "mean_itl_ms","median_itl_ms","p50_itl_ms","p95_itl_ms","p99_itl_ms",
            "mean_e2el_ms","median_e2el_ms","p50_e2el_ms","p95_e2el_ms","p99_e2el_ms",
            "ttfts","input_lens","output_lens","errors"
        }:
            keep[k]=v
    return keep

def write_csv(path,rows):
    if not rows: path.write_text(""); return
    keys=[]
    for r in rows:
        for k in r:
            if k not in keys: keys.append(k)
    with path.open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=keys); w.writeheader(); w.writerows(rows)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("root",type=Path)
    ap.add_argument("--out",type=Path,default=None)
    args=ap.parse_args()
    root=args.root.resolve()
    out=(args.out or root/"summary_v5").resolve(); out.mkdir(parents=True,exist_ok=True)
    
    manifest_paths = list(root.rglob("vllm_surrogate_manifest.json"))
    all_cases = []
    for mp in manifest_paths:
        try:
            m = json.loads(mp.read_text())
            for case in m.get("cases", []):
                case["_base_dir"] = str(mp.parent)
                all_cases.append(case)
        except Exception:
            pass

    names={
      "vllm:kv_cache_usage_perc","vllm:num_requests_running","vllm:num_requests_waiting",
      "vllm:num_preemptions_total","vllm:num_preemptions",
      "vllm:prefix_cache_hits_total","vllm:prefix_cache_hits",
      "vllm:prefix_cache_queries_total","vllm:prefix_cache_queries",
      "vllm:prompt_tokens_total","vllm:prompt_tokens",
      "vllm:generation_tokens_total","vllm:generation_tokens",
      "vllm:prompt_tokens_cached_total","vllm:prompt_tokens_cached",
      "vllm:kv_offload_total_bytes","vllm:kv_offload_total_time",
      "vllm:kv_offload_load_bytes_total","vllm:kv_offload_store_bytes_total",
      "vllm:request_queue_time_seconds_sum","vllm:request_queue_time_seconds_count",
      "vllm:request_prefill_time_seconds_sum","vllm:request_prefill_time_seconds_count",
      "vllm:request_decode_time_seconds_sum","vllm:request_decode_time_seconds_count",
      "vllm:request_inference_time_seconds_sum","vllm:request_inference_time_seconds_count",
      "vllm:request_num_preemptions_sum","vllm:request_num_preemptions_count",
      "vllm:request_prefill_kv_computed_tokens_sum","vllm:request_prefill_kv_computed_tokens_count",
      "vllm:estimated_flops_per_gpu_total","vllm:estimated_read_bytes_per_gpu_total",
      "vllm:estimated_write_bytes_per_gpu_total",
    }
    rows=[]
    for case in all_cases:
        for b in case.get("benchmarks",[]):
            bdir=Path(case["_base_dir"])/case["name"]/b["name"]
            recs=load_jsonl(bdir/"metrics_gpu.jsonl")
            ps=prom_snaps(recs); gs=gpu_snaps(recs); series=aggregate_series(ps,names)
            bench=parse_bench(Path(b["result_json"]))
            pre=delta(series,"vllm:num_preemptions_total")
            if pre is None: pre=delta(series,"vllm:num_preemptions")
            ph=delta(series,"vllm:prefix_cache_hits_total")
            if ph is None: ph=delta(series,"vllm:prefix_cache_hits")
            pq=delta(series,"vllm:prefix_cache_queries_total")
            if pq is None: pq=delta(series,"vllm:prefix_cache_queries")

            row={
              "case":case["name"],"purpose":case.get("purpose"),
              "transferability":case.get("transferability"),
              "tp":case.get("tp"),"pp":case.get("pp"),
              "max_num_batched_tokens":case.get("max_num_batched_tokens"),
              "prefix_caching":case.get("prefix_caching"),
              "offload_gib":case.get("offload_gib"),
              "kv_cache_memory_bytes":case.get("kv_cache_memory_bytes"),
              "bench":b["name"],"input_tokens":b["input"]+b.get("prefix",0),
              "prefix_tokens":b.get("prefix",0),"output_tokens_requested":b["output"],
              "concurrency":b["concurrency"],"prompts":b["prompts"],
              "warmups":b.get("warmups",1),"bench_exit_code":b["exit_code"],
              **{k:v for k,v in bench.items() if k not in ("ttfts","input_lens","output_lens","errors")},
              "ttfts_s_detail_json":json.dumps(bench.get("ttfts")),
              "peak_kv_usage":peak(series,"vllm:kv_cache_usage_perc"),
              "peak_running":peak(series,"vllm:num_requests_running"),
              "peak_waiting":peak(series,"vllm:num_requests_waiting"),
              "preemptions_delta":pre,"prefix_hits_delta":ph,"prefix_queries_delta":pq,
              "offload_bytes_delta":delta(series,"vllm:kv_offload_total_bytes"),
              "offload_time_delta_s":delta(series,"vllm:kv_offload_total_time"),
              "offload_load_bytes_delta":labeled_counter_delta(ps,"vllm:kv_offload_total_bytes","transfer_type","load"),
              "offload_store_bytes_delta":labeled_counter_delta(ps,"vllm:kv_offload_total_bytes","transfer_type","store"),
              "queue_mean_s_from_hist":hist_mean_delta(series,"vllm:request_queue_time_seconds"),
              "prefill_mean_s_from_hist":hist_mean_delta(series,"vllm:request_prefill_time_seconds"),
              "decode_mean_s_from_hist":hist_mean_delta(series,"vllm:request_decode_time_seconds"),
              "inference_mean_s_from_hist":hist_mean_delta(series,"vllm:request_inference_time_seconds"),
              "prefill_kv_computed_tokens_mean":hist_mean_delta(series,"vllm:request_prefill_kv_computed_tokens"),
              **gpu_stats(gs)
            }
            rows.append(row)

    write_csv(out/"vllm_runs.csv",rows)
    (out/"vllm_runs.json").write_text(json.dumps(rows,indent=2))
    md=["# V5 Kimi-Linear vLLM surrogate summary","",
        "> **Guardrail:** measured 48B surrogate data; absolute speed is not a K3 prediction.","",
        "| Case | Bench | Input | C | TTFT mean ms | TTFT P95 | TPOT mean ms | KV peak | Preempt Δ | Offload bytes Δ | GPU util mean |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    def fm(v,d=2):
        try: return f"{float(v):.{d}f}"
        except Exception: return ""
    for r in rows:
        md.append(f"| {r['case']} | {r['bench']} | {r['input_tokens']} | {r['concurrency']} | {fm(r.get('mean_ttft_ms'))} | {fm(r.get('p95_ttft_ms'))} | {fm(r.get('mean_tpot_ms'))} | {fm(r.get('peak_kv_usage'),3)} | {fm(r.get('preemptions_delta'),0)} | {fm(r.get('offload_bytes_delta'),0)} | {fm(r.get('gpu_util_mean_pct'),1)} |")
    (out/"VLLM_SUMMARY.md").write_text("\n".join(md)+"\n")
    print(f"Wrote {out}")

if __name__=="__main__":
    main()
