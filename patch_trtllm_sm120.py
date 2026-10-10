import re

# 1. Patch trtllm_ragged.py
target1 = '/home/ayu23/vllm_env/lib64/python3.12/site-packages/vllm/v1/attention/backends/mla/prefill/trtllm_ragged.py'
content1 = open(target1).read()
old1 = 'return device_capability.major == 10'
new1 = 'return device_capability.major in (10, 12)'
if old1 in content1:
    open(target1 + '.bak', 'w').write(content1)
    open(target1, 'w').write(content1.replace(old1, new1))
    print('Patched trtllm_ragged.py')
else:
    print('trtllm_ragged.py already patched or pattern not found')

# 2. Patch selector.py
target2 = '/home/ayu23/vllm_env/lib64/python3.12/site-packages/vllm/v1/attention/backends/mla/prefill/selector.py'
content2 = open(target2).read()
old2 = 'if device_capability.major == 10:  # Blackwell'
new2 = 'if device_capability.major in (10, 12):  # Blackwell'
if old2 in content2:
    open(target2 + '.bak', 'w').write(content2)
    open(target2, 'w').write(content2.replace(old2, new2))
    print('Patched selector.py')
else:
    print('selector.py already patched or pattern not found')
