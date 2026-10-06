#!/usr/bin/env python3
"""Audit the environment inherited by one Ray task on every live node.

V8-FULL fails if legacy local-transport forcing is present or if the allowed
network NCCL environment on a worker differs from the driver.  This makes the
GCP Socket workaround/interface binding symmetric across both Ray nodes rather
than merely checking the node-0 shell.
"""
from __future__ import annotations
import argparse, json, os, socket, time
from pathlib import Path

FORBIDDEN=("NCCL_P2P_DISABLE","NCCL_SHM_DISABLE","NCCL_P2P_LEVEL")


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    ap.add_argument('--expected-nodes', type=int, default=2)
    args=ap.parse_args()
    import ray
    from ray.util.scheduling_strategies import NodeAffinitySchedulingStrategy

    expected_nccl={k:v for k,v in os.environ.items() if k.startswith('NCCL_') and k not in FORBIDDEN}
    expected_ld=os.environ.get('LD_LIBRARY_PATH')
    ray.init(address='auto', ignore_reinit_error=True, logging_level='ERROR')
    nodes=[n for n in ray.nodes() if n.get('Alive')]

    @ray.remote(num_cpus=0)
    def snap():
        return {
            'hostname':socket.gethostname(),
            'pid':os.getpid(),
            'env':{k:v for k,v in os.environ.items() if k.startswith('NCCL_')},
            'ld_library_path':os.environ.get('LD_LIBRARY_PATH'),
        }

    rows=[]
    for n in nodes:
        node_id=n['NodeID']
        r=ray.get(snap.options(
            scheduling_strategy=NodeAffinitySchedulingStrategy(node_id=node_id, soft=False)
        ).remote())
        r['node_id']=node_id; r['node_manager_address']=n.get('NodeManagerAddress'); rows.append(r)

    violations=[]
    for r in rows:
        for k in FORBIDDEN:
            if k in r['env']:
                violations.append({'type':'FORBIDDEN_LOCAL_TRANSPORT_OVERRIDE','node_id':r['node_id'],
                                   'hostname':r['hostname'],'variable':k,'value':r['env'][k]})
        for k,v in expected_nccl.items():
            if r['env'].get(k) != v:
                violations.append({'type':'NCCL_ENV_MISMATCH','node_id':r['node_id'],'hostname':r['hostname'],
                                   'variable':k,'expected':v,'actual':r['env'].get(k)})
        if expected_ld is not None and r.get('ld_library_path') != expected_ld:
            violations.append({'type':'LD_LIBRARY_PATH_MISMATCH','node_id':r['node_id'],'hostname':r['hostname'],
                               'expected':expected_ld,'actual':r.get('ld_library_path')})

    payload={
        'schema_version':2,'timestamp':time.time(),'expected_nodes':args.expected_nodes,
        'live_nodes':len(nodes),'driver_expected_nccl_env':expected_nccl,
        'driver_expected_ld_library_path':expected_ld,'workers':rows,
        'forbidden_variables':list(FORBIDDEN),'violations':violations,
        'ok':len(nodes)==args.expected_nodes and not violations,
        'interpretation':(
            'Validates actual Ray-task inherited environment on every live node before vLLM actor creation. '
            'It rejects legacy P2P/SHM forcing and mismatched allowed NCCL network settings. '
            'It does not infer the physical transport chosen by NCCL from performance.'
        )
    }
    p=Path(args.out); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(payload,indent=2))
    print(json.dumps(payload,indent=2))
    raise SystemExit(0 if payload['ok'] else 2)

if __name__=='__main__': main()
