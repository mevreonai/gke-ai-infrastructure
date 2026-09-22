#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, os
from pathlib import Path

REQUIRED_CAPS=("GCP_CAPPED_100G","GCP_CAPPED_50G","GCP_CAPPED_20G","GCP_CAPPED_10G")
REQUIRED_NETWORKS=("GCP_NATIVE",)+REQUIRED_CAPS
REQUIRED_TP=("TP2","TP8","TP16")
REQUIRED_SIZES=("16k","128k","512k","64m","128m","256m")
LOCAL_SIZES=REQUIRED_SIZES


def log_ok(p: Path) -> bool:
    try: return "EXIT_CODE : 0" in p.read_text(errors="ignore")
    except Exception: return False


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('root',type=Path)
    ap.add_argument('--out',type=Path,default=None)
    ap.add_argument('--require-caps',action='store_true')
    a=ap.parse_args()
    root=a.root.resolve(); out=(a.out or root/'validation_hw.json').resolve()
    require_caps=a.require_caps or os.environ.get('RUN_NETWORK_CAPS','1')=='1'
    checks=[]
    def ck(name,ok,detail=''): checks.append({'name':name,'ok':bool(ok),'detail':detail})

    # Every node-local primitive expected by V8-FULL must exist, not merely one representative file.
    for node in ('node0','node1'):
        d=root/node
        ck(f'{node}:dir',d.is_dir(),str(d))
        names={p.name for p in d.rglob('*') if p.is_file()} if d.is_dir() else set()
        for fn in ('nvbandwidth_host_gpu.raw.json','nvbandwidth_d2d.raw.json','nvbandwidth_latency.raw.json','NCCL_ENV_NATIVE_BEFORE.txt'):
            ck(f'{node}:{fn}',fn in names)
        ck(f'{node}:babelstream_gpu0',any(n.startswith('110_babelstream_gpu0') and n.endswith('.log') for n in names))
        ck(f'{node}:babelstream_second_numa',sum(1 for n in names if n.startswith('110_babelstream_gpu') and n.endswith('.log'))>=2,sorted(n for n in names if n.startswith('110_babelstream_gpu')))
        for size in LOCAL_SIZES:
            ck(f'{node}:nccl_tp4_native_{size}',f'nccl_ar_tp4_native_{size}.json' in names)
            ck(f'{node}:nccl_tp8_native_{size}',f'nccl_ar_tp8_native_{size}.json' in names)
        for tp in (4,8):
            for kind in ('all_reduce','all_gather','reduce_scatter'):
                fn=f'130_{kind}_tp{tp}_native_curve.log'
                ck(f'{node}:curve:{kind}:tp{tp}',fn in names and log_ok(d/fn),fn)
        for level in ('SYS','PHB'):
            fn=f'140_ar_tp8_sensitivity_p2p_{level}.log'
            ck(f'{node}:sensitivity:p2p_level_{level}',fn in names and log_ok(d/fn),fn)
        fn='141_ar_tp8_sensitivity_p2p_disabled.log'
        ck(f'{node}:sensitivity:p2p_disabled',fn in names and log_ok(d/fn),fn)
        fn='150_nccl_debug_tp8_128m_native.log'
        ck(f'{node}:nccl_debug_native',fn in names and log_ok(d/fn),fn)
        # CUTLASS can only be skipped explicitly; a silent absence is invalid.
        cutlass_skip=(d/'CUTLASS_SKIPPED.txt').exists()
        cutlass_logs=[d/'160_cutlass_fp16_large_shape_reference.log',d/'161_cutlass_fp16_kimi_width_shape_reference.log']
        cutlass_ok=cutlass_skip or all(x.exists() and log_ok(x) for x in cutlass_logs)
        ck(f'{node}:cutlass_scope_or_results',cutlass_ok,{'skipped':cutlass_skip,'logs':[str(x) for x in cutlass_logs]})
        if not cutlass_skip:
            ck(f'{node}:cutlass_scope',(d/'CUTLASS_SCOPE.txt').exists())

    net=root/'network_node0'
    ck('network:dir',net.is_dir(),str(net))
    names={p.name for p in net.rglob('*') if p.is_file()} if net.is_dir() else set()
    required_networks=REQUIRED_NETWORKS if require_caps else ('GCP_NATIVE',)
    if require_caps: ck('network:caps_not_skipped',not (net/'CAPS_SKIPPED.txt').exists())
    for tag in required_networks:
        ck(f'network:{tag}:iperf',(net/f'iperf_{tag}.raw.json').exists())
        ck(f'network:{tag}:iperf_reverse',(net/f'iperf_{tag}_reverse.raw.json').exists())
        iv=net/f'iperf_{tag}.validation.json'
        d=json.loads(iv.read_text()) if iv.exists() else {}
        ck(f'network:{tag}:iperf_validation',iv.exists() and d.get('measurement_ok') is True and d.get('cap_enforced_upper_bound') is True,d)
        for size in REQUIRED_SIZES:
            fn=f'nccl_sendrecv_{tag}_{size}.json'
            ck(f'network:{tag}:sendrecv:{size}',fn in names,fn)
        for tp in REQUIRED_TP:
            logs=list(net.glob(f'225_crossnode_ar_{tp}_{tag}.log'))
            ck(f'network:{tag}:crossnode_{tp}',bool(logs) and all(log_ok(x) for x in logs),[str(x) for x in logs])

    # Preserve explicit environment and verbose native debug evidence.
    ck('network:nccl_env_node0',(net/'NCCL_ENV_NETWORK_NODE0.txt').exists())
    ck('network:nccl_env_node1',(net/'NCCL_ENV_NETWORK_NODE1.txt').exists())
    dbg=net/'240_nccl_debug_sendrecv_native_128m.log'
    ck('network:nccl_debug_native_sendrecv',dbg.exists() and log_ok(dbg),str(dbg))

    # Any structured benchmark log that does not show successful completion invalidates the smoke layer.
    bad=[]
    for p in root.rglob('*.log'):
        if p.stat().st_size>=20_000_000: continue
        txt=p.read_text(errors='ignore')
        if 'TEST      :' in txt and 'EXIT_CODE : 0' not in txt:
            bad.append(str(p.relative_to(root)))
    ck('structured_benchmark_logs_exit_zero',not bad,bad[:200])

    payload={'schema_version':2,'root':str(root),'require_caps':require_caps,'required_networks':required_networks,
             'checks':checks,'all_required_ok':all(x['ok'] for x in checks),
             'failed':[x for x in checks if not x['ok']]}
    out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(payload,indent=2))
    print(json.dumps({'all_required_ok':payload['all_required_ok'],'checks':len(checks),'failed':len(payload['failed']),'out':str(out)},indent=2))
    raise SystemExit(0 if payload['all_required_ok'] else 2)

if __name__=='__main__': main()
