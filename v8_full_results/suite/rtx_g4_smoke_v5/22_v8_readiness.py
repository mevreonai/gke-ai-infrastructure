#!/usr/bin/env python3
"""V8-FULL fail-fast node readiness validation.

This is deliberately separate from the byte-identical V6 preflight.  It verifies
that the environment still matches the known-good V6 core stack by default and
that the additional V8 distributed/profile capabilities are available before
expensive GPU work starts.
"""
from __future__ import annotations
import argparse, importlib.metadata as md, json, os, shutil, subprocess, sys, time
from pathlib import Path

EXPECTED_V6 = {
    "vllm": "0.29.0",
    "ray": "2.58.0",
    "torch": "2.13.0",
    "triton": "3.7.1",
    "flashinfer-python": "0.6.18",
    "nvidia-nccl-cu13": "2.29.7",
}
FORBIDDEN = ("NCCL_P2P_DISABLE", "NCCL_SHM_DISABLE", "NCCL_P2P_LEVEL")


def run(cmd, timeout=120):
    try:
        p = subprocess.run(cmd, text=True, stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT, timeout=timeout, check=False)
        return {"cmd": cmd, "rc": p.returncode, "out": p.stdout}
    except Exception as e:
        return {"cmd": cmd, "rc": None, "out": repr(e)}


def pkgver(name):
    try: return md.version(name)
    except Exception: return None


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    ap.add_argument('--require-v6-stack', type=int,
                    default=int(os.environ.get('V8_REQUIRE_V6_CORE_STACK','1')))
    ap.add_argument('--expected-gpus', type=int, default=int(os.environ.get('V8_EXPECTED_GPUS_PER_NODE','8')))
    ap.add_argument('--min-free-gib', type=float, default=float(os.environ.get('V8_MIN_FREE_GIB','100')))
    a=ap.parse_args()
    out=Path(a.out); out.mkdir(parents=True,exist_ok=True)
    checks=[]
    def ck(name, ok, detail=None, severity='ERROR'):
        checks.append({'name':name,'ok':bool(ok),'detail':detail,'severity':severity})

    # Executables and CLI capabilities.
    bins={x:shutil.which(x) for x in ('vllm','ray','nsys','nvidia-smi','iperf3','tc','python3')}
    for k,v in bins.items(): ck(f'bin:{k}', bool(v), v)
    serve=run([bins['vllm'],'serve','--help=all'],180) if bins['vllm'] else {'rc':None,'out':''}
    if not serve.get('out') or '--tensor-parallel-size' not in serve['out']:
        serve=run([bins['vllm'],'serve','--help'],180) if bins['vllm'] else {'rc':None,'out':''}
    bench=run([bins['vllm'],'bench','serve','--help=all'],180) if bins['vllm'] else {'rc':None,'out':''}
    if not bench.get('out') or '--request-rate' not in bench['out']:
        bench=run([bins['vllm'],'bench','serve','--help'],180) if bins['vllm'] else {'rc':None,'out':''}
    for flag in ('--distributed-executor-backend','--ray-workers-use-nsight','--profiler-config',
                 '--tensor-parallel-size','--pipeline-parallel-size','--no-enable-prefix-caching'):
        ck(f'vllm_serve_flag:{flag}', flag in serve['out'])
    ck('vllm_bench_flag:--profile','--profile' in bench['out'])
    for flag in ('--request-rate','--max-concurrency','--save-result','--save-detailed'):
        ck(f'vllm_bench_flag:{flag}',flag in bench['out'])

    # Exact package versions from the actual successful V6 qualification.
    versions={k:pkgver(k) for k in EXPECTED_V6}
    for k,exp in EXPECTED_V6.items():
        ok=(versions[k]==exp) if a.require_v6_stack else versions[k] is not None
        ck(f'v6_stack:{k}',ok,{'expected':exp,'actual':versions[k],'strict':bool(a.require_v6_stack)})

    # GPU identity/count/memory.  Memory threshold is intentionally loose enough
    # to recognize the 96GB class device while not depending on MiB/GiB wording.
    smi=run(['nvidia-smi','--query-gpu=index,uuid,name,memory.total,pci.bus_id','--format=csv,noheader,nounits']) if bins['nvidia-smi'] else {'rc':None,'out':''}
    rows=[x.strip() for x in smi['out'].splitlines() if x.strip()]
    ck('gpu_count',len(rows)==a.expected_gpus,{'expected':a.expected_gpus,'actual':len(rows),'rows':rows})
    ck('gpu_model_rtx_pro_6000_blackwell', bool(rows) and all('RTX PRO 6000 Blackwell' in x for x in rows), rows)
    mem=[]
    for r in rows:
        try: mem.append(float(r.split(',')[3].strip()))
        except Exception: pass
    ck('gpu_memory_96gb_class',len(mem)==len(rows) and bool(mem) and min(mem)>90000,mem)

    # Disk capacity for traces/evidence.  It is a fail-fast guard but configurable.
    du=shutil.disk_usage(str(Path.home()))
    free_gib=du.free/(1024**3)
    ck('disk_free',free_gib>=a.min_free_gib,{'free_gib':round(free_gib,2),'required_gib':a.min_free_gib})

    # Local transport forcing must be absent.  Allowed network-only NCCL variables
    # (e.g. NCCL_NET=Socket) may still be present for multi-node GCP.
    env_nccl={k:v for k,v in os.environ.items() if k.startswith('NCCL_')}
    forbidden={k:env_nccl[k] for k in FORBIDDEN if k in env_nccl}
    ck('no_forbidden_local_nccl_overrides',not forbidden,forbidden)

    # If the V6 GCP Socket workaround is active, verify its library directory is
    # actually usable on this node before Ray is started.
    if os.environ.get('NCCL_NET') == 'Socket' or '/tmp/clean_nccl_libs' in os.environ.get('LD_LIBRARY_PATH',''):
        d=Path('/tmp/clean_nccl_libs')
        nccl=list(d.glob('libnccl.so*')) if d.exists() else []
        ck('socket_workaround:clean_nccl_dir',d.is_dir(),str(d))
        ck('socket_workaround:libnccl_present',bool(nccl),[str(x) for x in nccl])
        net=d/'libnccl-net.so'
        ck('socket_workaround:net_plugin_disabled',net.is_symlink() and os.path.realpath(net)=='/dev/null',
           {'path':str(net),'is_symlink':net.is_symlink(),'target':os.path.realpath(net) if net.exists() or net.is_symlink() else None})

    payload={
      'schema_version':1,'timestamp':time.time(),'python':sys.version,'require_v6_stack':bool(a.require_v6_stack),
      'expected_v6_versions':EXPECTED_V6,'actual_versions':versions,'executables':bins,
      'vllm_serve_help_rc':serve.get('rc'),'vllm_bench_help_rc':bench.get('rc'),'gpu_inventory':rows,
      'nccl_env':env_nccl,'checks':checks,'ok':all(x['ok'] for x in checks),
      'failed':[x for x in checks if not x['ok']]
    }
    (out/'V8_READINESS.json').write_text(json.dumps(payload,indent=2))
    mdlines=['# V8-FULL readiness','',f"- Overall: **{'PASS' if payload['ok'] else 'FAIL'}**",
             f"- Require exact V6 core stack: **{bool(a.require_v6_stack)}**",f"- Free disk: **{free_gib:.1f} GiB**",'',
             '| Check | Status |','|---|---|']
    mdlines += [f"| `{x['name']}` | {'PASS' if x['ok'] else 'FAIL'} |" for x in checks]
    (out/'V8_READINESS.md').write_text('\n'.join(mdlines)+'\n')
    print(json.dumps({'ok':payload['ok'],'checks':len(checks),'failed':len(payload['failed']),'out':str(out)},indent=2))
    raise SystemExit(0 if payload['ok'] else 2)

if __name__=='__main__': main()
