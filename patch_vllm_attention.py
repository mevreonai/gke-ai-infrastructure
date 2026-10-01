import re, sys

files = [
    '/home/ayu23/vllm_env/lib64/python3.12/site-packages/vllm/models/deepseek_v4_1/nvidia/model.py',
    '/home/ayu23/vllm_env/lib64/python3.12/site-packages/vllm/models/deepseek_v4/nvidia/model.py'
]

for f in files:
    try:
        content = open(f).read()
        if 'return DeepseekV4FlashInferSM120Attention' in content:
            open(f + '.bak', 'w').write(content)
            new_content = content.replace('return DeepseekV4FlashInferSM120Attention', 'return DeepseekV4FlashInferMLAAttention')
            open(f, 'w').write(new_content)
            print(f'Successfully patched {f}')
        else:
            print(f'Already patched or pattern not found in {f}')
    except Exception as e:
        print(f'Error processing {f}: {e}')
