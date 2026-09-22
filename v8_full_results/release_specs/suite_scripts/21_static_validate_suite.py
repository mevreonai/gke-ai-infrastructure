#!/usr/bin/env python3
"""Static V8-FULL source-tree validation. Safe without GPUs/vLLM."""
from __future__ import annotations
import argparse, hashlib, json, py_compile, re, subprocess
from pathlib import Path

def sha(p:Path): return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--root',type=Path,default=Path(__file__).parent); ap.add_argument('--out',type=Path,default=None); a=ap.parse_args()
    root=a.root.resolve(); out=(a.out or root/'STATIC_VALIDATION.json').resolve(); checks=[]
    def add(name,ok,detail=''): checks.append({'name':name,'ok':bool(ok),'detail':str(detail)})

    # Syntax checks.
    for p in root.rglob('*.py'):
        try: py_compile.compile(str(p),doraise=True); add(f'py_compile:{p.relative_to(root)}',True)
        except Exception as e: add(f'py_compile:{p.relative_to(root)}',False,repr(e))
    for p in root.rglob('*.sh'):
        r=subprocess.run(['bash','-n',str(p)],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        add(f'bash_n:{p.relative_to(root)}',r.returncode==0,r.stdout[-2000:])
    for p in root.rglob('*.json'):
        try: d=json.loads(p.read_text()); add(f'json:{p.relative_to(root)}',True)
        except Exception as e: add(f'json:{p.relative_to(root)}',False,repr(e)); continue
        if isinstance(d,dict) and isinstance(d.get('cases'),list):
            names=[c.get('name') for c in d['cases']]; add(f'unique_cases:{p.name}',len(names)==len(set(names)))
            for c in d['cases']:
                seen=[]
                for b in c.get('benchmarks',[]):
                    after=(b.get('gate') or {}).get('after')
                    add(f'gate_order:{p.name}:{c.get("name")}:{b.get("name")}',not after or after in seen,f'after={after}, seen={seen}')
                    seen.append(b.get('name'))

    # V6 byte-identity for intentionally preserved files.
    cm=root/'V6_COMPATIBILITY_MANIFEST.json'
    if cm.exists():
        d=json.loads(cm.read_text())
        for rel,expected in d.get('sha256',{}).items():
            p=root/rel; actual=sha(p) if p.exists() else 'MISSING'
            add(f'v6_compat:{rel}',p.exists() and actual==expected,f'expected={expected} actual={actual}')
    else: add('v6_compat_manifest_present',False)

    # Required V8 artifacts.
    required=['00_run_v8_full.sh','90_collect_and_validate.py','99_package_v8_full_results.sh','V6_ALIGNMENT_EVIDENCE.json',
              'rtx_g4_smoke_v5/10d_v8_1m_extended_cases.json','rtx_g4_smoke_v5/20_nccl_policy.sh',
              'rtx_g4_smoke_v5/20_run_single_node_v6_aligned.sh','rtx_g4_smoke_v5/20_ray_nccl_env_audit.py','rtx_g4_smoke_v5/20_run_vllm_network_matrix.sh','rtx_g4_smoke_v5/22_v8_readiness.py',
              'rtx_g4_smoke_v5/21_run_vllm_capped_profiles.sh','rtx_g4_smoke_v5/18_multi_node_profile_matrix.json',
              'rtx_g4_smoke_v5/18_run_vllm_multi_node_profiles.sh','rtx_g4_smoke_v5/18_run_vllm_multi_node_profile_case.py',
              'rtx_g4_smoke_v5/19_postprocess_nsys.py','rtx_g4_smoke_v8_hw/07_validate_results.py']
    for rel in required: add(f'required:{rel}',(root/rel).exists())

    # V6 alignment evidence must show zero forbidden source hits and empty actual qualification NCCL env.
    ev=json.loads((root/'V6_ALIGNMENT_EVIDENCE.json').read_text())
    add('v6_source_has_no_forbidden_p2p_shm_flags',ev.get('v6_source_forbidden_flag_hits')==[],ev.get('v6_source_forbidden_flag_hits'))
    add('v6_qualification_env_empty',ev.get('v6_qualification_environment_manifest_env')=={},ev.get('v6_qualification_environment_manifest_env'))
    add('legacy_hw_forced_flags_identified',all(ev.get('legacy_20260915_forced_flags',{}).values()),ev.get('legacy_20260915_tp8_local_nccl_forced_command'))

    # Four scale-out topologies must include 128K, 512K, 1M with 1M gated after 512K.
    md=json.loads((root/'rtx_g4_smoke_v5/10b_vllm_multi_node_cases.json').read_text())
    expected={'tp4_pp2_dist','tp8_pp2_dist','tp4_pp4_dist','tp16_pp1_dist'}; got=set()
    for c in md['cases']:
        if c['name'] not in expected: continue
        bs={b['name']:b for b in c.get('benchmarks',[])}
        ok=all(x in bs for x in ('128k_c1','512k_c1','1m_c1')) and (bs['1m_c1'].get('gate') or {}).get('after')=='512k_c1'
        add(f'scaleout_context_matrix:{c["name"]}',ok)
        if ok: got.add(c['name'])
    add('scaleout_1m_all_four',got==expected,f'got={sorted(got)}')

    # Profiler matrix coverage.
    pm=json.loads((root/'rtx_g4_smoke_v5/18_multi_node_profile_matrix.json').read_text())
    pairs={(x['topology'],x['mode']) for x in pm['profiles']}
    for topo in sorted(expected):
        for mode in ('prefill_128k','decode_8k','batched_decode_8k_c8'):
            add(f'profile_matrix:{topo}:{mode}',(topo,mode) in pairs)

    # NCCL policy: local native clears all NCCL_*; single-node wrapper clears all; multi-node clears local-forcing only.
    hw=(root/'rtx_g4_smoke_v8_hw/02_run_node_local.sh').read_text()
    common=(root/'rtx_g4_smoke_v8_hw/00_smoke_common.sh').read_text()
    pol=(root/'rtx_g4_smoke_v5/20_nccl_policy.sh').read_text()
    multi=(root/'rtx_g4_smoke_v5/12_run_vllm_multi_node.sh').read_text()
    add('hw_native_clears_nccl_env','nccl_sanitize_local_native' in hw and "grep '^NCCL_'" in common)
    add('single_node_clears_all_nccl','nccl_clear_all_for_single_node' in pol)
    add('multi_node_clears_local_forcing','nccl_multi_node_v6_aligned_env' in multi and 'unset NCCL_P2P_DISABLE NCCL_SHM_DISABLE NCCL_P2P_LEVEL' in multi)
    add('multi_node_ray_worker_env_audit','20_ray_nccl_env_audit.py' in multi)
    prof=(root/'rtx_g4_smoke_v5/18_run_vllm_multi_node_profiles.sh').read_text()
    add('profile_ray_worker_env_audit','20_ray_nccl_env_audit.py' in prof)
    add('remote_allowed_nccl_env_propagated','REMOTE_V6_ENV' in multi and 'nccl_remote_v6_aligned_exports' in pol)
    add('profile_remote_allowed_nccl_env_propagated','REMOTE_V6_ENV' in prof and 'nccl_remote_v6_aligned_exports' in pol)
    raya=(root/'rtx_g4_smoke_v5/20_ray_nccl_env_audit.py').read_text()
    add('ray_audit_checks_env_symmetry','NCCL_ENV_MISMATCH' in raya and 'LD_LIBRARY_PATH_MISMATCH' in raya)
    hwnet=(root/'rtx_g4_smoke_v8_hw/03_run_network_sweep.sh').read_text()
    add('network_hw_clears_local_forcing','unset NCCL_P2P_DISABLE NCCL_SHM_DISABLE NCCL_P2P_LEVEL' in hwnet and 'REMOTE_FORBIDDEN' in hwnet)

    # Executable assignments of P2P/SHM-disabling flags: SHM disable must be zero; P2P_DISABLE=1 only one sensitivity assignment.
    assignment_hits=[]
    for p in list(root.rglob('*.sh'))+list(root.rglob('*.py')):
        txt=p.read_text(errors='ignore')
        for m in re.finditer(r'\b(NCCL_P2P_DISABLE|NCCL_SHM_DISABLE)\s*=\s*1\b',txt):
            assignment_hits.append((str(p.relative_to(root)),m.group(1),txt[max(0,m.start()-120):m.end()+120]))
    shm=[x for x in assignment_hits if x[1]=='NCCL_SHM_DISABLE']
    p2p=[x for x in assignment_hits if x[1]=='NCCL_P2P_DISABLE']
    add('no_executable_nccl_shm_disable_assignments',len(shm)==0,shm)
    allowed_p2p=(len(p2p)==1 and p2p[0][0]=='rtx_g4_smoke_v8_hw/02_run_node_local.sh' and 'SENSITIVITY_ONLY=1' in p2p[0][2])
    add('p2p_disable_only_sensitivity',allowed_p2p,p2p)

    # vLLM network modes exactly Native/100G/20G; no 50G/10G in vLLM model matrix.
    nm=(root/'rtx_g4_smoke_v5/20_run_vllm_network_matrix.sh').read_text()
    add('vllm_network_modes_native_100_20','VLLM_NETWORK_MODES:=native 100g 20g' in nm)
    add('vllm_network_matrix_no_50g_10g',not re.search(r'\b(50g|10g)\b',nm,re.I), '50G/10G should remain only in hardware microbench sweep')
    hws=(root/'rtx_g4_smoke_v8_hw/03_run_network_sweep.sh').read_text()
    add('hardware_network_sweep_keeps_100_50_20_10','for RATE in 100 50 20 10' in hws)
    add('hardware_network_sweep_forward_reverse_iperf','iperf_${tag}.raw.json' in hws and 'iperf_${tag}_reverse.raw.json' in hws)
    add('hardware_network_sweep_sendrecv_all_caps','run_sendrecv "$TAG" "$RATE"' in hws)
    add('hardware_network_sweep_tp2_tp8_tp16_all_caps','run_crossnode_ar "$TAG" "$RATE"' in hws and 'TP2:1' in hws and 'TP8:4' in hws and 'TP16:8' in hws)
    add('hardware_tc_noninteractive','sudo -n tc' in hws)

    # Capped profiler subset is explicit and limited to 100G/20G 128K prefill.
    cp=(root/'rtx_g4_smoke_v5/21_run_vllm_capped_profiles.sh').read_text()
    add('capped_profiles_100_20','CAPPED_PROFILE_MODES:=100g 20g' in cp)
    add('capped_profiles_prefill128k_only','PROFILE_MODE_FILTER=prefill_128k' in cp)

    # Master defaults and no stale V7 executable paths.
    master=(root/'00_run_v8_full.sh').read_text()
    add('master_v8_results_root','v8_full_results' in master)
    add('master_network_modes','VLLM_NETWORK_MODES:=native 100g 20g' in master)
    add('master_runs_capped_profiles','RUN_CAPPED_PROFILE:=1' in master and '21_run_vllm_capped_profiles.sh' in master)
    add('master_runs_readiness_both_nodes','readiness_node0' in master and 'readiness_node1' in master and '22_v8_readiness.py' in master)
    stale=[]
    for p in list(root.rglob('*.sh'))+list(root.rglob('*.py')):
        if p.resolve()==Path(__file__).resolve(): continue
        t=p.read_text(errors='ignore')
        if 'v7_full_results' in t or '00_run_v7_full.sh' in t or '99_package_v7_full_results.sh' in t:
            stale.append(str(p.relative_to(root)))
    add('no_stale_v7_executable_paths',not stale,stale)

    payload={'schema_version':2,'root':str(root),'ok':all(x['ok'] for x in checks),'checks':checks,'failed':[x for x in checks if not x['ok']]}
    out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(payload,indent=2))
    print(json.dumps({'ok':payload['ok'],'checks':len(checks),'failed':len(payload['failed']),'out':str(out)},indent=2))
    raise SystemExit(0 if payload['ok'] else 2)

if __name__=='__main__': main()
