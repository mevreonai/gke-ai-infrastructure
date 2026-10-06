#!/usr/bin/env python3
"""Run one targeted distributed vLLM workload against an already-formed Ray cluster.
The Ray worker processes are expected to have been started under Nsight Systems on BOTH nodes
by 18_run_vllm_multi_node_profiles.sh. This script triggers vLLM's profiler API via
`vllm bench serve --profile` and captures benchmark + Prometheus + per-node GPU telemetry.
"""
from __future__ import annotations
import argparse, json, os, shlex, shutil, subprocess, sys, time
from pathlib import Path
from v5_runner_lib import *

def ssh_base(key, host):
    return ["ssh","-i",key,"-o","BatchMode=yes","-o","ConnectTimeout=20","-o","StrictHostKeyChecking=no","-o","UserKnownHostsFile=/dev/null",host]
def scp_base(key):
    return ["scp","-i",key,"-o","BatchMode=yes","-o","ConnectTimeout=20","-o","StrictHostKeyChecking=no","-o","UserKnownHostsFile=/dev/null"]

def start_remote_sampler(key, host, remote_py, remote_out, gpu_csv, interval):
    cmd=ssh_base(key,host)+[f"nohup python3 {shlex.quote(remote_py)} --gpu-only --interval {interval} --out {shlex.quote(remote_out)} --gpu-indices {shlex.quote(gpu_csv)} --node-label node1 >/tmp/v8full_prof_sampler.out 2>&1 & echo $!"]
    p=subprocess.run(cmd,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=False)
    if p.returncode!=0: return None,p.stderr
    try: return int(p.stdout.strip().splitlines()[-1]),None
    except Exception: return None,f"could not parse remote PID: {p.stdout!r}"

def stop_remote_sampler(key,host,pid,remote_out,local_out):
    if pid:
        subprocess.run(ssh_base(key,host)+[f"kill {pid} 2>/dev/null || true"],check=False,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        time.sleep(1)
    subprocess.run(scp_base(key)+[f"{host}:{remote_out}",str(local_out)],check=False,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)

def snap(outdir,label):
    for name,cmd in {
        'ray_status':['ray','status'],
        'ray_nodes':['ray','list','nodes','--detail'],
        'ray_actors':['ray','list','actors','--detail'],
        'nvidia_topo':['nvidia-smi','topo','-m'],
        'nvidia_inventory':['nvidia-smi','--query-gpu=index,uuid,name,memory.total,pci.bus_id','--format=csv,noheader,nounits'],
    }.items():
        r=run_capture(cmd,timeout=90); (outdir/f'{label}_{name}.log').write_text(r['out'])

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--topology',required=True)
    ap.add_argument('--tp',type=int,required=True); ap.add_argument('--pp',type=int,required=True)
    ap.add_argument('--ray-gpus-per-node',type=int,required=True)
    ap.add_argument('--mode',required=True); ap.add_argument('--input',type=int,required=True)
    ap.add_argument('--output',type=int,required=True); ap.add_argument('--concurrency',type=int,required=True)
    ap.add_argument('--prompts',type=int,required=True); ap.add_argument('--out',required=True)
    ap.add_argument('--port',type=int,default=8020); ap.add_argument('--startup-timeout',type=int,default=3600)
    ap.add_argument('--node1-ip',default=os.environ.get('NODE1_IP')); ap.add_argument('--ssh-key',default=os.environ.get('SSH_KEY',str(Path.home()/'.ssh/google_compute_engine')))
    ap.add_argument('--remote-sampler',default='/tmp/v5_metrics_sampler.py')
    args=ap.parse_args()
    if not args.node1_ip: raise SystemExit('NODE1_IP missing')
    out=Path(args.out).resolve(); out.mkdir(parents=True,exist_ok=True)
    vllm=shutil.which('vllm'); py=sys.executable
    if not vllm: raise SystemExit('vllm CLI not found')
    sampler=str(Path(__file__).with_name('09_metrics_sampler.py').resolve())
    serve_help=cli_help(vllm,['serve']); bench_help=cli_help(vllm,['bench','serve'])
    if '--profile' not in bench_help: raise SystemExit('vllm bench serve --profile not supported by installed vLLM')
    if '--ray-workers-use-nsight' not in serve_help:
        raise SystemExit('vLLM --ray-workers-use-nsight is unavailable; distributed worker profiling is not enabled in this environment')
    if '--profiler-config' not in serve_help and '--profiler-config.profiler' not in serve_help:
        raise SystemExit('vLLM profiler-config capability not found; refuse to claim a distributed profile')
    cfg=json.loads(Path(__file__).with_name('10b_vllm_multi_node_cases.json').read_text())
    model=cfg['model']
    case={
      'name':args.topology,'tp':args.tp,'pp':args.pp,'ray_gpus_per_node':args.ray_gpus_per_node,
      'gpu_indices':list(range(args.ray_gpus_per_node)),'max_num_batched_tokens':8192,
      'max_num_seqs':max(8,args.concurrency),'prefix_caching':False,'offload_gib':0,
      'observability_profile':'full'
    }
    env=os.environ.copy(); gpu_csv=','.join(map(str,case['gpu_indices'])); env['CUDA_VISIBLE_DEVICES']=gpu_csv
    env['VLLM_WORKER_MULTIPROC_METHOD']='spawn'
    server_cmd=build_server_cmd(vllm,serve_help,cfg,case,model,args.port,distributed=True)
    if '--enforce-eager' in serve_help: server_cmd += ['--enforce-eager']
    if '--enable-layerwise-nvtx-tracing' in serve_help: server_cmd += ['--enable-layerwise-nvtx-tracing']
    server_cmd += ['--ray-workers-use-nsight']
    # Existing V6 profiler path used nested profiler config successfully. Preserve that behavior.
    if '--profiler-config.profiler' in serve_help or '--profiler-config' in serve_help:
        server_cmd += ['--profiler-config.profiler','cuda']
    (out/'SERVER_COMMAND.txt').write_text(q(server_cmd)+'\n')
    profile_bench={'name':args.mode,'input':args.input,'output':args.output,'concurrency':args.concurrency,'prompts':args.prompts,'warmups':0}
    manifest={
      'schema_version':1,'evidence_class':'MEASURED-48B-PROFILE','topology':args.topology,'tp':args.tp,'pp':args.pp,
      'mode':args.mode,'input':args.input,'output':args.output,'concurrency':args.concurrency,'prompts':args.prompts,
      'model':model,'revision':cfg.get('revision'),'network_provenance':os.environ.get('GCP_NETWORK_PROVENANCE','GCP_UNSPECIFIED'),
      'nccl_transport_provenance':os.environ.get('NCCL_TRANSPORT_PROVENANCE','UNSPECIFIED'),
      'network_mode':os.environ.get('V8_VLLM_NETWORK_MODE','native'),
      'configured_network_cap_gbps':os.environ.get('V8_VLLM_NETWORK_CAP_GBPS','0'),
      'environment':environment_manifest(vllm),'server_command':server_cmd,'started':time.time()
    }
    server_log=(out/'server.log').open('w',buffering=1); proc=None; local_sampler=None; remote_pid=None
    try:
        snap(out,'before')
        proc=subprocess.Popen(server_cmd,stdout=server_log,stderr=subprocess.STDOUT,text=True,env=env,start_new_session=True)
        manifest['models_endpoint']=wait_ready(f'http://127.0.0.1:{args.port}',proc,args.startup_timeout)
        snap(out,'ready')
        interval=0.25
        lcmd=[py,sampler,'--url',f'http://127.0.0.1:{args.port}/metrics','--interval',str(interval),'--out',str(out/'metrics_node0.jsonl'),'--raw-prom',str(out/'metrics_raw.prom.log'),'--gpu-indices',gpu_csv,'--node-label','node0']
        local_sampler=subprocess.Popen(lcmd,stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT,env=env)
        remote_out=f"/tmp/v8full_profile_{os.getpid()}_{args.topology}_{args.mode}.jsonl"
        remote_pid,remote_err=start_remote_sampler(args.ssh_key,args.node1_ip,args.remote_sampler,remote_out,gpu_csv,interval)
        manifest['remote_sampler_error']=remote_err
        time.sleep(1.0)
        bench_cmd=build_bench_cmd(vllm,bench_help,model,args.port,profile_bench,out,'bench.json',7000,True)
        bench_cmd += ['--profile']
        (out/'BENCH_COMMAND.txt').write_text(q(bench_cmd)+'\n')
        t0=time.time()
        with (out/'bench.log').open('w') as f: rc=subprocess.call(bench_cmd,stdout=f,stderr=subprocess.STDOUT,env=env)
        manifest['bench_start']=t0; manifest['bench_end']=time.time(); manifest['bench_exit_code']=rc
        result=parse_result(out/'bench.json'); manifest.update(validate_result_lengths(result,profile_bench))
        manifest.update(quick_metrics(out/'metrics_node0.jsonl'))
        manifest['status']='COMPLETED' if rc==0 else 'FAILED'
    except Exception as e:
        manifest['status']='FAILED'; manifest['error']=repr(e)
    finally:
        if local_sampler: stop_proc(local_sampler)
        if remote_pid: stop_remote_sampler(args.ssh_key,args.node1_ip,remote_pid,remote_out,out/'metrics_node1.jsonl')
        kill_process_group(proc); server_log.close(); snap(out,'after')
        manifest['ended']=time.time(); (out/'PROFILE_CASE_MANIFEST.json').write_text(json.dumps(manifest,indent=2))
    print(json.dumps({'out':str(out),'status':manifest.get('status')},indent=2))
    raise SystemExit(0 if manifest.get('status')=='COMPLETED' else 2)
if __name__=='__main__': main()
