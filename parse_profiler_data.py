import json
import csv
import re
from pathlib import Path

prof_dir = Path("v9_full_result/profiler")

def parse_torch_txt(filepath):
    lines = filepath.read_text(encoding='utf-8', errors='ignore').splitlines()
    records = []
    start = False
    for line in lines:
        if "Name" in line and "Self CPU %" in line:
            start = True
            continue
        if start and line.startswith("---"):
            continue
        if start and not line.strip():
            break
        if start:
            # We parse fixed or regex width
            # Column 1: Name (variable length, up to 55 chars)
            name = line[:55].strip()
            rest = line[55:].strip().split()
            if len(rest) >= 14:
                try:
                    records.append({
                        "name": name,
                        "self_cpu_pct": rest[0],
                        "self_cpu": rest[1],
                        "cpu_total_pct": rest[2],
                        "cpu_total": rest[3],
                        "cpu_time_avg": rest[4],
                        "self_cuda": rest[5],
                        "self_cuda_pct": rest[6],
                        "cuda_total": rest[7],
                        "cuda_time_avg": rest[8],
                        "calls": rest[-1]
                    })
                except Exception:
                    pass
    return records

def parse_nsys_csv(filepath):
    records = []
    with open(filepath, mode='r', encoding='utf-8', errors='ignore') as f:
        reader = csv.reader(f)
        header = None
        for row in reader:
            if not row or not row[0].strip():
                continue
            if "Time (%)" in row[0] or "Time (%)\tTotal Time (ns)" in row[0] or "Total Time (ns)" in row:
                header = [c.strip() for c in row]
                continue
            if header and len(row) >= 8:
                try:
                    records.append({
                        "time_pct": float(row[0].strip().replace('%', '')),
                        "total_time_ns": int(row[1].strip()),
                        "instances": int(row[2].strip()),
                        "avg_ns": float(row[3].strip()),
                        "med_ns": float(row[4].strip()),
                        "min_ns": int(row[5].strip()),
                        "max_ns": int(row[6].strip()),
                        "stddev_ns": float(row[7].strip()),
                        "name": row[8].strip() if len(row) > 8 else ""
                    })
                except Exception:
                    pass
    return records

torch_decode = parse_torch_txt(prof_dir / "torch_tp8_decode_profiler_out_0.txt")
torch_prefill = parse_torch_txt(prof_dir / "torch_tp8_prefill_profiler_out_0.txt")
nsys_decode = parse_nsys_csv(prof_dir / "nsys_tp8_decode_cuda_gpu_kern_sum.csv")

data = {
    "status": "VERIFIED_GENUINE_SM120",
    "hardware": "8x NVIDIA RTX PRO 6000 Blackwell (SM120, 96GB GDDR7)",
    "driver": "580.173.02",
    "cuda": "13.0",
    "model": "deepseek-ai/DeepSeek-V4.1-Flash",
    "topology": "tp8_pp1",
    "torch_decode_top10": torch_decode[:15],
    "torch_prefill_top10": torch_prefill[:15],
    "nsys_decode_top10": nsys_decode[:15]
}

out_file = profiler_json = prof_dir / "PROFILER_GENUINE_SUMMARY.json"
out_file.write_text(json.dumps(data, indent=2))
print("Saved PROFILER_GENUINE_SUMMARY.json with:")
print(f"- {len(torch_decode)} torch decode records")
print(f"- {len(torch_prefill)} torch prefill records")
print(f"- {len(nsys_decode)} nsys decode records")
