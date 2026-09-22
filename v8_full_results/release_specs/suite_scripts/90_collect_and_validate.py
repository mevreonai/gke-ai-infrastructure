#!/usr/bin/env python3
"""V8-FULL final collector and strict coverage/provenance validator.

Key rules:
- Missing results are never converted to zero.
- Scale-out coverage is keyed by network provenance, not only case/bench.
- Required vLLM network modes are GCP_NATIVE / GCP_CAPPED_100G / GCP_CAPPED_20G.
- Native/local evidence must not contain NCCL_P2P_DISABLE, NCCL_SHM_DISABLE, or NCCL_P2P_LEVEL.
- Safety-gated 1M rows remain valid evidence but prevent strict full-coverage sign-off.
"""
from __future__ import annotations
import argparse, csv, hashlib, json, os
from pathlib import Path
from typing import Any

REQUIRED_NETWORKS=["GCP_NATIVE","GCP_CAPPED_100G","GCP_CAPPED_20G"]
REQUIRED_TOPOLOGIES=["tp4_pp2_dist","tp8_pp2_dist","tp4_pp4_dist","tp16_pp1_dist"]
FORBIDDEN_LOCAL_NCCL=("NCCL_P2P_DISABLE","NCCL_SHM_DISABLE","NCCL_P2P_LEVEL")

def load_json(p:Path, default=None):
    try: return json.loads(p.read_text())
    except Exception: return default

def sha256_file(p:Path,block=1024*1024):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(block),b''): h.update(b)
    return h.hexdigest()

def write_csv(path:Path,rows:list[dict[str,Any]]):
    if not rows: path.write_text(''); return
    keys=[]
    for r in rows:
        for k in r:
            if k not in keys: keys.append(k)
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=keys); w.writeheader(); w.writerows(rows)

def flatten_config(path:Path,scope:str,network_provenance:str="SINGLE_NODE_LOCAL"):
    cfg=load_json(path,{}) or {}; out=[]
    for c in cfg.get('cases',[]):
        for b in c.get('benchmarks',[]):
            inp=b.get('input') if b.get('dataset')!='prefix_repetition' else int(b.get('prefix',0))+int(b.get('suffix',0))
            out.append({'scope':scope,'network_provenance':network_provenance,'case':c.get('name'),'bench':b.get('name'),
                        'tp':c.get('tp'),'pp':c.get('pp',1),'input_tokens':inp,'output_tokens':b.get('output'),
                        'concurrency':b.get('concurrency'),'has_gate':bool(b.get('gate')),'groups':c.get('groups',[]),'purpose':c.get('purpose')})
    return out

def status_class(x:dict|None):
    if not x: return 'NOT_RUN'
    s=x.get('status')
    if s=='COMPLETED' and x.get('exit_code') in (0,'0',None): return 'COMPLETED'
    if s=='SKIPPED_BY_SAFETY_GATE': return 'SAFETY_SKIPPED'
    if s in ('WARMUP_FAILED','FAILED'): return 'FAILED'
    return s or 'UNKNOWN'

def find_actual(root:Path):
    # Multiple case/bench pairs exist by network provenance; preserve every one.
    idx={}
    for p in root.rglob('case_manifest.json'):
        d=load_json(p,{}) or {}; case=d.get('name')
        net=d.get('network_provenance','SINGLE_NODE_LOCAL')
        for b in d.get('benchmarks',[]):
            idx[(net,case,b.get('name'))]={**b,'_manifest':str(p),'_case':d}
    return idx

def forbidden_env_hits(path:Path):
    try: txt=path.read_text(errors='ignore')
    except Exception: return []
    return [x for x in FORBIDDEN_LOCAL_NCCL if x in txt]

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--root',required=True,type=Path); ap.add_argument('--suite',required=True,type=Path); ap.add_argument('--strict-exit',action='store_true')
    a=ap.parse_args(); root=a.root.resolve(); suite=a.suite.resolve(); out=root/'final_validation'; out.mkdir(parents=True,exist_ok=True)

    configured=[]
    configured += flatten_config(suite/'rtx_g4_smoke_v5/10_vllm_surrogate_cases.json','SINGLE_V6_BASE')
    configured += flatten_config(suite/'rtx_g4_smoke_v5/10d_v8_1m_extended_cases.json','SINGLE_V8_1M_EXT')
    multi_cfg=suite/'rtx_g4_smoke_v5/10b_vllm_multi_node_cases.json'
    for net in REQUIRED_NETWORKS: configured += flatten_config(multi_cfg,'MULTI_V8',net)

    actual=find_actual(root)
    coverage=[]
    for e in configured:
        x=actual.get((e['network_provenance'],e['case'],e['bench']))
        coverage.append({**e,'status':status_class(x),'manifest':x.get('_manifest') if x else None,
                         'exit_code':x.get('exit_code') if x else None,'gate_reason':x.get('gate_reason') if x else None,
                         'peak_kv_usage':x.get('peak_kv_usage') if x else None,'preemptions_delta':x.get('preemptions_delta') if x else None,
                         'metric_samples':x.get('metric_samples') if x else None,'remote_sampler_error':x.get('remote_sampler_error') if x else None,
                         'input_len_exact_match':x.get('input_len_exact_match') if x else None,
                         'configured_network_cap_gbps':(x.get('_case') or {}).get('configured_network_cap_gbps') if x else None,
                         'nccl_transport_provenance':(x.get('_case') or {}).get('nccl_transport_provenance') if x else None})

    gen=root/'10c_v8_generated_load_cases.json'
    if gen.exists():
        for e in flatten_config(gen,'OPEN_LOOP_GENERATED'):
            x=actual.get(('SINGLE_NODE_LOCAL',e['case'],e['bench']))
            coverage.append({**e,'status':status_class(x),'manifest':x.get('_manifest') if x else None,
                             'exit_code':x.get('exit_code') if x else None,'gate_reason':x.get('gate_reason') if x else None,
                             'peak_kv_usage':x.get('peak_kv_usage') if x else None,'preemptions_delta':x.get('preemptions_delta') if x else None,
                             'metric_samples':x.get('metric_samples') if x else None,'remote_sampler_error':x.get('remote_sampler_error') if x else None,
                             'input_len_exact_match':x.get('input_len_exact_match') if x else None})

    combined=[]
    for p in root.rglob('summary_v8full/vllm_runs.json'):
        for r in load_json(p,[]) or []: combined.append({**r,'source_summary':str(p)})
    (out/'combined_vllm_runs.json').write_text(json.dumps(combined,indent=2)); write_csv(out/'combined_vllm_runs.csv',combined)
    (out/'coverage.json').write_text(json.dumps(coverage,indent=2)); write_csv(out/'coverage.csv',coverage)

    counts={}
    for r in coverage: counts[r['status']]=counts.get(r['status'],0)+1
    failed=[r for r in coverage if r['status'] in ('FAILED','WARMUP_FAILED','UNKNOWN')]
    not_run=[r for r in coverage if r['status']=='NOT_RUN']
    safety=[r for r in coverage if r['status']=='SAFETY_SKIPPED']

    # First-class scale-out/1M coverage by network mode.
    multi=[r for r in coverage if r['scope']=='MULTI_V8']
    scaleout_matrix={}
    for net in REQUIRED_NETWORKS:
        scaleout_matrix[net]={}
        for topo in REQUIRED_TOPOLOGIES:
            scaleout_matrix[net][topo]={}
            for bench in ('128k_c1','512k_c1','1m_c1'):
                q=[r for r in multi if r['network_provenance']==net and r['case']==topo and r['bench']==bench]
                scaleout_matrix[net][topo][bench]=q[0]['status'] if q else 'NOT_CONFIGURED'
    scaleout_1m_all=all(scaleout_matrix[n][t]['1m_c1']=='COMPLETED' for n in REQUIRED_NETWORKS for t in REQUIRED_TOPOLOGIES)

    one_m=[r for r in coverage if int(r.get('input_tokens') or 0)>=1_000_000]

    # Hardware validation.
    hw=load_json(root/'hardware_processed/validation_hw.json',{}) or {}

    # Both nodes must have passed the V8 fail-fast readiness gate.
    readiness={}
    for node in ('node0','node1'):
        d=load_json(root/f'readiness_{node}/V8_READINESS.json',{}) or {}
        readiness[node]={'present':bool(d),'ok':bool(d.get('ok')),'failed':d.get('failed',[])}
    readiness_ok=all(x['present'] and x['ok'] for x in readiness.values())

    # Profiler coverage: native full matrix + capped 128K prefill for 4 topologies x 2 caps.
    pvals=[]
    for p in root.rglob('PROFILE_VALIDATION.json'):
        d=load_json(p,{}) or {}; pvals.append({'path':str(p),**d})
    native_expected=12 + (2 if os.environ.get('RUN_HEAVY_PROFILE','1')=='1' else 0)
    capped_expected=8 if os.environ.get('RUN_CAPPED_PROFILE','1')=='1' else 0
    dist_expected=native_expected+capped_expected
    dist_complete=sum(1 for x in pvals if x.get('complete'))

    single_meta=[]
    p1=root/'profiles_single_node'
    if p1.exists():
        for p in p1.rglob('PROFILE_METADATA.json'): single_meta.append(load_json(p,{}) or {})
    torch=[]; pt=root/'profiles_torch_single_node'
    if pt.exists():
        for d in sorted(pt.glob('tp*_8k_decode')):
            torch.append({'path':str(d),'bench_json':(d/'bench.json').exists(),'server_log':(d/'server.log').exists(),
                          'trace_files':len(list((d/'torch').rglob('*'))) if (d/'torch').exists() else 0})
    torch_complete=sum(1 for x in torch if x['bench_json'] and x['server_log'] and x['trace_files']>0)

    # Runtime NCCL-policy audit. Text snapshots verify the launching shells; Ray-worker
    # audit JSONs verify the actual worker environment on each live node before vLLM actors.
    policy_files=[]
    for p in root.rglob('NCCL_ENV*.txt'):
        hits=forbidden_env_hits(p); policy_files.append({'path':str(p.relative_to(root)),'forbidden_hits':hits,'ok':not hits})
    ray_audits=[]
    for p in root.rglob('*RAY_NCCL_ENV_AUDIT.json'):
        d=load_json(p,{}) or {}
        ray_audits.append({'path':str(p.relative_to(root)),'ok':bool(d.get('ok')),'live_nodes':d.get('live_nodes'),'violations':d.get('violations',[])})
    scaleout_ray_count=sum(1 for x in ray_audits if x['path'].startswith('vllm_scaleout_network_matrix/'))
    profile_ray_count=sum(1 for x in ray_audits if x['path'].startswith('profiles_multi_node_'))
    expected_scaleout_ray=12  # four topologies x Native/100G/20G
    expected_profile_ray=dist_expected
    ray_policy_complete=(scaleout_ray_count>=expected_scaleout_ray and profile_ray_count>=expected_profile_ray and all(x['ok'] for x in ray_audits))
    policy_ok=bool(policy_files) and all(x['ok'] for x in policy_files) and ray_policy_complete
    (out/'NCCL_POLICY_AUDIT.json').write_text(json.dumps({
        'ok':policy_ok,'files':policy_files,'ray_worker_audits':ray_audits,
        'scaleout_ray_audit_count':scaleout_ray_count,'scaleout_ray_audit_expected':expected_scaleout_ray,
        'profile_ray_audit_count':profile_ray_count,'profile_ray_audit_expected':expected_profile_ray,
        'ray_policy_complete':ray_policy_complete},indent=2))

    # Network validation presence for all 3 vLLM modes.
    net_validation={}
    for net in REQUIRED_NETWORKS:
        d=root/'vllm_scaleout_network_matrix'/net/'network_validation'
        iv=load_json(d/'IPERF_VALIDATION.json',{}) or {}
        net_validation[net]={'dir_exists':d.exists(),'mode_json':(d/'NETWORK_MODE.json').exists(),
                             'iperf_forward':(d/'iperf_forward.json').exists(),'iperf_reverse':(d/'iperf_reverse.json').exists(),
                             'iperf_validation':(d/'IPERF_VALIDATION.json').exists(),'measured_forward_gbps':iv.get('measured_forward_gbps'),
                             'cap_enforced_upper_bound':iv.get('cap_enforced_upper_bound')}
    network_evidence_ok=all(v['dir_exists'] and v['mode_json'] and v['iperf_forward'] and v['iperf_validation'] and v.get('cap_enforced_upper_bound') is not False for v in net_validation.values())

    # Completed distributed model runs are required to retain both-node telemetry.
    # The benchmark remains scientifically usable if telemetry is missing, but V8 strict
    # sign-off is withheld because the package promised validation-grade raw evidence.
    scaleout_telemetry=[]
    for r in multi:
        if r['status']!='COMPLETED': continue
        mp=Path(r['manifest']) if r.get('manifest') else None
        bdir=(mp.parent/r['bench']) if mp else None
        row={'network':r['network_provenance'],'case':r['case'],'bench':r['bench'],
             'node0_metrics':bool(bdir and (bdir/'metrics_node0.jsonl').exists()),
             'node1_metrics':bool(bdir and (bdir/'metrics_node1.jsonl').exists()),
             'prometheus_raw':bool(bdir and (bdir/'metrics_raw.prom.log').exists()),
             'metric_samples':r.get('metric_samples'),'remote_sampler_error':r.get('remote_sampler_error')}
        row['ok']=row['node0_metrics'] and row['node1_metrics'] and row['prometheus_raw'] and not row['remote_sampler_error'] and (row['metric_samples'] or 0)>0
        scaleout_telemetry.append(row)
    scaleout_telemetry_ok=bool(scaleout_telemetry) and all(x['ok'] for x in scaleout_telemetry)
    (out/'SCALEOUT_TELEMETRY_AUDIT.json').write_text(json.dumps({'ok':scaleout_telemetry_ok,'rows':scaleout_telemetry},indent=2))

    # Artifact index.
    raw_index=[]; critical={'.json','.jsonl','.csv','.log','.txt','.md','.sqlite'}
    for p in root.rglob('*'):
        if not p.is_file(): continue
        rec={'path':str(p.relative_to(root)),'size_bytes':p.stat().st_size}
        if p.suffix in critical and p.stat().st_size<=64*1024*1024:
            try: rec['sha256']=sha256_file(p)
            except Exception: pass
        if p.suffix=='.nsys-rep': rec['artifact_type']='NSYS_RAW_REPORT'
        raw_index.append(rec)
    (out/'artifact_index.json').write_text(json.dumps(raw_index,indent=2))

    serving_matrix_complete=not failed and not not_run and not safety
    profiles_all_complete=(len(single_meta)>=6 and torch_complete>=2 and dist_complete>=dist_expected)
    full_suite_valid=(serving_matrix_complete and readiness_ok and bool(hw.get('all_required_ok')) and profiles_all_complete and scaleout_1m_all and policy_ok and network_evidence_ok and scaleout_telemetry_ok)
    final={'schema_version':2,'result_root':str(root),'coverage_counts':counts,'failed_count':len(failed),'not_run_count':len(not_run),
           'safety_skipped_count':len(safety),'readiness_ok':readiness_ok,'readiness':readiness,'hardware_required_ok':hw.get('all_required_ok'),'single_profile_metadata_count':len(single_meta),
           'torch_profiles_complete_count':torch_complete,'distributed_profile_validation_count':len(pvals),
           'distributed_profiles_complete_count':dist_complete,'distributed_profiles_expected':dist_expected,
           'scaleout_1m_all_networks_completed':scaleout_1m_all,'required_vllm_networks':REQUIRED_NETWORKS,
           'network_evidence_ok':network_evidence_ok,'network_validation':net_validation,'scaleout_telemetry_ok':scaleout_telemetry_ok,'nccl_policy_ok':policy_ok,
           'ray_nccl_scaleout_audits':scaleout_ray_count,'ray_nccl_scaleout_expected':expected_scaleout_ray,
           'ray_nccl_profile_audits':profile_ray_count,'ray_nccl_profile_expected':expected_profile_ray,
           'profiles_all_complete':profiles_all_complete,'serving_matrix_complete':serving_matrix_complete,
           'strict_full_coverage':full_suite_valid,'full_suite_valid':full_suite_valid,
           'note':'Safety skips are scientifically valid evidence but prevent strict full-coverage sign-off. Missing results are never treated as zero.'}
    (out/'FINAL_VALIDATION.json').write_text(json.dumps(final,indent=2))

    # Human-readable reports.
    lines=['# V8-FULL 1M Context Coverage','',
           '> 1,000,000 nominal input tokens are distinct from the 1,048,576 max-model-length setting.','',
           '| Scope | Network | Case | Bench | TP | PP | C | Status | KV peak | Preemptions | Gate |',
           '|---|---|---|---|---:|---:|---:|---|---:|---:|---|']
    for r in one_m:
        kv='' if r.get('peak_kv_usage') is None else f"{float(r['peak_kv_usage'])*100:.1f}%"
        lines.append(f"| {r['scope']} | {r['network_provenance']} | {r['case']} | {r['bench']} | {r['tp']} | {r['pp']} | {r.get('concurrency') or ''} | **{r['status']}** | {kv} | {r.get('preemptions_delta','')} | {r.get('gate_reason') or ''} |")
    (out/'ONE_MILLION_COVERAGE.md').write_text('\n'.join(lines)+'\n')

    lines=['# V8-FULL Scale-Out Network Coverage','',
           '> vLLM scale-out modes are intentionally limited to Native / 100G / 20G. 50G and 10G remain hardware/NCCL microbenchmark sensitivity points.','']
    for net in REQUIRED_NETWORKS:
        lines += [f'## {net}','', '| Topology | 128K | 512K | 1M |','|---|---|---|---|']
        for t in REQUIRED_TOPOLOGIES:
            x=scaleout_matrix[net][t]; lines.append(f"| {t} | {x['128k_c1']} | {x['512k_c1']} | {x['1m_c1']} |")
        lines.append('')
    (out/'SCALEOUT_NETWORK_COVERAGE.md').write_text('\n'.join(lines)+'\n')

    md=['# V8-FULL Final Validation','',f"- Coverage rows: **{len(coverage)}**",f"- Completed: **{counts.get('COMPLETED',0)}**",
        f"- Safety-skipped: **{counts.get('SAFETY_SKIPPED',0)}**",f"- Not run: **{counts.get('NOT_RUN',0)}**",f"- Failed: **{len(failed)}**",
        f"- Readiness both nodes: **{readiness_ok}**",f"- Hardware validation: **{hw.get('all_required_ok')}**",f"- NCCL local-policy audit: **{policy_ok}**",f"- vLLM network evidence (Native/100G/20G): **{network_evidence_ok}**",f"- Scale-out both-node telemetry: **{scaleout_telemetry_ok}**",
        f"- Distributed profiles complete: **{dist_complete}/{dist_expected}**",f"- All 12 scale-out 1M topology×network points completed: **{scaleout_1m_all}**",
        f"- Strict full coverage: **{full_suite_valid}**",'', '## Guardrails',
        '- V6 single-node native runs must have no NCCL_* overrides.',
        '- Multi-node runs may retain the V6 NCCL Socket network workaround, but never disable local P2P/SHM.',
        '- GCP_CAPPED_20G is a bandwidth-sensitivity proxy, not LOCAL_REAL_2x10G.',
        '- Aggregate Nsight kernel time is not request critical-path wall time.',
        '- 48B absolute latency/tok/s does not transfer directly to Kimi K3.']
    (out/'FINAL_VALIDATION.md').write_text('\n'.join(md)+'\n')
    print(json.dumps(final,indent=2))
    raise SystemExit(0 if (full_suite_valid or not a.strict_exit) else 2)

if __name__=='__main__': main()
