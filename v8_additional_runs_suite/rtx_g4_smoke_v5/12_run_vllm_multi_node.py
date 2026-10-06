#!/usr/bin/env python3
"""Run one or more multi-node Ray vLLM cases after Ray has been formed by 12_run_vllm_multi_node.sh.
Captures central Prometheus metrics, GPU telemetry on both nodes, and Ray placement snapshots.
"""
from __future__ import annotations
import argparse, json, os, shlex, shutil, subprocess, sys, time
from pathlib import Path
from v5_runner_lib import *

def ssh_base(key, host): return ["ssh","-i",key,"-o","BatchMode=yes","-o","ConnectTimeout=20","-o","StrictHostKeyChecking=no","-o","UserKnownHostsFile=/dev/null",host]
def scp_base(key): return ["scp","-i",key,"-o","BatchMode=yes","-o","ConnectTimeout=20","-o","StrictHostKeyChecking=no","-o","UserKnownHostsFile=/dev/null"]

def start_remote_sampler(key, host, remote_py, remote_out, gpu_csv, interval):
    cmd=ssh_base(key,host)+[f"nohup python3 {shlex.quote(remote_py)} --gpu-only --interval {interval} --out {shlex.quote(remote_out)} --gpu-indices {shlex.quote(gpu_csv)} --node-label node1 >/tmp/v5_sampler.out 2>&1 & echo $!"]
    p=subprocess.run(cmd,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=False)
    if p.returncode!=0: return None,p.stderr
    try: return int(p.stdout.strip().splitlines()[-1]),None
    except Exception: return None,f"could not parse remote PID: {p.stdout!r}"

def stop_remote_sampler(key,host,pid,remote_out,local_out):
    if pid:
        subprocess.run(ssh_base(key,host)+[f"kill {pid} 2>/dev/null || true"],check=False,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        time.sleep(1)
    subprocess.run(scp_base(key)+[f"{host}:{remote_out}",str(local_out)],check=False,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)

def ray_snapshot(outdir:Path,label:str):
    for name,cmd in {
        "status":["ray","status"],
        "nodes":["ray","list","nodes","--detail"],
        "actors":["ray","list","actors","--detail"],
        "placement_groups":["ray","list","placement-groups","--detail"],
    }.items():
        r=run_capture(cmd,timeout=60); (outdir/f"ray_{label}_{name}.log").write_text(r["out"])

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--cases",default=str(Path(__file__).with_name("10b_vllm_multi_node_cases.json")))
    ap.add_argument("--out",required=True)
    ap.add_argument("--case",action="append",default=[])
    ap.add_argument("--group",action="append",default=[])
    ap.add_argument("--all",action="store_true")
    ap.add_argument("--port",type=int,default=8000)
    ap.add_argument("--startup-timeout",type=int,default=3600)
    ap.add_argument("--seed-base",type=int,default=5000)
    ap.add_argument("--node1-ip",default=os.environ.get("NODE1_IP"))
    ap.add_argument("--ssh-key",default=os.environ.get("SSH_KEY",str(Path.home()/".ssh/google_compute_engine")))
    ap.add_argument("--remote-sampler",default="/tmp/v5_metrics_sampler.py")
    ap.add_argument("--dry-run",action="store_true")
    args=ap.parse_args()
    if not args.node1_ip: raise SystemExit("NODE1_IP not set. Source RUN_CONFIG.env or pass --node1-ip.")

    cfg=json.loads(Path(args.cases).read_text()); model=cfg["model"]
    cases=choose_cases(cfg,args.case,args.group,args.all)
    out=Path(args.out).resolve(); out.mkdir(parents=True,exist_ok=True)
    vllm=shutil.which("vllm"); py=sys.executable
    if not vllm: raise SystemExit("vllm CLI not found")
    sampler=str(Path(__file__).with_name("09_metrics_sampler.py").resolve())
    serve_help=cli_help(vllm,["serve"]); bench_help=cli_help(vllm,["bench","serve"])
    top={"schema_version":2,"model":model,"revision":cfg.get("revision"),"evidence_class":"MEASURED-48B",
         "network_provenance":os.environ.get("GCP_NETWORK_PROVENANCE","GCP_UNSPECIFIED"),
         "nccl_transport_provenance":os.environ.get("NCCL_TRANSPORT_PROVENANCE","UNSPECIFIED"),
         "configured_network_cap_gbps":os.environ.get("V8_VLLM_NETWORK_CAP_GBPS","0"),
         "network_mode":os.environ.get("V8_VLLM_NETWORK_MODE","native"),
         "started":time.time(),"environment":environment_manifest(vllm),"cases":[]}

    for ci,case in enumerate(cases):
        cdir=out/case["name"]; cdir.mkdir(parents=True,exist_ok=True)
        ray_snapshot(cdir,"before_server")
        gpus=case.get("gpu_indices",list(range(int(case.get("ray_gpus_per_node",8)))))
        gpu_csv=",".join(map(str,gpus)); env=os.environ.copy(); env["CUDA_VISIBLE_DEVICES"]=gpu_csv
        server_cmd=build_server_cmd(vllm,serve_help,cfg,case,model,args.port,distributed=True)
        (cdir/"SERVER_COMMAND.txt").write_text(q(server_cmd)+"\n")
        rec={"name":case["name"],"groups":case.get("groups",[]),"purpose":case.get("purpose"),"tp":case["tp"],"pp":case.get("pp",1),
             "ray_gpus_per_node":case.get("ray_gpus_per_node"),"physical_gpu_indices_each_node":gpus,
             "max_num_batched_tokens":case["max_num_batched_tokens"],"max_num_seqs":case.get("max_num_seqs"),
             "kv_cache_dtype":resolved(case,cfg,"kv_cache_dtype","auto"),
             "network_provenance":os.environ.get("GCP_NETWORK_PROVENANCE","GCP_UNSPECIFIED"),
             "configured_network_cap_gbps":os.environ.get("V8_VLLM_NETWORK_CAP_GBPS","0"),
             "network_mode":os.environ.get("V8_VLLM_NETWORK_MODE","native"),
             "nccl_transport_provenance":os.environ.get("NCCL_TRANSPORT_PROVENANCE","UNSPECIFIED"),
             "server_command":server_cmd,"benchmarks":[]}
        if args.dry_run:
            top["cases"].append(rec); continue
        server_log=(cdir/"server.log").open("w",buffering=1); server_proc=None; local_sampler=None; remote_pid=None; remote_out=None
        try:
            rec["server_start"]=time.time(); server_proc=subprocess.Popen(server_cmd,stdout=server_log,stderr=subprocess.STDOUT,text=True,env=env,start_new_session=True)
            models=wait_ready(f"http://127.0.0.1:{args.port}",server_proc,args.startup_timeout)
            rec["server_ready"]=time.time(); rec["models_endpoint"]=models; ray_snapshot(cdir,"server_ready")
            observations={}
            for bi,b in enumerate(case["benchmarks"]):
                bdir=cdir/b["name"]; bdir.mkdir(exist_ok=True)
                allow,reason=gate_allows(b.get("gate"),observations)
                if not allow:
                    brec={**b,"status":"SKIPPED_BY_SAFETY_GATE","gate_reason":reason,"exit_code":None}
                    rec["benchmarks"].append(brec); observations[b["name"]]=brec
                    (bdir/"SKIPPED.txt").write_text(reason+"\n")
                    continue
                warm=run_warmup(vllm,bench_help,model,args.port,b,bdir,args.seed_base+ci*1000+bi*10,env)
                (bdir/"warmup_manifest.json").write_text(json.dumps(warm,indent=2))
                if warm.get("ran") and warm.get("exit_code")!=0:
                    brec={**b,"status":"WARMUP_FAILED","exit_code":warm.get("exit_code")}
                    rec["benchmarks"].append(brec); observations[b["name"]]=brec; continue
                interval=float(case.get("metrics_interval_s",cfg["server_defaults"].get("metrics_interval_s",0.5)))
                lcmd=[py,sampler,"--url",f"http://127.0.0.1:{args.port}/metrics","--interval",str(interval),"--out",str(bdir/"metrics_node0.jsonl"),
                      "--raw-prom",str(bdir/"metrics_raw.prom.log"),"--gpu-indices",gpu_csv,"--node-label","node0"]
                local_sampler=subprocess.Popen(lcmd,stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT,env=env)
                remote_out=f"/tmp/v5_{os.getpid()}_{case['name']}_{b['name']}.jsonl"
                remote_pid,remote_err=start_remote_sampler(args.ssh_key,args.node1_ip,args.remote_sampler,remote_out,gpu_csv,interval)
                time.sleep(max(1.0,2*interval))
                result_file=f"{b['name']}.json"; bench_cmd=build_bench_cmd(vllm,bench_help,model,args.port,b,bdir,result_file,args.seed_base+ci*1000+bi,True)
                (bdir/"COMMAND.txt").write_text(q(bench_cmd)+"\n")
                t0=time.time()
                with (bdir/"bench_stdout.log").open("w") as log: rc=subprocess.call(bench_cmd,stdout=log,stderr=subprocess.STDOUT,env=env)
                t1=time.time(); time.sleep(max(1.0,2*interval)); stop_proc(local_sampler); local_sampler=None
                stop_remote_sampler(args.ssh_key,args.node1_ip,remote_pid,remote_out,bdir/"metrics_node1.jsonl"); remote_pid=None
                result=parse_result(bdir/result_file); qm=quick_metrics(bdir/"metrics_node0.jsonl"); lens=validate_result_lengths(result,b)
                brec={**b,"status":"COMPLETED" if rc==0 else "FAILED","command":bench_cmd,"start":t0,"end":t1,"exit_code":rc,
                      "result_json":str(bdir/result_file),"remote_sampler_error":remote_err,"warmup_separate":True,
                      "gate_applied":bool(b.get("gate")),"gate_reason":"GATE_PASSED" if b.get("gate") else "NO_GATE",**qm,**lens}
                rec["benchmarks"].append(brec); observations[b["name"]]=brec
        except Exception as e:
            rec["error"]=repr(e); rec["status"]="FAILED"
        finally:
            if local_sampler: stop_proc(local_sampler)
            if remote_pid and remote_out: stop_remote_sampler(args.ssh_key,args.node1_ip,remote_pid,remote_out,cdir/"remote_sampler_unrecovered.jsonl")
            rec["server_end"]=time.time(); kill_process_group(server_proc); server_log.close(); ray_snapshot(cdir,"after_server")
            if "status" not in rec:
                states=[x.get("status") for x in rec.get("benchmarks",[])]
                rec["status"]="COMPLETED" if states and all(x in ("COMPLETED","SKIPPED_BY_SAFETY_GATE") for x in states) else ("FAILED" if any(x in ("FAILED","WARMUP_FAILED") for x in states) else "INCOMPLETE")
            (cdir/"case_manifest.json").write_text(json.dumps(rec,indent=2)); top["cases"].append(rec)
    top["ended"]=time.time(); (out/"vllm_surrogate_manifest.json").write_text(json.dumps(top,indent=2)); print(f"Wrote {out/'vllm_surrogate_manifest.json'}")

if __name__=="__main__": main()
