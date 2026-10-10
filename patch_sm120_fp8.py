import re
import sys

target = '/home/ayu23/vllm_env/lib64/python3.12/site-packages/vllm/model_executor/layers/attention/mla_attention.py'
content = open(target).read()
old_code = 'if not current_platform.is_device_capability_family(100):'
new_code = 'if not (current_platform.is_device_capability_family(100) or current_platform.is_device_capability_family(120)):'

if old_code in content:
    with open(target + '.bak', 'w') as f:
        f.write(content)
    with open(target, 'w') as f:
        f.write(content.replace(old_code, new_code))
    print('SUCCESS: Patched mla_attention.py for SM120')
else:
    print('Pattern not found or already patched')
