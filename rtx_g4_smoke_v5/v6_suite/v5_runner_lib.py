#!/usr/bin/env python3
from __future__ import annotations
import json, math, os, platform, shlex, shutil, signal, subprocess, sys, time
from pathlib import Path
from urllib.request import urlopen

def q(cmd): return " ".join(shlex.quote(str(x)) for x in cmd)

def stop_proc(p):
    if not p: return
    if p.poll() is None:
        p.terminate()
        try: p.wait(timeout=20)
        except subprocess.TimeoutExpired:
            p.kill(); p.wait(timeout=10)

def run_capture(cmd, timeout=120):
    try:
        p=subprocess.run(cmd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=timeout,check=False)
        return {"rc":p.returncode,"out":p.stdout}
    except Exception as e: return {"rc":None,"out":repr(e)}

def cli_help(vllm, parts):
    return run_capture([vllm]+list(parts)+["--help=all"], timeout=120)["out"]

def require_flag(help_text, flag, where):
    if flag not in help_text:
        raise RuntimeError(f"Required CLI flag {flag} is not supported by installed {where}. Run 07_preflight_v5.py and use the same vLLM environment.")

def add_if_supported(cmd, help_text, flag, *values):
    if flag in help_text: cmd += [flag, *map(str,values)]; return True
    return False

def wait_ready(base, proc, timeout):
    end=time.time()+timeout; last=None
    while time.time()<end:
        if proc.poll() is not None: raise RuntimeError(f"server exited rc={proc.returncode}")
        try:
            with urlopen(base+"/v1/models",timeout=5) as r:
                if r.status==200: return json.loads(r.read().decode("utf-8","replace"))
        except Exception as e: last=e
        time.sleep(2)
    raise TimeoutError(f"server not ready after {timeout}s; last={last!r}")

def environment_manifest(vllm):
    cmds={
      "vllm_version":[vllm,"--version"],
      "nvidia_smi":["nvidia-smi","--query-gpu=index,uuid,name,memory.total,pci.bus_id","--format=csv,noheader,nounits"],
      "nvidia_topo":["nvidia-smi","topo","-m"],
      "python_packages":[sys.executable,"-m","pip","freeze"],
    }
    rec={"time":time.time(),"host":platform.node(),"python":sys.version,"commands":{},
         "env":{k:v for k,v in os.environ.items() if k.startswith(("NCCL_","CUDA_","VLLM_","RAY_"))}}
    for k,c in cmds.items(): rec["commands"][k]={"cmd":c,**run_capture(c,timeout=120)}
    return rec

def choose_cases(cfg, names, groups, run_all=False):
    names=set(names or []); groups=set(groups or [])
    out=[]
    for c in cfg["cases"]:
        if run_all or c.get("name") in names or groups.intersection(c.get("groups",[])): out.append(c)
    if not out: raise SystemExit("No cases selected. Use --group qualification, --group <name>, --case <name>, or --all.")
    unknown=names-{c["name"] for c in cfg["cases"]}
    if unknown: raise SystemExit(f"Unknown case(s): {sorted(unknown)}")
    return out

def resolved(case, cfg, key, default=None):
    if key in case: return case[key]
    return cfg.get("server_defaults",{}).get(key,default)

def build_server_cmd(vllm, serve_help, cfg, case, model, port, distributed=False):
    for flag in ("--tensor-parallel-size","--pipeline-parallel-size","--max-model-len","--max-num-batched-tokens","--kv-cache-dtype","--revision"):
        require_flag(serve_help,flag,"vllm serve")
    cmd=[vllm,"serve",model]
    add_if_supported(cmd,serve_help,"--model-impl","vllm")
    if "--trust-remote-code" in serve_help: cmd += ["--trust-remote-code"]
    cmd += ["--revision",str(cfg["revision"]),"--host","0.0.0.0","--port",str(port),
            "--tensor-parallel-size",str(case["tp"]),"--pipeline-parallel-size",str(case.get("pp",1)),
            "--max-model-len",str(resolved(case,cfg,"max_model_len")),
            "--max-num-batched-tokens",str(case["max_num_batched_tokens"]),
            "--kv-cache-dtype",str(resolved(case,cfg,"kv_cache_dtype","auto"))]
    if distributed:
        require_flag(serve_help,"--distributed-executor-backend","vllm serve")
        cmd += ["--distributed-executor-backend","ray"]
    if case.get("max_num_seqs") is not None:
        require_flag(serve_help,"--max-num-seqs","vllm serve"); cmd += ["--max-num-seqs",str(case["max_num_seqs"])]
    if case.get("max_num_active_seqs") is not None:
        require_flag(serve_help,"--max-num-active-seqs","vllm serve"); cmd += ["--max-num-active-seqs",str(case["max_num_active_seqs"])]
    if case.get("kv_cache_memory_bytes") is not None:
        require_flag(serve_help,"--kv-cache-memory-bytes","vllm serve")
        cmd += ["--kv-cache-memory-bytes",str(case["kv_cache_memory_bytes"])]
    else:
        gmu=resolved(case,cfg,"gpu_memory_utilization",0.9)
        require_flag(serve_help,"--gpu-memory-utilization","vllm serve")
        cmd += ["--gpu-memory-utilization",str(gmu)]
    pm=resolved(case,cfg,"performance_mode")
    if pm is not None: add_if_supported(cmd,serve_help,"--performance-mode",pm)
    ol=resolved(case,cfg,"optimization_level")
    if ol is not None: add_if_supported(cmd,serve_help,"--optimization-level",ol)

    if case.get("prefix_caching",False):
        require_flag(serve_help,"--enable-prefix-caching","vllm serve"); cmd += ["--enable-prefix-caching"]
    else:
        require_flag(serve_help,"--no-enable-prefix-caching","vllm serve"); cmd += ["--no-enable-prefix-caching"]
    if float(case.get("offload_gib",0) or 0)>0:
        require_flag(serve_help,"--kv-offloading-size","vllm serve")
        cmd += ["--kv-offloading-size",str(case["offload_gib"])]
        add_if_supported(cmd,serve_help,"--kv-offloading-backend","native")

    obs=resolved(case,cfg,"observability_profile","full")
    if obs=="full":
        if "--kv-cache-metrics" in serve_help: cmd += ["--kv-cache-metrics"]
        if "--kv-cache-metrics-sample" in serve_help: cmd += ["--kv-cache-metrics-sample","1.0"]
        for f in ("--cudagraph-metrics","--enable-mfu-metrics","--enable-logging-iteration-details"):
            if f in serve_help: cmd += [f]
    return cmd

def dataset_expected_input(b):
    if b.get("dataset")=="prefix_repetition": return int(b.get("prefix",0))+int(b.get("suffix",0))
    return int(b["input"])

def build_bench_cmd(vllm, bench_help, model, port, b, outdir, result_file, seed, measured=True, metadata=None):
    for flag in ("--dataset-name","--num-prompts","--max-concurrency","--num-warmups"):
        require_flag(bench_help,flag,"vllm bench serve")
    dataset=b.get("dataset","random")
    cmd=[vllm,"bench","serve","--backend","openai","--host","127.0.0.1","--port",str(port),
         "--endpoint","/v1/completions","--model",model]
    if "--trust-remote-code" in bench_help: cmd += ["--trust-remote-code"]
    cmd += ["--dataset-name",dataset]
    if dataset=="prefix_repetition":
        for f in ("--prefix-repetition-prefix-len","--prefix-repetition-suffix-len","--prefix-repetition-num-prefixes","--prefix-repetition-output-len"):
            require_flag(bench_help,f,"vllm bench serve")
        cmd += ["--prefix-repetition-prefix-len",str(b["prefix"]),"--prefix-repetition-suffix-len",str(b.get("suffix",256)),
                "--prefix-repetition-num-prefixes",str(b.get("num_prefixes",1)),"--prefix-repetition-output-len",str(b["output"])]
    else:
        cmd += ["--random-input-len",str(b["input"]),"--random-output-len",str(b["output"]),"--random-range-ratio","0"]
    cmd += ["--num-prompts",str(b["prompts"]),"--max-concurrency",str(b["concurrency"]),"--ignore-eos","--num-warmups","0",
            "--percentile-metrics","ttft,tpot,itl,e2el","--metric-percentiles","50,95,99","--seed",str(seed)]
    if b.get("request_rate") is not None:
        require_flag(bench_help,"--request-rate","vllm bench serve"); cmd += ["--request-rate",str(b["request_rate"])]
        if b.get("burstiness") is not None:
            require_flag(bench_help,"--burstiness","vllm bench serve"); cmd += ["--burstiness",str(b["burstiness"])]
    if b.get("probe_request_rate") is not None:
        require_flag(bench_help,"--probe-request-rate","vllm bench serve"); cmd += ["--probe-request-rate",str(b["probe_request_rate"])]
    for k,flag in (("ramp_up_strategy","--ramp-up-strategy"),("ramp_up_start_rps","--ramp-up-start-rps"),("ramp_up_end_rps","--ramp-up-end-rps")):
        if b.get(k) is not None: require_flag(bench_help,flag,"vllm bench serve"); cmd += [flag,str(b[k])]
    if measured:
        cmd += ["--save-result","--save-detailed","--result-dir",str(outdir),"--result-filename",result_file]
        if metadata and "--metadata" in bench_help:
            cmd += ["--metadata"] + [f"{k}={v}" for k,v in metadata.items()]
    return cmd

def run_warmup(vllm, bench_help, model, port, b, bdir, seed, env):
    n=int(b.get("warmups",0) or 0)
    if n<=0: return {"ran":False}
    wb=dict(b); wb["prompts"]=n; wb["concurrency"]=min(max(1,int(b.get("concurrency",1))),n)
    cmd=build_bench_cmd(vllm,bench_help,model,port,wb,bdir,"unused.json",seed,measured=False)
    t0=time.time()
    with (bdir/"warmup_stdout.log").open("w") as log: rc=subprocess.call(cmd,stdout=log,stderr=subprocess.STDOUT,env=env)
    return {"ran":True,"command":cmd,"start":t0,"end":time.time(),"exit_code":rc}

def parse_result(path:Path):
    if not path.exists(): return {}
    try: return json.loads(path.read_text())
    except Exception: return {}

def quick_metrics(path:Path):
    peak_kv=None; pre0=None; pre1=None; samples=0
    if not path.exists(): return {"peak_kv_usage":None,"preemptions_delta":None,"metric_samples":0}
    for line in path.read_text(errors="ignore").splitlines():
        try: r=json.loads(line)
        except Exception: continue
        if r.get("kind")!="prometheus": continue
        samples+=1
        for m in r.get("metrics",[]):
            n=m.get("name"); v=float(m.get("value",0))
            if n=="vllm:kv_cache_usage_perc": peak_kv=v if peak_kv is None else max(peak_kv,v)
            if n in ("vllm:num_preemptions_total","vllm:num_preemptions"):
                if pre0 is None: pre0=v
                pre1=v
    return {"peak_kv_usage":peak_kv,"preemptions_delta":None if pre0 is None or pre1 is None else pre1-pre0,"metric_samples":samples}

def validate_result_lengths(result, b):
    expected=dataset_expected_input(b); xs=result.get("input_lens") or []
    ys=result.get("output_lens") or []
    rec={"expected_input_tokens":expected,"requested_output_tokens":int(b["output"]),"input_lens_count":len(xs),"output_lens_count":len(ys)}
    if xs:
        rec.update({"actual_input_min":min(xs),"actual_input_max":max(xs),"actual_input_mean":sum(xs)/len(xs),
                    "input_len_exact_match":all(int(x)==expected for x in xs)})
    else: rec["input_len_exact_match"]=None
    if ys: rec.update({"actual_output_min":min(ys),"actual_output_max":max(ys),"actual_output_mean":sum(ys)/len(ys)})
    return rec

def gate_allows(gate, observations):
    if not gate: return True,"NO_GATE"
    src=observations.get(gate.get("after"))
    if not src: return False,"GATE_SOURCE_MISSING"
    if src.get("exit_code")!=0: return False,"PRIOR_BENCH_FAILED"
    kv=src.get("peak_kv_usage")
    if gate.get("max_peak_kv_usage") is not None:
        if kv is None: return False,"KV_METRIC_NOT_CAPTURED"
        if kv>float(gate["max_peak_kv_usage"]): return False,f"KV_USAGE_{kv:.3f}_ABOVE_GATE"
    pre=src.get("preemptions_delta")
    if gate.get("max_preemptions") is not None:
        if pre is None: return False,"PREEMPTION_METRIC_NOT_CAPTURED"
        if pre>float(gate["max_preemptions"]): return False,f"PREEMPTIONS_{pre}_ABOVE_GATE"
    return True,"GATE_PASSED"

def kill_process_group(proc):
    if not proc: return
    try:
        if proc.poll() is None: os.killpg(proc.pid,signal.SIGTERM); proc.wait(timeout=30)
    except Exception:
        try: os.killpg(proc.pid,signal.SIGKILL)
        except Exception: pass
