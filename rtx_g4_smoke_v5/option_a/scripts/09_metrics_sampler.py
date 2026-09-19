#!/usr/bin/env python3
"""
Poll vLLM /metrics plus nvidia-smi. Saves every vLLM metric with labels.
Stdlib only so it can run inside the isolated venv.

Output: JSONL with records:
  {"ts": ..., "kind":"prometheus", "metrics":[...]}
  {"ts": ..., "kind":"gpu", "gpus":[...]}
"""
from __future__ import annotations
import argparse, json, re, subprocess, time
from pathlib import Path
from urllib.request import urlopen, Request

PROM_RE = re.compile(r'^([^\s{]+)(?:\{(.*)\})?\s+([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?|[+-]?Inf|NaN)$')
LABEL_RE = re.compile(r'(\w+)="((?:\\.|[^"])*)"')

def scrape(url: str):
    req = Request(url, headers={"User-Agent":"v5-smoke"})
    with urlopen(req, timeout=5) as r:
        text = r.read().decode("utf-8", "replace")
    metrics = []
    for line in text.splitlines():
        line=line.strip()
        if not line or line.startswith("#"):
            continue
        m=PROM_RE.match(line)
        if not m:
            continue
        name, labels_raw, value_raw=m.groups()
        if not name.startswith("vllm:"):
            continue
        labels={}
        if labels_raw:
            for lm in LABEL_RE.finditer(labels_raw):
                labels[lm.group(1)] = bytes(lm.group(2), "utf-8").decode("unicode_escape")
        try:
            val=float(value_raw)
        except Exception:
            continue
        metrics.append({"name":name,"labels":labels,"value":val})
    return metrics, text

def gpu_snapshot():
    fields = [
        "index","uuid","pstate","utilization.gpu","utilization.memory",
        "memory.used","memory.total","power.draw","temperature.gpu",
        "clocks.sm","clocks.mem","pcie.link.gen.current","pcie.link.width.current"
    ]
    cmd=["nvidia-smi","--query-gpu="+",".join(fields),"--format=csv,noheader,nounits"]
    try:
        out=subprocess.check_output(cmd,text=True,stderr=subprocess.STDOUT,timeout=5)
    except Exception as e:
        return [{"error":repr(e)}]
    rows=[]
    for line in out.splitlines():
        vals=[x.strip() for x in line.split(",")]
        rows.append(dict(zip(fields,vals)))
    return rows

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--url", default="http://127.0.0.1:8000/metrics")
    ap.add_argument("--interval", type=float, default=1.0)
    ap.add_argument("--out", required=True)
    ap.add_argument("--raw-prom", default=None)
    args=ap.parse_args()
    out=Path(args.out); out.parent.mkdir(parents=True,exist_ok=True)
    raw=Path(args.raw_prom) if args.raw_prom else None

    with out.open("a", buffering=1) as f:
        while True:
            ts=time.time()
            try:
                metrics, text=scrape(args.url)
                f.write(json.dumps({"ts":ts,"kind":"prometheus","metrics":metrics})+"\n")
                if raw:
                    with raw.open("a") as rf:
                        rf.write(f"\n# === scrape ts={ts} ===\n{text}\n")
            except Exception as e:
                f.write(json.dumps({"ts":ts,"kind":"prometheus_error","error":repr(e)})+"\n")
            f.write(json.dumps({"ts":ts,"kind":"gpu","gpus":gpu_snapshot()})+"\n")
            f.flush()
            time.sleep(args.interval)

if __name__=="__main__":
    main()
