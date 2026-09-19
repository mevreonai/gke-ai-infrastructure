#!/usr/bin/env python3
"""Single-node V5 runner for Kimi-Linear-48B.
Key correctness properties:
- exact HF revision passed to vLLM server
- TP4 samples only selected GPUs
- per-case KV dtype is honored
- warmup is outside the measured telemetry window
- actual token lengths are validated from detailed result JSON
- 512K/1M concurrency can be capacity-gated
- request_rate/burstiness/probe loads are supported
"""
from __future__ import annotations
import argparse, json, os, shutil, subprocess, sys, time
from pathlib import Path
from v5_runner_lib import *

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--cases",default=str(Path(__file__).with_name("10_vllm_surrogate_cases.json")))
    ap.add_argument("--out",required=True)
    ap.add_argument("--case",action="append",default=[])
    ap.add_argument("--group",action="append",default=[])
    ap.add_argument("--all",action="store_true")
    ap.add_argument("--port",type=int,default=8000)
    ap.add_argument("--startup-timeout",type=int,default=3600)
    ap.add_argument("--seed-base",type=int,default=1000)
    ap.add_argument("--dry-run",action="store_true")
    args=ap.parse_args()

    cfg=json.loads(Path(args.cases).read_text()); model=cfg["model"]
    cases=choose_cases(cfg,args.case,args.group,args.all)
    out=Path(args.out).resolve(); out.mkdir(parents=True,exist_ok=True)
    vllm=shutil.which("vllm")
    if not vllm: raise SystemExit("vllm CLI not found; activate the same vllm_env used for prior runs.")
    py=sys.executable; sampler=str(Path(__file__).with_name("09_metrics_sampler.py").resolve())
    serve_help=cli_help(vllm,["serve"]); bench_help=cli_help(vllm,["bench","serve"])

    top={"schema_version":2,"model":model,"revision":cfg.get("revision"),"evidence_class":cfg.get("evidence_class","MEASURED-48B"),
         "guardrail":cfg.get("guardrail"),"started":time.time(),"source_cases":str(Path(args.cases).resolve()),
         "environment":environment_manifest(vllm),"cases":[]}

    for ci,case in enumerate(cases):
        cdir=out/case["name"]; cdir.mkdir(parents=True,exist_ok=True)
        gpus=case.get("gpu_indices",list(range(int(case["tp"]))))
        gpu_csv=",".join(map(str,gpus))
        env=os.environ.copy(); env["CUDA_VISIBLE_DEVICES"]=gpu_csv
        server_cmd=build_server_cmd(vllm,serve_help,cfg,case,model,args.port,distributed=False)
        (cdir/"SERVER_COMMAND.txt").write_text(q(server_cmd)+"\n")
        case_rec={"name":case["name"],"groups":case.get("groups",[]),"purpose":case.get("purpose"),"tp":case["tp"],"pp":case.get("pp",1),
                  "physical_gpu_indices":gpus,"cuda_visible_devices":gpu_csv,"max_num_batched_tokens":case["max_num_batched_tokens"],
                  "max_num_seqs":case.get("max_num_seqs"),"max_num_active_seqs":case.get("max_num_active_seqs"),
                  "kv_cache_dtype":resolved(case,cfg,"kv_cache_dtype","auto"),"kv_cache_memory_bytes":case.get("kv_cache_memory_bytes"),
                  "offload_gib_total_across_tp":case.get("offload_gib",0),"prefix_caching":bool(case.get("prefix_caching")),
                  "observability_profile":resolved(case,cfg,"observability_profile","full"),"server_command":server_cmd,"benchmarks":[]}
        if case.get("offload_gib"):
            case_rec["offload_gib_per_tp_rank_derived"] = float(case["offload_gib"])/int(case["tp"])
        if args.dry_run:
            for bi,b in enumerate(case["benchmarks"]):
                bdir=cdir/b["name"]; bdir.mkdir(exist_ok=True)
                cmd=build_bench_cmd(vllm,bench_help,model,args.port,b,bdir,f"{b['name']}.json",args.seed_base+ci*100+bi,True)
                (bdir/"COMMAND.txt").write_text(q(cmd)+"\n")
                case_rec["benchmarks"].append({**b,"planned_command":cmd,"dry_run":True})
            top["cases"].append(case_rec); continue

        server_log=(cdir/"server.log").open("w",buffering=1); server_proc=None; metrics_proc=None
        observations={}
        try:
            case_rec["server_start"]=time.time()
            server_proc=subprocess.Popen(server_cmd,stdout=server_log,stderr=subprocess.STDOUT,text=True,env=env,start_new_session=True)
            models=wait_ready(f"http://127.0.0.1:{args.port}",server_proc,args.startup_timeout)
            case_rec["server_ready"]=time.time(); case_rec["models_endpoint"]=models
            (cdir/"resolved_models.json").write_text(json.dumps(models,indent=2))

            for bi,b in enumerate(case["benchmarks"]):
                bdir=cdir/b["name"]; bdir.mkdir(exist_ok=True)
                allow,reason=gate_allows(b.get("gate"),observations)
                if not allow:
                    rec={**b,"status":"SKIPPED_BY_SAFETY_GATE","gate_reason":reason,"exit_code":None}
                    case_rec["benchmarks"].append(rec); observations[b["name"]]=rec
                    (bdir/"SKIPPED.txt").write_text(reason+"\n"); continue

                warm=run_warmup(vllm,bench_help,model,args.port,b,bdir,args.seed_base+ci*1000+bi*10,env)
                (bdir/"warmup_manifest.json").write_text(json.dumps(warm,indent=2))
                if warm.get("ran") and warm.get("exit_code")!=0:
                    rec={**b,"status":"WARMUP_FAILED","exit_code":warm.get("exit_code")}
                    case_rec["benchmarks"].append(rec); observations[b["name"]]=rec; continue
                time.sleep(1)

                interval=float(case.get("metrics_interval_s",cfg["server_defaults"].get("metrics_interval_s",0.5)))
                metrics_cmd=[py,sampler,"--url",f"http://127.0.0.1:{args.port}/metrics","--interval",str(interval),
                             "--out",str(bdir/"metrics_gpu.jsonl"),"--raw-prom",str(bdir/"metrics_raw.prom.log"),
                             "--gpu-indices",gpu_csv,"--node-label","node0"]
                (bdir/"METRICS_COMMAND.txt").write_text(q(metrics_cmd)+"\n")
                metrics_proc=subprocess.Popen(metrics_cmd,stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT,env=env)
                time.sleep(max(1.0,2*interval))
                result_file=f"{b['name']}.json"
                bench_cmd=build_bench_cmd(vllm,bench_help,model,args.port,b,bdir,result_file,args.seed_base+ci*1000+bi,
                                          True,{"case":case["name"],"bench":b["name"],"revision":cfg.get("revision","")})
                (bdir/"COMMAND.txt").write_text(q(bench_cmd)+"\n")
                t0=time.time()
                with (bdir/"bench_stdout.log").open("w") as log:
                    rc=subprocess.call(bench_cmd,stdout=log,stderr=subprocess.STDOUT,env=env)
                t1=time.time(); time.sleep(max(1.0,2*interval)); stop_proc(metrics_proc); metrics_proc=None
                result_path=bdir/result_file; result=parse_result(result_path); qm=quick_metrics(bdir/"metrics_gpu.jsonl")
                lens=validate_result_lengths(result,b)
                rec={**b,"status":"COMPLETED" if rc==0 else "FAILED","command":bench_cmd,"start":t0,"end":t1,"exit_code":rc,
                     "result_json":str(result_path),"stdout":str(bdir/"bench_stdout.log"),"warmup_separate":True,
                     "request_rate":b.get("request_rate","inf"),"burstiness":b.get("burstiness"),"probe_request_rate":b.get("probe_request_rate"),
                     **qm,**lens}
                case_rec["benchmarks"].append(rec); observations[b["name"]]=rec
        except Exception as e:
            case_rec["error"]=repr(e)
        finally:
            case_rec["server_end"]=time.time()
            if metrics_proc: stop_proc(metrics_proc)
            kill_process_group(server_proc); server_log.close()
            (cdir/"case_manifest.json").write_text(json.dumps(case_rec,indent=2)); top["cases"].append(case_rec)

    top["ended"]=time.time(); (out/"vllm_surrogate_manifest.json").write_text(json.dumps(top,indent=2))
    print(f"Wrote {out/'vllm_surrogate_manifest.json'}")

if __name__=="__main__": main()
