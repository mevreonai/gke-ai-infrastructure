#!/usr/bin/env python3
"""
Analyze summary output and create a decision-oriented Markdown report.
No external Python packages required.

Usage:
  python3 05_analyze_model.py summary/summary.json --out model_analysis.md \
      [--local-tpot-ms 57.7] [--local-ttft-512-s 160] [--local-ttft-1m-s 900]

Important:
- These are hardware-level proxy models.
- No result is labeled as Kimi model throughput.
"""
from __future__ import annotations
import argparse, json, math, statistics
from pathlib import Path

L=93
H=7168
BF16_BYTES=2
PREFILL_CHUNK=8192
PROXY_MSG_BYTES=128*1024**2  # nearest test point to ~112 MiB BF16 hidden-state proxy

def find(rows, kind=None, tp=None, prov=None, size_bytes=None):
    out=[]
    for r in rows:
        if kind is not None and r.get("kind") != kind: continue
        if tp is not None and str(r.get("tp")) != str(tp): continue
        if prov is not None and r.get("network_provenance") != prov: continue
        if size_bytes is not None and int(r.get("size_bytes",0)) != size_bytes: continue
        out.append(r)
    return out

def first(rows, **kw):
    x=find(rows,**kw)
    return x[0] if x else None

def linear_fit(xs,ys):
    n=len(xs)
    if n<2: return None
    xm=sum(xs)/n; ym=sum(ys)/n
    den=sum((x-xm)**2 for x in xs)
    if den==0: return None
    b=sum((x-xm)*(y-ym) for x,y in zip(xs,ys))/den
    a=ym-b*xm
    return a,b

def pct(x):
    return f"{100*x:.1f}%"

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("summary_json",type=Path)
    ap.add_argument("--out",type=Path,default=Path("MODEL_ANALYSIS.md"))
    ap.add_argument("--local-tpot-ms",type=float,default=None)
    ap.add_argument("--local-ttft-512-s",type=float,default=None)
    ap.add_argument("--local-ttft-1m-s",type=float,default=None)
    args=ap.parse_args()

    d=json.loads(args.summary_json.read_text())
    rows=d.get("nccl",[])
    iperf={r["network_provenance"]:r for r in d.get("iperf",[])}

    sizes={"16K":16*1024,"128M":128*1024**2,"256M":256*1024**2}
    tp={}
    for t in (4,8):
        tp[t]={}
        for name,b in sizes.items():
            tp[t][name]=first(rows,kind="ALLREDUCE",tp=t,size_bytes=b)

    md=["# RTX PRO 6000 smoke-test model analysis",""]
    md.append("This report converts the synthetic measurements into inputs for the separate **3-node Kimi K3 TP8/PP3 vs TP4/PP6 model**. It does not claim end-to-end Kimi performance.")
    md.append("")

    # TP comparison
    md.append("## 1. TP4 vs TP8")
    if tp[4]["16K"] and tp[8]["16K"]:
        t4=tp[4]["16K"]["time_us"]; t8=tp[8]["16K"]["time_us"]
        md.append(f"- 16 KiB collective time: TP4 **{t4:.3f} us**, TP8 **{t8:.3f} us**; TP8/TP4 latency ratio = **{t8/t4:.2f}×**.")
    else:
        md.append("- 16 KiB TP4/TP8 points missing.")

    for sz in ("128M","256M"):
        a=tp[4][sz]; b=tp[8][sz]
        if a and b and b["algbw_GBs"]>0:
            ratio=a["algbw_GBs"]/b["algbw_GBs"]
            md.append(f"- {sz} algbw: TP4 **{a['algbw_GBs']:.2f} GB/s**, TP8 **{b['algbw_GBs']:.2f} GB/s**; TP4/TP8 = **{ratio:.2f}×**.")
    # Gate
    a=tp[4]["128M"]; b=tp[8]["128M"]
    if a and b and b["algbw_GBs"]>0:
        adv=a["algbw_GBs"]/b["algbw_GBs"]-1
        if adv < .10:
            verdict="TP topology looks secondary from this synthetic test."
        elif adv < .30:
            verdict="TP topology matters, but model-level A/B is still required."
        elif adv < .50:
            verdict="TP4/PP6 should be a high-priority real-model A/B."
        else:
            verdict="Strong synthetic evidence that TP8 cross-domain communication is expensive; TP4/PP6 should be tested early."
        md.append(f"- **Decision gate:** TP4 large-message advantage = **{pct(adv)}**. {verdict}")
    md.append("")

    # Network table
    md.append("## 2. Network sweep")
    provs=["GCP_NATIVE","GCP_CAPPED_100G","GCP_CAPPED_50G","GCP_CAPPED_20G","GCP_CAPPED_10G"]
    md.append("| Provenance | iperf Gb/s | SendRecv 16K us | 128M us | 256M us | 128M effective GB/s |")
    md.append("|---|---:|---:|---:|---:|---:|")
    for p in provs:
        r16=first(rows,kind="SENDRECV",prov=p,size_bytes=16*1024)
        r128=first(rows,kind="SENDRECV",prov=p,size_bytes=128*1024**2)
        r256=first(rows,kind="SENDRECV",prov=p,size_bytes=256*1024**2)
        ig=iperf.get(p,{}).get("gbps")
        def val(r,k): return f"{r[k]:.3f}" if r else ""
        eff=(128*1024**2/(r128["time_us"]*1e-6)/1e9) if r128 and r128["time_us"]>0 else None
        md.append(f"| {p} | {ig:.2f}" if ig is not None else f"| {p} | ")
        md[-1] += f" | {val(r16,'time_us')} | {val(r128,'time_us')} | {val(r256,'time_us')} | {eff:.3f}" if eff is not None else f" | {val(r16,'time_us')} | {val(r128,'time_us')} | {val(r256,'time_us')} | "
        md[-1] += " |"

    # alpha-beta fits for each provenance using 64/128/256M
    md.append("")
    md.append("### Large-message alpha–beta fits")
    md.append("| Provenance | alpha (ms) | fitted payload BW (GB/s) |")
    md.append("|---|---:|---:|")
    netfit={}
    for p in provs:
        rs=[]
        for b in (64*1024**2,128*1024**2,256*1024**2):
            r=first(rows,kind="SENDRECV",prov=p,size_bytes=b)
            if r: rs.append(r)
        fit=linear_fit([r["size_bytes"] for r in rs],[r["time_us"]*1e-6 for r in rs])
        if fit and fit[1]>0:
            alpha,beta=fit
            bw=1/beta/1e9
            netfit[p]=(alpha,bw)
            md.append(f"| {p} | {alpha*1e3:.3f} | {bw:.3f} |")
    md.append("")
    md.append("> The capped curves primarily characterize the **bandwidth/serialization term**. They do not reproduce the local lab NIC's physical latency, NUMA placement, queueing, offloads, switch behavior, or firmware.")

    # PP proxy
    md.append("")
    md.append("## 3. PP-network proxy for the 3-node system")
    hidden_bytes=PREFILL_CHUNK*H*BF16_BYTES
    md.append(f"An 8K-token BF16 hidden-state proxy is **{hidden_bytes/1024**2:.1f} MiB**. The smoke suite measures nearby 128 MiB transfers and also fits the 64/128/256 MiB curve.")
    for p in ("GCP_CAPPED_20G","GCP_CAPPED_10G"):
        fit=netfit.get(p)
        if fit:
            alpha,bw=fit
            t=alpha + hidden_bytes/(bw*1e9)
            # two remote PP boundaries; no-overlap upper proxy
            two=2*t
            t512=64*two
            t1m=128*two
            md.append(f"- {p}: fitted one-boundary transfer ≈ **{t*1e3:.1f} ms** at 8K chunk; two serialized boundaries ≈ **{two*1e3:.1f} ms/chunk**. No-overlap network-only proxies: 512K ≈ **{t512:.1f} s**, 1M ≈ **{t1m:.1f} s**.")
    md.append("")
    md.append("These are intentionally conservative *serialization proxies*. Real vLLM can overlap some PP communication with compute/pipeline execution.")

    # TP K sensitivity
    md.append("")
    md.append("## 4. TP communication sensitivity for K3")
    md.append("For the 93-layer model, if the runtime executes an effective **K** full-hidden-state collective equivalents per layer, a simple 8K-chunk proxy is:")
    md.append("")
    md.append("`T_TP_chunk ≈ 93 × K × measured_AllReduce_time(128MiB)`")
    md.append("")
    md.append("| TP | K=1 | K=1.5 | K=2 |")
    md.append("|---|---:|---:|---:|")
    for t in (4,8):
        r=tp[t]["128M"]
        if r:
            one=r["time_us"]*1e-6
            vals=[L*k*one for k in (1,1.5,2)]
            md.append(f"| TP{t} | {vals[0]:.3f} s | {vals[1]:.3f} s | {vals[2]:.3f} s |")
    md.append("")
    md.append("> K is deliberately a sensitivity parameter; only a real vLLM/K3 trace can establish the exact collective count/fusion behavior.")

    # Decode proxy
    md.append("")
    md.append("## 5. Decode collective-latency proxy")
    md.append("Using the 16 KiB NCCL point as a batch-1-sized proxy:")
    for t in (4,8):
        r=tp[t]["16K"]
        if r:
            one=r["time_us"]*1e-6
            vals=[L*k*one*1e3 for k in (1,1.5,2)]
            md.append(f"- TP{t}: ~**{vals[0]:.2f}/{vals[1]:.2f}/{vals[2]:.2f} ms/token** for K=1/1.5/2, before overlap/fusion.")
    if args.local_tpot_ms:
        md.append(f"- Local observed TPOT supplied to analyzer: **{args.local_tpot_ms:.2f} ms/token**.")
        r=tp[8]["16K"]
        if r:
            for k in (1,1.5,2):
                frac=(L*k*r["time_us"]/1000)/args.local_tpot_ms
                md.append(f"  - TP8 communication proxy at K={k}: **{pct(frac)}** of local TPOT.")
    md.append("")

    # Local TTFT consistency
    if args.local_ttft_512_s or args.local_ttft_1m_s:
        md.append("## 6. Compare against supplied local TTFT")
        if args.local_ttft_512_s: md.append(f"- Local 512K TTFT: **{args.local_ttft_512_s:.1f} s**.")
        if args.local_ttft_1m_s: md.append(f"- Local 1M TTFT: **{args.local_ttft_1m_s:.1f} s**.")
        if args.local_ttft_512_s and args.local_ttft_1m_s:
            ratio=args.local_ttft_1m_s/args.local_ttft_512_s
            md.append(f"- 1M/512K scaling ratio: **{ratio:.2f}×**.")
            if ratio>4:
                md.append("- This exceeds the 2×–4× range expected from a simple linear+quadratic compute/communication model, strengthening the hypothesis of an additional regime change such as cache/offload/scheduler pressure.")
        md.append("")

    md.append("## 7. What remains unresolved without Kimi/vLLM")
    md.extend([
        "- MXFP4 Kimi kernel efficiency",
        "- actual KDA/MLA execution time",
        "- exact collective count/fusion per K3 layer",
        "- vLLM pipeline overlap and bubbles",
        "- SimpleCPUOffloadConnector / LMCache lookup, eviction and restore behavior",
        "- KV/cache residency at 512K and 1M",
        "- scheduler/preemption effects",
        "",
        "Therefore this report should be used to **prioritize** TP8/PP3 vs TP4/PP6 and network/offload experiments, not to claim final tokens/s."
    ])

    args.out.write_text("\n".join(md)+"\n")
    print(f"Wrote {args.out}")

if __name__=="__main__":
    main()
