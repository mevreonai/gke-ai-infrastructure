import csv
import re
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Read 02_evidence_rows.csv
with open('rtx_g4_smoke_v5/03_dashboards/docs/audit/02_evidence_rows.csv', 'r', encoding='utf-8') as f:
    csv_rows = list(csv.DictReader(f))

# Read HTML and find evidence rows
with open('MASTER_CHARACTERIZATION_DASHBOARD.html', 'r', encoding='utf-8') as f:
    html_content = f.read()

# Pattern for evidence rows in HTML
row_matches = re.findall(r'<tr class="evidence-row"[^>]*>(.*?)</tr>', html_content, re.DOTALL)
print(f"Evidence rows in HTML: {len(row_matches)}")
print(f"Evidence rows in CSV: {len(csv_rows)}")

# Extract row details from HTML
html_rows = []
for idx, r in enumerate(row_matches):
    cols = re.findall(r'<td[^>]*>(.*?)</td>', r, re.DOTALL)
    clean_cols = [re.sub(r'<[^>]+>', '', c).strip() for c in cols]
    html_rows.append(clean_cols)

print("Sample HTML row 0:", html_rows[0] if html_rows else 'none')

# Check Fig 4: 8K TP4 throughput divergence
print("\n--- FIG 4 CHECK: 8K TP4 Throughput (tp4_closedloop_8k) ---")
for r in csv_rows:
    if r['case'] == 'tp4_closedloop_8k':
        print(f"  CSV: c{r['concurrency']} -> {r['output_tok_s']} tok/s")

# Let's see what the HTML JS has for canvasScaleUpThroughput or canvasExecTps
print("HTML JS canvasScaleUpThroughput arrays:")
for line in html_content.splitlines():
    if "TP4 Output tok/s" in line or "TP8 Output tok/s" in line:
        print("  ", line.strip())

# Check Fig 11: 128K KV utilization
print("\n--- FIG 11 CHECK: 128K KV Utilization (tp4_closedloop_128k) ---")
for r in csv_rows:
    if r['case'] == 'tp4_closedloop_128k':
        print(f"  CSV: c{r['concurrency']} -> {r['kv_peak_pct']}%")

print("HTML JS canvasSchedKvUtil arrays:")
for line in html_content.splitlines():
    if "128K Context KV %" in line or "8K Context KV %" in line:
        print("  ", line.strip())

# Diff all rows
mismatches = []
for i, (h, c) in enumerate(zip(html_rows, csv_rows)):
    case_h = h[0]
    bench_h = h[1]
    tp_pp_h = h[2]
    input_h = h[3].replace(',', '')
    conc_h = h[4]
    ttft_h = h[5].replace(' ms', '')
    tpot_h = h[6].replace(' ms', '')
    tps_h = h[7]
    kv_h = h[8].replace('%', '')
    status_h = h[9].replace('●', '').strip()

    case_c = c['case']
    bench_c = c['bench']
    input_c = c['input_tokens_displayed'].replace(',', '')
    conc_c = c['concurrency']
    ttft_c = f"{float(c['ttft_ms']):.1f}" if c['ttft_ms'] else ''
    tpot_c = f"{float(c['tpot_ms']):.2f}" if c['tpot_ms'] else ''
    tps_c = f"{float(c['output_tok_s']):.1f}" if c['output_tok_s'] else ''
    kv_c = f"{float(c['kv_peak_pct']):.1f}" if c['kv_peak_pct'] else ''

    diffs = []
    if case_h != case_c: diffs.append(f"case: '{case_h}' vs '{case_c}'")
    if bench_h != bench_c: diffs.append(f"bench: '{bench_h}' vs '{bench_c}'")
    if input_h != input_c: diffs.append(f"input: '{input_h}' vs '{input_c}'")
    if conc_h != f"c{conc_c}": diffs.append(f"conc: '{conc_h}' vs 'c{conc_c}'")
    if ttft_h != ttft_c: diffs.append(f"ttft: '{ttft_h}' vs '{ttft_c}'")
    if tpot_h != tpot_c: diffs.append(f"tpot: '{tpot_h}' vs '{tpot_c}'")
    if tps_h != tps_c: diffs.append(f"tps: '{tps_h}' vs '{tps_c}'")
    if kv_h != kv_c: diffs.append(f"kv: '{kv_h}' vs '{kv_c}'")

    if diffs:
        mismatches.append((i, case_c, bench_c, diffs))

print(f"\nTotal row-by-row mismatches between HTML Evidence table and 02_evidence_rows.csv: {len(mismatches)}")
for m in mismatches[:15]:
    print(f"  Row {m[0]} ({m[1]}::{m[2]}): {m[3]}")

# Check Scale-Out values in HTML (lines in HTML)
print("\n--- SCALE-OUT VALUES IN HTML ---")
for line in html_content.splitlines():
    if "TTFT (128K)" in line or "canvasScaleOutTtft" in line or "canvasScaleOutTps" in line or "1723.7" in line or "6024.9" in line:
        print("  ", line.strip())
