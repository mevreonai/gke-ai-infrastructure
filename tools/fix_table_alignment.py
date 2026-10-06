import sys, re, json, os

sys.stdout.reconfigure(encoding="utf-8")
dash_path = r"v8_full_results\dashboards\v4_dashboard\MASTER_CHARACTERIZATION_DASHBOARD.html"
index_path = r"v8_full_results\dashboards\v4_dashboard\index.html"

with open(dash_path, "r", encoding="utf-8") as f:
    h = f.read()

# 1. Update openEvidenceForFinding ID map (Fix P1)
old_func_map = """window.openEvidenceForFinding = function(pageId) {
    const findingToEv = {
        1: 'EV-030', // TP16/PP1 20G TTFT 256.889s
        2: 'EV-034', // Concurrency 1M c4 TTFT 231.268s
        3: 'PR-007', // TP4/PP4 512K distributed profile FlashAttention shift
        4: 'EV-038', // Prefix cache hit speedup 36.0x
        5: 'EV-040', // 16K chunk admission 3.3586 req/s
        6: 'EV-044', // TP8/PP2 664.24 GPU-s measured point
        7: 'PR-003', // 8K TP8 Decode PyTorch AllReduce 583.87ms
        8: 'EV-048', // Chunk prefill TTFT reduction 38.868s vs 53.303s (-27.1%)
        9: 'EV-050', // True efficiency TP4/PP4 28.568s vs TP16/PP1 68.197s
        10: 'EV-054' // KV cache dilution 2.75% vs 88.83 GiB physical telemetry
    };"""

new_func_map = """window.openEvidenceForFinding = function(pageId) {
    const findingToEv = {
        1: 'EV-111', // TP16/PP1 20G TTFT 256.889s
        2: 'EV-067', // Concurrency 1M c4 TTFT 231.268s
        3: 'PR-007', // TP4/PP4 512K distributed profile FlashAttention shift
        4: 'EV-075', // Prefix cache hit speedup
        5: 'EV-116', // Max num seqs throughput knee
        6: 'EV-081', // TP16/PP1 efficiency
        7: 'PR-003', // 8K TP8 Decode PyTorch AllReduce 583.87ms
        8: 'EV-027', // Chunk prefill TTFT reduction
        9: 'EV-084', // True efficiency TP4/PP4 vs TP16/PP1
        10: 'EV-084' // KV cache headroom
    };"""

if old_func_map in h:
    h = h.replace(old_func_map, new_func_map)
    print("Fixed P1: openEvidenceForFinding ID map updated.")
else:
    print("Notice: old_func_map not matched exactly.")

# 2. Fix the Table Header: Remove <th>Cold Load</th>
h = h.replace("<th>Cold Load</th>\n", "")
h = h.replace("<th>Cold Load</th>", "")
print("Removed <th>Cold Load</th> header.")

# 3. Align all evidence rows: ensure exactly 15 cells per row
# Load combined_vllm_runs to get actual warmups and prompts_requested
combined_runs = json.load(open(r"v8_full_results\results\real_data\final_validation\combined_vllm_runs.json", encoding="utf-8"))
run_dict = {}
for r in combined_runs:
    key = (r.get("case"), r.get("bench"))
    run_dict[key] = r

# Find all <tr class="ev-row" ...>
row_pattern = re.compile(r'(<tr class="ev-row"[^>]*data-ev-id="([^"]+)"[^>]*data-case="([^"]+)"[^>]*data-bench="([^"]+)"[^>]*>)(.*?)(</tr>)', re.DOTALL)

def fix_row(m):
    tr_open = m.group(1)
    ev_id = m.group(2)
    case = m.group(3)
    bench = m.group(4)
    body = m.group(5)
    tr_close = m.group(6)
    
    # Get tds
    td_matches = re.findall(r'<td[^>]*>.*?</td>', body, re.DOTALL)
    
    # Lookup warmups & prompts
    run_info = run_dict.get((case, bench), {})
    warmup = run_info.get("warmups", 0)
    prompts = run_info.get("prompts_requested", 1)
    if "c" in bench and not run_info:
        try:
            c_val = int(re.search(r'c(\d+)', bench).group(1))
            prompts = c_val
        except:
            prompts = 1
    
    warmup_td = f'<td class="mono" style="font-size:7px;color:var(--text)">w={warmup} &middot; {prompts} req</td>'
    
    # Check if warmup_td already present (like w=1 · 32 req)
    has_warmup = any('req</td>' in td for td in td_matches)
    
    if has_warmup:
        # replace the generic "w=1 · 32 req" with accurate warmup & prompts
        new_tds = []
        for td in td_matches:
            if 'req</td>' in td:
                new_tds.append(warmup_td)
            else:
                new_tds.append(td)
        td_matches = new_tds
    else:
        # Insert warmup_td at column index 8 (9th column, right after Runtime Knobs)
        if len(td_matches) >= 8:
            td_matches.insert(8, warmup_td)
    
    new_body = "\n" + "\n".join(td_matches) + "\n"
    return tr_open + new_body + tr_close

new_h, count = row_pattern.subn(fix_row, h)
print(f"Fixed {count} evidence rows to have matching 15 columns!")
h = new_h

with open(dash_path, "w", encoding="utf-8") as f:
    f.write(h)
with open(index_path, "w", encoding="utf-8") as f:
    f.write(h)
print(f"Updated {dash_path} and {index_path} ({len(h):,} bytes).")
