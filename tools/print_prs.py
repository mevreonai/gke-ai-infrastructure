import sys, re

sys.stdout.reconfigure(encoding='utf-8')
with open('v8_full_results/dashboards/v4_dashboard/MASTER_CHARACTERIZATION_DASHBOARD.html', 'r', encoding='utf-8') as f:
    h = f.read()

pos = h.find('window.PROFILER_REGISTRY =')
end_pos = h.find('window.DISCOVERY_MAP =', pos)
reg = h[pos:end_pos]

for k in ['PR-004', 'PR-005', 'PR-006', 'PR-007']:
    target = f"'{k}':"
    kp = reg.find(target)
    ke = reg.find('},\n', kp)
    if ke == -1: ke = reg.find('}\n', kp)
    print(f"=== {k} ===")
    print(reg[kp:ke+2])
