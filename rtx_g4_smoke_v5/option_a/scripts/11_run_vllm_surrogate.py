#!/usr/bin/env python3
"""
Launch vLLM case-by-case, run benchmarks, and collect:
- exact server/client commands
- vLLM server logs
- vllm bench serve JSON with per-request detail
- /metrics time series every second
- nvidia-smi time series every second
- case manifest with timestamps and exit codes

Guardrail: this script never converts 48B latency into K3 latency.
"""
from __future__ import annotations
import argparse, json, os, shlex, shutil, signal, subprocess, sys, time
from pathlib import Path
from urllib.request import urlopen

def q(cmd): return " ".join(shlex.quote(str(x)) for x in cmd)

def wait_ready(base, proc, timeout):
    end=time.time()+timeout
    last=None
    while time.time()<end:
        if proc.poll() is not None:
            raise RuntimeError(f"server exited rc={proc.returncode}")
        try:
            with urlopen(base+"/v1/models", timeout=5) as r:
                if r.status==200: return
        except Exception as e:
            last=e
        time.sleep(2)
    raise TimeoutError(f"server not ready after {timeout}s; last={last!r}")

def stop_proc(p):
    if not p: return
    try:
        os.killpg(p.pid, signal.SIGKILL)
    except Exception:
        try: p.kill()
        except Exception: pass
    time.sleep(1)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--cases", default="10_vllm_surrogate_cases.json")
    ap.add_argument("--out", required=True)
    ap.add_argument("--case", action="append", default=[], help="Run only named case(s).")
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--startup-timeout", type=int, default=3600)
    ap.add_argument("--model", default=None)
    ap.add_argument("--seed-base", type=int, default=1000)
    args=ap.parse_args()

    cfg=json.loads(Path(args.cases).read_text())
    model=args.model or cfg["model"]
    out=Path(args.out).resolve(); out.mkdir(parents=True,exist_ok=True)
    vllm=shutil.which("vllm")
    if not vllm: raise SystemExit("vllm CLI not found; activate V5 venv first.")
    py=sys.executable
    sampler=str(Path(__file__).with_name("09_metrics_sampler.py").resolve())

    selected=[c for c in cfg["cases"] if not args.case or c["name"] in set(args.case)]
    if args.case and len(selected)!=len(set(args.case)):
        known={c["name"] for c in cfg["cases"]}
        raise SystemExit(f"Unknown case(s): {set(args.case)-known}")

    top_manifest={
        "model":model,
        "started":time.time(),
        "vllm_cli":vllm,
        "python":py,
        "source_cases":str(Path(args.cases).resolve()),
        "guardrail":"48B absolute performance is not extrapolated to K3.",
        "cases":[]
    }

    for ci,case in enumerate(selected):
        cdir=out/case["name"]; cdir.mkdir(parents=True,exist_ok=True)
        server_log=(cdir/"server.log").open("w", buffering=1)
        server_cmd=[
            vllm,"serve",model,
            "--model-impl","vllm",
            "--trust-remote-code",
            "--host","0.0.0.0","--port",str(args.port),
            "--tensor-parallel-size",str(case["tp"]),
            "--pipeline-parallel-size",str(case.get("pp",1)),
            "--max-model-len",str(cfg["server_defaults"]["max_model_len"]),
            "--max-num-batched-tokens",str(case["max_num_batched_tokens"]),
            "--gpu-memory-utilization",str(case.get("gpu_memory_utilization", cfg["server_defaults"]["gpu_memory_utilization"])),
            "--kv-cache-dtype",str(case.get("kv_cache_dtype", cfg["server_defaults"]["kv_cache_dtype"])),
            "--performance-mode",str(cfg["server_defaults"]["performance_mode"]),
            "--optimization-level",str(cfg["server_defaults"]["optimization_level"]),
            "--no-enable-flashinfer-autotune",
            "--kv-cache-metrics","--kv-cache-metrics-sample","1.0",
            "--cudagraph-metrics",
            "--enable-mfu-metrics",
            "--enable-logging-iteration-details",
        ]
        server_cmd += ["--enable-prefix-caching" if case.get("prefix_caching") else "--no-enable-prefix-caching"]
        if case.get("kv_cache_memory_bytes"):
            server_cmd += ["--kv-cache-memory-bytes",str(case["kv_cache_memory_bytes"])]
        if float(case.get("offload_gib",0))>0:
            server_cmd += ["--kv-offloading-size",str(case["offload_gib"]),
                           "--kv-offloading-backend","native"]

        (cdir/"SERVER_COMMAND.txt").write_text(q(server_cmd)+"\n")
        case_rec={
            "name":case["name"],"purpose":case.get("purpose"),
            "transferability":case.get("transferability"),
            "tp":case["tp"],"pp":case.get("pp",1),
            "max_num_batched_tokens":case["max_num_batched_tokens"],
            "prefix_caching":bool(case.get("prefix_caching")),
            "offload_gib":case.get("offload_gib",0),
            "kv_cache_memory_bytes":case.get("kv_cache_memory_bytes"),
            "server_command":server_cmd,"server_start":time.time(),"benchmarks":[]
        }
        server_proc=None
        try:
            subprocess.run("sudo fuser -k -9 /dev/nvidia* 2>/dev/null || true", shell=True)
            time.sleep(2)
            env=os.environ.copy()
            env["CUDA_HOME"] = "/usr/local/cuda"
            env["PATH"] = "/usr/local/cuda/bin:" + env.get("PATH", "")
            env["LD_LIBRARY_PATH"] = "/usr/local/cuda/lib64:" + env.get("LD_LIBRARY_PATH", "")
            env["CPATH"] = "/usr/local/cuda/include:" + env.get("CPATH", "")
            env["VLLM_TORCH_PROFILER_DIR"] = str(cdir/"torch_profile")
            env["FLASHINFER_DISABLE_AUTOTUNE"] = "1"
            server_proc=subprocess.Popen(server_cmd,stdout=server_log,stderr=subprocess.STDOUT,
                                         text=True,env=env,start_new_session=True)
            wait_ready(f"http://127.0.0.1:{args.port}",server_proc,args.startup_timeout)
            case_rec["server_ready"]=time.time()

            for bi,b in enumerate(case["benchmarks"]):
                bdir=cdir/b["name"]; bdir.mkdir(exist_ok=True)
                result_file=f"{b['name']}.json"

                metrics_cmd=[py,sampler,
                             "--url",f"http://127.0.0.1:{args.port}/metrics",
                             "--interval","0.5",
                             "--out",str(bdir/"metrics_gpu.jsonl"),
                             "--raw-prom",str(bdir/"metrics_raw.prom.log")]
                (bdir/"METRICS_COMMAND.txt").write_text(q(metrics_cmd)+"\n")
                metrics_proc=subprocess.Popen(metrics_cmd,stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT)
                time.sleep(2)

                bench_cmd=[
                    vllm,"bench","serve",
                    "--backend","openai",
                    "--host","127.0.0.1","--port",str(args.port),
                    "--endpoint","/v1/completions",
                    "--model",model,
                    "--trust-remote-code",
                    "--dataset-name","random",
                    "--random-input-len",str(b["input"]),
                    "--random-output-len",str(b["output"]),
                    "--random-range-ratio","0",
                    "--num-prompts",str(b["prompts"]),
                    "--max-concurrency",str(b["concurrency"]),
                    "--ignore-eos",
                    "--num-warmups",str(b.get("warmups",1)),
                    "--percentile-metrics","ttft,tpot,itl,e2el",
                    "--metric-percentiles","50,95,99",
                    "--save-result","--save-detailed",
                    "--result-dir",str(bdir),
                    "--result-filename",result_file,
                    "--seed",str(args.seed_base+ci*100+bi)
                ]
                if b.get("prefix"):
                    bench_cmd += ["--random-prefix-len",str(b["prefix"])]
                (bdir/"COMMAND.txt").write_text(q(bench_cmd)+"\n")
                t0=time.time()
                with (bdir/"bench_stdout.log").open("w") as log:
                    rc=subprocess.call(bench_cmd,stdout=log,stderr=subprocess.STDOUT,env=env)
                t1=time.time()
                case_rec["benchmarks"].append({
                    **b,"command":bench_cmd,"start":t0,"end":t1,"exit_code":rc,
                    "result_json":str(bdir/result_file),
                    "stdout":str(bdir/"bench_stdout.log"),
                })
                # small cool-down so the metrics sampler captures a post-run state
                time.sleep(3)
                stop_proc(metrics_proc)
                metrics_proc=None
                if server_proc.poll() is not None:
                    print(f"Server died during benchmark {b['name']} with rc={server_proc.returncode}")
                    break

        except Exception as e:
            case_rec["error"]=repr(e)
        finally:
            case_rec["server_end"]=time.time()
            if 'metrics_proc' in locals() and metrics_proc: stop_proc(metrics_proc)
            if server_proc:
                stop_proc(server_proc)
                subprocess.run("sudo fuser -k -9 /dev/nvidia* 2>/dev/null || true", shell=True)
                time.sleep(2)
                server_proc=None
            server_log.close()
            (cdir/"case_manifest.json").write_text(json.dumps(case_rec,indent=2))
            top_manifest["cases"].append(case_rec)

    top_manifest["ended"]=time.time()
    (out/"vllm_surrogate_manifest.json").write_text(json.dumps(top_manifest,indent=2))
    print(f"Wrote {out/'vllm_surrogate_manifest.json'}")

if __name__=="__main__":
    main()
