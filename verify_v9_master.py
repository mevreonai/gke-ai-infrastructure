with open('v9_runs/dashboard/MASTER_CHARACTERIZATION_DASHBOARD_V9.html', 'r', encoding='utf-8') as f:
    c = f.read()

print('=== AUDIT REPORT FOR V9 MASTER DASHBOARD ===')
print('File size:', len(c))
print('Count of 112,640 (fake kernels):', c.count('112,640'))
print('Count of 251.529 (fake V8 self CUDA):', c.count('251.529'))
print('Count of 583.866 (fake V8 self CUDA):', c.count('583.866'))
print('Count of 28.568 (old V8 1M latency):', c.count('28.568'))
print('Count of 41.515 (old V8 TP8/PP2):', c.count('41.515'))
print('Count of Qwen:', c.count('Qwen'))
print('Count of Kimi-Linear-48B:', c.count('Kimi-Linear-48B'))
print('Count of PROFILER_REGISTRY = {}:', c.count('window.PROFILER_REGISTRY = {};'))
print('Count of NOT RUN IN TEST 2:', c.count('NOT RUN IN TEST 2'))
print('Count of Pending Test 3:', c.count('Pending Test 3'))
print('Count of CAPABILITY_BLOCKED:', c.count('CAPABILITY_BLOCKED'))
print('Count of EV-V9-:', c.count('EV-V9-'))
print('Shell open tag:', c.count('<div class="shell">'))
print('Shell close tag:', c.count('</div> <!-- /shell -->'))

# Check tabs
import re
tabs = re.findall(r'data-tab="([^"]+)"', c)
pages = re.findall(r'<section class="tabpage[^"]*" id="([^"]+)"', c)
print('Tabs in navigation:', tabs)
print('Tab pages in body:  ', pages)
assert tabs == pages, f"Tabs mismatch: {tabs} vs {pages}"
print('Tab-to-Page contract: PERFECT 1:1 MATCH!')
