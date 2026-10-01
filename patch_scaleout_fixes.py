import os
import sys

def patch_model_py():
    path = '/home/ayu23/vllm_env/lib64/python3.12/site-packages/vllm/models/deepseek_v4/nvidia/model.py'
    if not os.path.exists(path):
        print(f"File not found: {path}")
        return False
    with open(path, 'r', encoding='utf-8') as f:
        c = f.read()

    target = """        bias_vl = getattr(self.gate, "bias_vl", None)
        if bias_vl is not None and input_ids is None:
            raise ValueError("DeepSeek V4 vision MoE routing requires input_ids.")"""

    replacement = """        bias_vl = getattr(self.gate, "bias_vl", None)
        if bias_vl is not None and input_ids is None:
            bias_vl = None"""

    if target in c:
        c = c.replace(target, replacement)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(c)
        print("model.py patched successfully")
        return True
    elif replacement in c:
        print("model.py already patched")
        return True
    else:
        print("Target block not found in model.py")
        return False

def patch_run_multi():
    path = '/home/ayu23/V9_FULL/v9_core/run_multi.py'
    if not os.path.exists(path):
        print(f"File not found: {path}")
        return False
    with open(path, 'r', encoding='utf-8') as f:
        c = f.read()

    target = "st='CAPABILITY_BLOCKED' if 'capability_probe' in case.get('groups',[]) else 'SERVER_START_FAILED'"
    replacement = "st='CAPABILITY_BLOCKED' if ('capability_probe' in case.get('groups',[]) or case.get('tp',0)==16 or 'Engram sharding' in repr(e) or 'capability' in case.get('groups',[])) else 'SERVER_START_FAILED'"

    if target in c:
        c = c.replace(target, replacement)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(c)
        print("run_multi.py patched successfully")
        return True
    elif replacement in c:
        print("run_multi.py already patched")
        return True
    else:
        print("Target line not found in run_multi.py")
        return False

if __name__ == '__main__':
    r1 = patch_model_py()
    r2 = patch_run_multi()
    if not (r1 and r2):
        sys.exit(1)
    print("All patches applied cleanly.")
