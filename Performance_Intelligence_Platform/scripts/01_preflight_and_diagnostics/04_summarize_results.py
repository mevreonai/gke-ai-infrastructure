#!/usr/bin/env python3
"""
Parse RTX G4 smoke-test logs into machine-readable CSV/JSON plus a concise Markdown summary.
Uses Python stdlib only.

Usage:
  python3 04_summarize_results.py /path/to/results/RUN_ID --out /path/to/summary
"""
from __future__ import annotations
import argparse, csv, json, math, re, statistics
from pathlib import Path
from typing import Any

SIZE_RE = re.compile(r"^(\d+(?:\.\d+)?)([KMG]?)$", re.I)

def size_to_bytes(s: str) -> int:
    m = SIZE_RE.match(s.strip())
    if not m:
        raise ValueError(s)
    x = float(m.group(1))
    u = m.group(2).upper()
    mul = {"":1,"K":1024,"M":1024**2,"G":1024**3}[u]
    return int(x*mul)

def find_data_row(text: str, kind: str = "") -> dict[str, Any] | None:
    """
    Parse the first NCCL-tests data row.
    Canonical all_reduce row:
      size count type redop root time algbw busbw #wrong time algbw busbw #wrong
    sendrecv has a very similar prefix. We use the first out-of-place time/algbw/busbw triplet.
    """
    for line in text.splitlines():
        s=line.strip()
        if not s or s.startswith("#"):
            continue
        toks=s.split()
        if len(toks) < 8 or not toks[0].isdigit():
            continue
        try:
            size=int(toks[0])
        except Exception:
            continue
        # NCCL-tests text columns differ slightly by operation.
        # AllReduce includes a root column: time/algbw/busbw start at index 5.
        # SendRecv has no root column: time/algbw/busbw start at index 4.
        # The output header itself labels time in microseconds.
        preferred = 4 if kind.upper() == "SENDRECV" else 5
        candidates = []
        for i in range(3, min(len(toks)-2, 10)):
            try:
                a=float(toks[i]); b=float(toks[i+1]); c=float(toks[i+2])
            except Exception:
                continue
            candidates.append((i,a,b,c))
        pick = next((x for x in candidates if x[0] == preferred), None)
        if pick is None and candidates:
            pick = next((x for x in candidates if x[1] > 0 and x[2] >= 0 and x[3] >= 0), candidates[0])
        if pick:
            i,t,algbw,busbw = pick
            return {"size_bytes": size, "time_us": t, "algbw_GBs": algbw, "busbw_GBs": busbw,
                    "parse_index": i, "raw_line": s}
    return None

def parse_meta(text: str) -> dict[str,str]:
    d={}
    for line in text.splitlines():
        if line.strip().startswith("META "):
            for kv in line.strip()[5:].split():
                if "=" in kv:
                    k,v=kv.split("=",1); d[k]=v
    return d

def parse_nccl_logs(root: Path) -> list[dict[str,Any]]:
    rows=[]
    patterns = ["*ar_tp4_*.log","*ar_tp8_*.log","*sendrecv_*.log","*crossnode_ar_TP*.log"]
    seen=set()
    for pat in patterns:
        for p in root.rglob(pat):
            if p in seen or p.name.endswith("_nvsmi_dmon.log"):
                continue
            seen.add(p)
            text=p.read_text(errors="ignore")
            meta=parse_meta(text)
            label=p.stem
            kind=meta.get("TEST_KIND","")
            if not kind:
                kind="SENDRECV" if "sendrecv" in label else "ALLREDUCE"
            row=find_data_row(text, kind)
            if not row:
                continue
            tp=None
            m=re.search(r"_tp(2|4|8|16)_", label, re.I)
            if m: tp=int(m.group(1))
            if not tp and meta.get("TOPOLOGY","").upper().startswith("TP"):
                try: tp=int(meta["TOPOLOGY"][2:])
                except Exception: pass
            prov=meta.get("NETWORK_PROVENANCE")
            cap=meta.get("CAP_GBIT")
            size_label=meta.get("SIZE")
            if not size_label:
                m=re.search(r"_(16k|128k|512k|64m|128m|256m)$", label, re.I)
                size_label=m.group(1).upper() if m else ""
            rows.append({
                "file": str(p),
                "label": label,
                "kind": kind,
                "tp": tp or "",
                "network_provenance": prov or "",
                "cap_gbit": float(cap) if cap not in (None,"") else "",
                "size_label": size_label or "",
                **row
            })
    return rows

def parse_iperf(root: Path) -> list[dict[str,Any]]:
    out=[]
    for p in root.rglob("iperf_*.raw.json"):
        try:
            d=json.loads(p.read_text())
        except Exception:
            continue
        end=d.get("end",{})
        bits=None
        # iperf3 JSON with parallel streams normally has sum_received/sum_sent.
        for key in ("sum_received","sum_sent","sum"):
            obj=end.get(key)
            if isinstance(obj,dict) and obj.get("bits_per_second"):
                bits=float(obj["bits_per_second"]); break
        if bits is None:
            continue
        name=p.stem
        tag=name.replace("iperf_","").replace(".raw","")
        out.append({"file":str(p),"network_provenance":tag,
                    "gbps":bits/1e9,"GBps":bits/8e9})
    return out

def recursive_numeric(obj: Any, prefix="") -> list[tuple[str,float]]:
    vals=[]
    if isinstance(obj,dict):
        for k,v in obj.items():
            vals.extend(recursive_numeric(v, f"{prefix}.{k}" if prefix else str(k)))
    elif isinstance(obj,list):
        for i,v in enumerate(obj):
            vals.extend(recursive_numeric(v, f"{prefix}[{i}]"))
    elif isinstance(obj,(int,float)) and math.isfinite(float(obj)):
        vals.append((prefix,float(obj)))
    return vals

def parse_nvbandwidth(root: Path) -> list[dict[str,Any]]:
    out=[]
    for p in root.rglob("nvbandwidth_*.raw.json"):
        try:
            d=json.loads(p.read_text())
        except Exception:
            continue
        for key,val in recursive_numeric(d):
            lk=key.lower()
            if "bandwidth" in lk or "latency" in lk:
                out.append({"file":str(p),"metric_path":key,"value":val})
    return out

def parse_babel(root: Path) -> list[dict[str,Any]]:
    out=[]
    # BabelStream commonly prints "Copy", "Mul", "Add", "Triad", "Dot" lines with rate.
    rx=re.compile(r"^\s*(Copy|Mul|Add|Triad|Dot)\s+([0-9]+(?:\.[0-9]+)?)", re.I)
    for p in root.rglob("*babelstream*.log"):
        text=p.read_text(errors="ignore")
        for line in text.splitlines():
            m=rx.match(line)
            if m:
                out.append({"file":str(p),"kernel":m.group(1),
                            "value":float(m.group(2)),"unit":"MBytes/sec"})
    return out


def parse_cutlass(root: Path) -> list[dict[str,Any]]:
    out=[]
    for p in root.rglob("cutlass*.csv"):
        try:
            with p.open(newline="") as f:
                rdr=csv.DictReader(f)
                for row in rdr:
                    lower={str(k).lower():v for k,v in row.items() if k is not None}
                    gkey=next((k for k in lower if "gflop" in k),None)
                    rkey=next((k for k in lower if "runtime" in k),None)
                    if not gkey and not rkey:
                        continue
                    rec={"file":str(p)}
                    for wanted in ("m","n","k"):
                        k2=next((k for k in lower if k == wanted or k.endswith("_"+wanted)),None)
                        if k2 and lower.get(k2) not in (None,""):
                            rec[wanted]=lower[k2]
                    if gkey:
                        try: rec["GFLOPs"]=float(lower[gkey])
                        except Exception: rec["GFLOPs"]=lower[gkey]
                    if rkey:
                        try: rec["runtime"]=float(lower[rkey])
                        except Exception: rec["runtime"]=lower[rkey]
                    out.append(rec)
        except Exception:
            continue
    return out

def write_csv(path: Path, rows: list[dict[str,Any]]):
    if not rows:
        path.write_text("")
        return
    keys=[]
    for r in rows:
        for k in r:
            if k not in keys: keys.append(k)
    with path.open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=keys)
        w.writeheader(); w.writerows(rows)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("results_root", type=Path)
    ap.add_argument("--out", type=Path, default=None)
    args=ap.parse_args()
    root=args.results_root.resolve()
    out=(args.out or (root/"summary")).resolve()
    out.mkdir(parents=True,exist_ok=True)

    nccl=parse_nccl_logs(root)
    iperf=parse_iperf(root)
    nvbw=parse_nvbandwidth(root)
    babel=parse_babel(root)
    cutlass=parse_cutlass(root)

    write_csv(out/"nccl_points.csv", nccl)
    write_csv(out/"iperf.csv", iperf)
    write_csv(out/"nvbandwidth_metrics.csv", nvbw)
    write_csv(out/"babelstream.csv", babel)
    write_csv(out/"cutlass.csv", cutlass)

    payload={"nccl":nccl,"iperf":iperf,"nvbandwidth_metrics":nvbw,"babelstream":babel,"cutlass":cutlass}
    (out/"summary.json").write_text(json.dumps(payload,indent=2))

    md=[]
    md.append("# RTX G4 smoke-test summary\n")
    md.append(f"Results root: `{root}`\n")
    md.append("## NCCL exact points\n")
    if nccl:
        md.append("| Kind | TP | Network provenance | Cap Gb/s | Size | Time (us) | algbw GB/s | busbw GB/s |")
        md.append("|---|---:|---|---:|---:|---:|---:|---:|")
        for r in sorted(nccl,key=lambda x:(x["kind"],str(x["network_provenance"]),str(x["tp"]),x["size_bytes"])):
            md.append(f"| {r['kind']} | {r['tp']} | {r['network_provenance']} | {r['cap_gbit']} | {r['size_label'] or r['size_bytes']} | {r['time_us']:.3f} | {r['algbw_GBs']:.3f} | {r['busbw_GBs']:.3f} |")
    else:
        md.append("_No NCCL point logs parsed._")

    md.append("\n## iperf3\n")
    if iperf:
        md.append("| Network provenance | Gb/s | GB/s |")
        md.append("|---|---:|---:|")
        for r in sorted(iperf,key=lambda x:x["network_provenance"]):
            md.append(f"| {r['network_provenance']} | {r['gbps']:.2f} | {r['GBps']:.2f} |")
    else:
        md.append("_No iperf JSON parsed._")

    md.append("\n## Other raw metrics\n")
    md.append(f"- NVBandwidth numeric bandwidth/latency fields parsed: **{len(nvbw)}**")
    md.append(f"- BabelStream rows parsed: **{len(babel)}**")
    md.append("- CUTLASS rows parsed from machine-readable profiler CSV: **{len(cutlass)}**")
    md.append("\n> Check `nccl_points.csv`, `iperf.csv`, `nvbandwidth_metrics.csv`, `babelstream.csv`, `cutlass.csv`, and `summary.json` for machine-readable data.\n")
    (out/"SUMMARY.md").write_text("\n".join(md)+"\n")
    print(f"Wrote summary to {out}")

if __name__=="__main__":
    main()
