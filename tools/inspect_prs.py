import re

with open('v8_full_results/dashboards/v4_dashboard/MASTER_CHARACTERIZATION_DASHBOARD.html', 'r', encoding='utf-8') as f:
    h = f.read()

pos = h.find('window.PROFILER_REGISTRY =')
end_pos = h.find('window.DISCOVERY_MAP =', pos)
registry_str = h[pos:end_pos]

keys = re.findall(r"'(PR-\d{3})':", registry_str)
print("Keys in PROFILER_REGISTRY:", sorted(list(set(keys))))

for k in sorted(list(set(keys))):
    k_pos = registry_str.find(f"'{k}':")
    k_end = registry_str.find("},", k_pos)
    print(f"\n=== {k} ===")
    print(registry_str[k_pos:k_end+2])
