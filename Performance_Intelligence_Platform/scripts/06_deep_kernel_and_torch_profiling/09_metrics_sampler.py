#!/usr/bin/env python3
"""Poll vLLM /metrics, selected GPUs, and lightweight host telemetry.
Designed so TP4 does not average idle GPUs 4-7. Can also run GPU-only on a remote node.
"""
from __future__ import annotations
import argparse, json, os, platform, re, subprocess, time
from pathlib import Path
from urllib.request import urlopen, Request

PROM_RE = re.compile(r'^([^\s{]+)(?:\{(.*)\})?\s+([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?|[+-]?Inf|NaN)$')
LABEL_RE = re.compile(r'(\w+)="((?:\\.|[^"])*)"')

def scrape(url: str):
    req = Request(url, headers={"User-Agent":"v5-characterization"})
    with urlopen(req, timeout=5) as r:
        text = r.read().decode("utf-8", "replace")
    metrics=[]
    for line in text.splitlines():
        line=line.strip()
        if not line or line.startswith("#"): continue
        m=PROM_RE.match(line)
        if not m: continue
        name, labels_raw, value_raw=m.groups()
        if not name.startswith("vllm:"): continue
        labels={}
        if labels_raw:
            for lm in LABEL_RE.finditer(labels_raw):
                labels[lm.group(1)] = bytes(lm.group(2), "utf-8").decode("unicode_escape")
        try: val=float(value_raw)
        except Exception: continue
        metrics.append({"name":name,"labels":labels,"value":val})
    return metrics, text

def parse_indices(raw: str | None):
    if not raw: return None
    return {int(x) for x in raw.split(",") if x.strip()}

def gpu_snapshot(indices=None):
    fields=["index","uuid","pstate","utilization.gpu","utilization.memory","memory.used","memory.total",
            "power.draw","temperature.gpu","clocks.sm","clocks.mem","pcie.link.gen.current","pcie.link.width.current"]
    cmd=["nvidia-smi","--query-gpu="+",".join(fields),"--format=csv,noheader,nounits"]
    try: out=subprocess.check_output(cmd,text=True,stderr=subprocess.STDOUT,timeout=5)
    except Exception as e: return [{"error":repr(e)}]
    rows=[]
    for line in out.splitlines():
        vals=[x.strip() for x in line.split(",")]
        d=dict(zip(fields,vals))
        try: idx=int(d["index"])
        except Exception: continue
        if indices is None or idx in indices: rows.append(d)
    return rows

def host_snapshot():
    rec={}
    try:
        with open("/proc/loadavg") as f:
            parts=f.read().split(); rec.update({"load1":float(parts[0]),"load5":float(parts[1]),"load15":float(parts[2])})
    except Exception: pass
    try:
        vals={}
        for line in Path("/proc/meminfo").read_text().splitlines():
            k,v=line.split(":",1); vals[k]=int(v.strip().split()[0])
        rec["mem_total_kib"]=vals.get("MemTotal"); rec["mem_available_kib"]=vals.get("MemAvailable")
    except Exception: pass
    return rec

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--url", default="http://127.0.0.1:8000/metrics")
    ap.add_argument("--interval", type=float, default=0.5)
    ap.add_argument("--out", required=True)
    ap.add_argument("--raw-prom", default=None)
    ap.add_argument("--gpu-indices", default=None, help="Comma-separated physical GPU indices to sample.")
    ap.add_argument("--gpu-only", action="store_true", help="Do not scrape vLLM /metrics; useful on remote Ray worker.")
    ap.add_argument("--node-label", default=None)
    args=ap.parse_args()
    out=Path(args.out); out.parent.mkdir(parents=True,exist_ok=True)
    raw=Path(args.raw_prom) if args.raw_prom else None
    indices=parse_indices(args.gpu_indices)
    node=args.node_label or platform.node()

    with out.open("a",buffering=1) as f:
        f.write(json.dumps({"ts":time.time(),"kind":"sampler_start","node":node,"pid":os.getpid(),"gpu_indices":sorted(indices) if indices is not None else None})+"\n")
        try:
            while True:
                ts=time.time()
                if not args.gpu_only:
                    try:
                        metrics,text=scrape(args.url)
                        f.write(json.dumps({"ts":ts,"kind":"prometheus","node":node,"metrics":metrics})+"\n")
                        if raw:
                            with raw.open("a") as rf: rf.write(f"\n# === scrape ts={ts} node={node} ===\n{text}\n")
                    except Exception as e:
                        f.write(json.dumps({"ts":ts,"kind":"prometheus_error","node":node,"error":repr(e)})+"\n")
                f.write(json.dumps({"ts":ts,"kind":"gpu","node":node,"gpus":gpu_snapshot(indices)})+"\n")
                f.write(json.dumps({"ts":ts,"kind":"host","node":node,"host":host_snapshot()})+"\n")
                f.flush(); time.sleep(args.interval)
        except KeyboardInterrupt:
            pass

if __name__=="__main__": main()
