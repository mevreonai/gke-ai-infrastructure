with open('v9_runs/dashboard/MASTER_CHARACTERIZATION_DASHBOARD_V9.html', 'r', encoding='utf-8') as f:
    c = f.read()

import re

for val in ['251.529', '583.866', '41.515']:
    matches = [m.start() for m in re.finditer(re.escape(val), c)]
    print(f'{val}: {len(matches)} occurrences')
    for idx in matches[:2]:
        print('   snippet:', repr(c[max(0, idx-50):min(len(c), idx+100)]))

tabs = re.findall(r'data-tab="([^"]+)"', c)
print('data-tab occurrences:', tabs)
