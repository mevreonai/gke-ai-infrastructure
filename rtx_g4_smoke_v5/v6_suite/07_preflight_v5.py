#!/usr/bin/env python3
"""Preflight validator for the V5 vLLM characterization suite.
Fails closed on missing required CLI capabilities and records exact environment provenance.
"""
from __future__ import annotations
import argparse, json, os, platform, shutil, subprocess, sys, time
from pathlib import Path

REQUIRED_SERVE_FLAGS = [
    "--tensor-parallel-size", "--pipeline-parallel-size", "--max-model-len",
    "--max-num-batched-tokens", "--max-num-seqs", "--gpu-memory-utilization",
    "--kv-cache-dtype", "--revision", "--enable-prefix-caching",
]
REQUIRED_BENCH_FLAGS = [
    "--dataset-name", "--random-input-len", "--random-output-len",
    "--num-prompts", "--max-concurrency", "--request-rate", "--burstiness",
    "--num-warmups", "--save-result", "--save-detailed",
]
OPTIONAL_SERVE_FLAGS = [
    "--max-num-active-seqs", "--kv-cache-memory-bytes", "--kv-offloading-size",
    "--kv-offloading-backend", "--performance-mode", "--optimization-level",
    "--kv-cache-metrics", "--cudagraph-metrics", "--enable-mfu-metrics",
    "--enable-logging-iteration-details", "--profiler-config",
    "--enable-layerwise-nvtx-tracing", "--distributed-executor-backend",
]
OPTIONAL_BENCH_FLAGS = [
    "--probe-request-rate", "--ramp-up-strategy", "--ramp-up-start-rps",
    "--ramp-up-end-rps", "--prefix-repetition-prefix-len",
    "--prefix-repetition-suffix-len", "--prefix-repetition-num-prefixes",
    "--prefix-repetition-output-len", "--profile", "--goodput",
]

def run(cmd, timeout=60):
    try:
        p = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                           timeout=timeout, check=False)
        return {"rc": p.returncode, "out": p.stdout}
    except Exception as e:
        return {"rc": None, "out": repr(e)}

def has_all(text, flags):
    return {f: (f in text) for f in flags}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="preflight_v5")
    ap.add_argument("--require-ray", action="store_true")
    ap.add_argument("--require-nsys", action="store_true")
    args = ap.parse_args()
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)

    vllm = shutil.which("vllm")
    if not vllm:
        raise SystemExit("vllm CLI not found. Activate the same vllm_env used for prior successful runs.")

    version = run([vllm, "--version"])
    serve_help = run([vllm, "serve", "--help"], timeout=120)
    bench_help = run([vllm, "bench", "serve", "--help"], timeout=120)
    nvsmi = run(["nvidia-smi", "--query-gpu=index,uuid,name,memory.total,pci.bus_id", "--format=csv,noheader,nounits"])
    pyver = sys.version.replace("\n", " ")
    pip_freeze = run([sys.executable, "-m", "pip", "freeze"], timeout=120)
    pkg_lines = [x for x in pip_freeze["out"].splitlines() if any(k in x.lower() for k in (
        "vllm", "torch", "triton", "flashinfer", "ray", "transformers", "huggingface", "nccl"
    ))]

    serve_caps = has_all(serve_help["out"], REQUIRED_SERVE_FLAGS + OPTIONAL_SERVE_FLAGS)
    bench_caps = has_all(bench_help["out"], REQUIRED_BENCH_FLAGS + OPTIONAL_BENCH_FLAGS)
    missing = [f for f in REQUIRED_SERVE_FLAGS if not serve_caps[f]] + [f for f in REQUIRED_BENCH_FLAGS if not bench_caps[f]]

    rec = {
        "timestamp": time.time(), "hostname": platform.node(), "platform": platform.platform(),
        "python": pyver, "vllm_path": vllm, "vllm_version_output": version,
        "gpu_inventory": nvsmi, "packages": pkg_lines,
        "serve_capabilities": serve_caps, "bench_capabilities": bench_caps,
        "ray_path": shutil.which("ray"), "nsys_path": shutil.which("nsys"),
        "required_missing": missing,
        "env_subset": {k: v for k, v in os.environ.items() if k.startswith(("NCCL_", "CUDA_", "VLLM_", "RAY_"))},
    }
    (out / "preflight.json").write_text(json.dumps(rec, indent=2))
    md = ["# V5 preflight", "", f"- Host: `{platform.node()}`", f"- vLLM: `{version['out'].strip()}`",
          f"- Required flags missing: `{missing or 'none'}`", f"- Ray: `{shutil.which('ray') or 'NOT FOUND'}`",
          f"- Nsight Systems: `{shutil.which('nsys') or 'NOT FOUND'}`", "", "## GPU inventory", "```", nvsmi["out"].strip(), "```",
          "", "## Relevant packages", "```", "\n".join(pkg_lines), "```"]
    (out / "PREFLIGHT.md").write_text("\n".join(md) + "\n")

    hard_fail = bool(missing)
    if args.require_ray and not shutil.which("ray"): hard_fail = True
    if args.require_nsys and not shutil.which("nsys"): hard_fail = True
    print(json.dumps({"preflight_dir": str(out.resolve()), "missing_required": missing, "ok": not hard_fail}, indent=2))
    raise SystemExit(2 if hard_fail else 0)

if __name__ == "__main__":
    main()
