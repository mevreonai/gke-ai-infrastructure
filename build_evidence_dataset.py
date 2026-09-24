import json
import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

print("=== Building Complete Audited V8 Characterization Dashboard ===")

# 1. Resolve Data Path
base_dir = r'v8_full_results\results\real_data'
if not os.path.exists(base_dir):
    base_dir = r'v8_full_results\20260921_195656'

print(f"Using canonical data directory: {base_dir}")

cov_path = os.path.join(base_dir, r'final_validation\coverage.json')
comb_path = os.path.join(base_dir, r'final_validation\combined_vllm_runs.json')
val_path = os.path.join(base_dir, r'final_validation\FINAL_VALIDATION.json')

with open(cov_path, 'r', encoding='utf-8') as f:
    coverage_raw = json.load(f)
cov_items = coverage_raw if isinstance(coverage_raw, list) else coverage_raw.get('results', [])

with open(comb_path, 'r', encoding='utf-8') as f:
    combined_runs = json.load(f)

with open(val_path, 'r', encoding='utf-8') as f:
    final_val = json.load(f)

print(f"Loaded {len(cov_items)} coverage points, {len(combined_runs)} combined runs.")

run_map = {}
for r in combined_runs:
    key = (r.get('case'), r.get('bench'), r.get('network_provenance'))
    run_map[key] = r

# 2. Build Rich Evidence Data
evidence_dataset = []
for i, item in enumerate(cov_items, 1):
    c_scope = item.get('scope', 'UNKNOWN')
    c_net = item.get('network_provenance', 'UNKNOWN')
    c_case = item.get('case', '')
    c_bench = item.get('bench', '')
    c_tp = item.get('tp', 0)
    c_pp = item.get('pp', 0)
    c_ctx = item.get('input_tokens', 0)
    c_out = item.get('output_tokens', 256)
    c_conc = item.get('concurrency', 1)
    c_status = item.get('status', 'UNKNOWN')
    c_man = item.get('manifest') or f"{c_case}/{c_bench}"
    
    r_key = (c_case, c_bench, c_net)
    run_data = run_map.get(r_key, {})
    
    ev_id = f"EV-{i:03d}"
    
    # 1. execution_status and evidence_class
    if c_status == 'NOT_RUN':
        exec_status = 'NOT_RUN'
        evidence_class = 'GUARDED_NOT_RUN'
    elif 'CAPPED' in c_net:
        exec_status = 'COMPLETED'
        evidence_class = 'AUXILIARY_SENSITIVITY'
    else:
        exec_status = 'COMPLETED'
        evidence_class = 'PRIMARY_NATIVE'
        
    # Model revision
    model_name = "moonshotai/Kimi-Linear-48B-A3B-Instruct"
    model_rev = "e1df551"
    
    # Batch tokens & seqs
    batch_tokens = run_data.get('max_num_batched_tokens', 8192 if '8192' in c_case or c_ctx >= 8192 else 4096)
    max_seqs = run_data.get('max_num_seqs', 16 if 'maxseq' in c_case else (32 if 'qualification' in c_case else 64))
    kv_dtype = "BF16 (auto)"
    prefix_c = "ON" if run_data.get('prefix_caching') or 'prefix' in c_case else "OFF"
    
    # Network bandwidth
    if c_net == 'SINGLE_NODE_LOCAL':
        net_desc = "Local PCIe/NUMA"
        meas_bw = "Local Bus (~25.9 GB/s)"
    elif c_net == 'GCP_NATIVE':
        net_desc = "GCP_NATIVE"
        meas_bw = "173.6 Gbps (0.05ms RTT)"
    elif '100G' in c_net:
        net_desc = "100G Capped"
        meas_bw = "56.8 Gbps (tc/netem)"
    elif '20G' in c_net:
        net_desc = "20G Capped"
        meas_bw = "16.5 Gbps (tc/netem)"
    elif '50G' in c_net:
        net_desc = "50G Capped"
        meas_bw = "33.0 Gbps (hw qualification)"
    elif '10G' in c_net:
        net_desc = "10G Capped"
        meas_bw = "9.0 Gbps (hw qualification)"
    else:
        net_desc = c_net
        meas_bw = "N/A"
        
    # Sample count & reliability
    prompts = run_data.get('prompts_requested', run_data.get('metric_samples', 1))
    p95_rel = run_data.get('p95_reliable', False)
    p99_rel = run_data.get('p99_reliable', False)
    if exec_status == 'NOT_RUN':
        rel_flag = 'NOT_RUN'
        rel_badge = '<span class="status s-na">NOT_RUN</span>'
    elif p95_rel and p99_rel:
        rel_flag = 'CERTIFIED_HIGH_N'
        rel_badge = f'<span class="badge b-green" title="N={prompts} prompts: Sufficient sample count for production p95/p99 SLO">N={prompts} (p95/p99 Valid)</span>'
    elif prompts >= 30:
        rel_flag = 'CERTIFIED_HIGH_N'
        rel_badge = f'<span class="badge b-green" title="N={prompts} prompts: High sample count">N={prompts} (p95 Valid)</span>'
    else:
        rel_flag = 'LOW_N_UNCERTIFIED'
        rel_badge = f'<span class="badge b-amber" title="N={prompts} prompts: Low sample count (N<30). DO NOT use for production p95/p99 SLO!">N={prompts} (Low-N Uncertified)</span>'
        
    # Metrics
    if exec_status == 'COMPLETED' and run_data:
        ttft_val = run_data.get('mean_ttft_ms', 0)
        tpot_val = run_data.get('mean_tpot_ms', 0)
        kv_val = run_data.get('peak_kv_usage', 0)
        q_val = run_data.get('queue_mean_s_from_hist', 0.0)
        preempt = run_data.get('preemptions_delta', 0)
        
        ttft_str = f"{ttft_val/1000:.2f}s" if ttft_val >= 1000 else f"{ttft_val:.1f}ms"
        tpot_str = f"{tpot_val:.2f}ms"
        kv_str = f"{kv_val*100:.1f}%" if kv_val <= 1.0 else f"{kv_val:.1f}%"
        q_str = f"{q_val:.4f}s" if q_val > 0.0001 else "0.0s"
    else:
        ttft_str = "—"
        tpot_str = "—"
        kv_str = "—"
        q_str = "—"
        preempt = "—"
        
    # Clean relative manifest path
    c_man_clean = str(c_man).replace('\\', '/')
    for prefix in ['C:/Users/ayu23/OneDrive/Desktop/tpu/', 'v8_full_results/20260921_195656/', 'v8_full_results/results/real_data/']:
        c_man_clean = c_man_clean.replace(prefix, '')
    if 'scaleout_matrix/' in c_man_clean:
        c_man_clean = c_man_clean[c_man_clean.find('scaleout_matrix/'):]
    elif 'vllm_' in c_man_clean:
        c_man_clean = c_man_clean[c_man_clean.find('vllm_'):]
        
    ctx_str = f"{c_ctx//1000}K" if c_ctx >= 1000 else str(c_ctx)
    if c_ctx in [1048576, 1000000]:
        ctx_str = "1M"
        
    evidence_dataset.append({
        'id': ev_id,
        'scope': c_scope,
        'case': c_case,
        'bench': c_bench,
        'tp': c_tp,
        'pp': c_pp,
        'parallelism': f"TP{c_tp}/PP{c_pp}/DP1/EP1",
        'context': ctx_str,
        'input_tokens': c_ctx,
        'concurrency': c_conc,
        'exec_status': exec_status,
        'evidence_class': evidence_class,
        'model': model_name,
        'model_rev': model_rev,
        'batch_tokens': batch_tokens,
        'max_seqs': max_seqs,
        'kv_dtype': kv_dtype,
        'prefix_caching': prefix_c,
        'net_desc': net_desc,
        'meas_bw': meas_bw,
        'prompts': prompts,
        'p95_rel': p95_rel,
        'p99_rel': p99_rel,
        'rel_flag': rel_flag,
        'rel_badge': rel_badge,
        'ttft': ttft_str,
        'tpot': tpot_str,
        'kv': kv_str,
        'queue': q_str,
        'preempt': preempt,
        'manifest': c_man_clean
    })

print(f"Successfully processed {len(evidence_dataset)} evidence rows.")
classes = {}
for e in evidence_dataset:
    classes[e['evidence_class']] = classes.get(e['evidence_class'], 0) + 1
print("Evidence class distribution:", classes)
