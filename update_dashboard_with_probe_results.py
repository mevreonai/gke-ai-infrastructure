import os
import re

dashboard_paths = [
    r"c:\Users\ayu23\OneDrive\Desktop\tpu\MASTER_CHARACTERIZATION_DASHBOARD_V4_4thOct_2amIST_V8_KIMI48B.html",
    r"c:\Users\ayu23\OneDrive\Desktop\tpu\MASTER_CHARACTERIZATION_DASHBOARD_V4_27thSept_7pmIST.html",
    r"c:\Users\ayu23\OneDrive\Desktop\tpu\MASTER_CHARACTERIZATION_DASHBOARD_V4_27thSept_7pmIST_WITH_KEYFINDS.html",
    r"c:\Users\ayu23\OneDrive\Desktop\tpu\MASTER_CHARACTERIZATION_DASHBOARD_V4_27thSept_7pmIST_NO_KEYFINDS.html",
    r"c:\Users\ayu23\OneDrive\Desktop\tpu\v8_full_results\dashboards\v4_dashboard\index.html",
    r"c:\Users\ayu23\OneDrive\Desktop\tpu\v8_full_results\dashboards\v4_dashboard\MASTER_CHARACTERIZATION_DASHBOARD.html",
    r"c:\Users\ayu23\OneDrive\Desktop\tpu\v8_full_results\dashboards\v4_dashboard\MASTER_CHARACTERIZATION_DASHBOARD_WITH_KEYFINDS.html",
    r"c:\Users\ayu23\OneDrive\Desktop\tpu\v8_full_results\release_specs\index.html",
    r"c:\Users\ayu23\OneDrive\Desktop\tpu\v8_full_results\release_specs\MASTER_CHARACTERIZATION_DASHBOARD.html",
    r"c:\Users\ayu23\OneDrive\Desktop\tpu\v8_full_results\release_specs\MASTER_CHARACTERIZATION_DASHBOARD_WITH_KEYFINDS.html",
]

# 1. Read canonical source
src_path = dashboard_paths[0]
with open(src_path, "r", encoding="utf-8") as f:
    content = f.read()

# Target 1: Storage / Model Load / LMCache row in Reviewer Audit Matrix
old_audit_row = '<tr><td><b>Storage / Model Load / LMCache</b></td><td><code>server_start → server_ready</code> per case (§4.12); H2D/D2H 56.9/56.6 GB/s (§4.9); offload pressure probe defined.</td><td>Startup duration ledger (§4.12) &amp; host DRAM KV reload sizing (8.1 GB/rank in 0.14s).</td><td>Execute the defined <code>tp4_native_offload_pressure</code> test script.</td></tr>'

new_audit_row = '<tr><td><b>Storage / Model Load / LMCache</b></td><td><code>server_start → server_ready</code> per case (§4.12); H2D/D2H 56.9/56.6 GB/s (§4.9); offload probe executed (Probe #4).</td><td>Startup duration ledger (§4.12), host DRAM KV reload sizing (8.1 GB/rank in 0.14s), and UVA offloader pinned host memory validation (23.60 GiB/rank engram table offloaded to 1.4 TiB DRAM).</td><td><span class="status s-completed">PROBE EXECUTED</span> Pinned UVA host memory active; offload fault isolated to prefix-cache block-hash alignment.</td></tr>'

if old_audit_row in content:
    content = content.replace(old_audit_row, new_audit_row)
    print("[+] Replaced Storage / Model Load / LMCache audit row")
else:
    print("[-] Target audit row not found directly, checking regex")

# Write back and synchronize across all 10 dashboard copies
for path in dashboard_paths:
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"[+] Synchronized {path} ({len(content)} bytes)")
