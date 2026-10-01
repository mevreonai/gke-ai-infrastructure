import os
import sys

def patch_router():
    path = '/home/ayu23/vllm_env/lib64/python3.12/site-packages/vllm/model_executor/layers/fused_moe/router/fused_topk_bias_router.py'
    if not os.path.exists(path):
        print(f"File not found: {path}")
        return False
    with open(path, 'r', encoding='utf-8') as f:
        c = f.read()

    target1 = """    if bias_vl is not None:
        # Image tokens carry five consecutive in-vocab sentinel ids starting
        # at image_sentinel_lo and select experts with bias_vl instead of the
        # regular routing path. image_sentinel_lo == 0 disables this.
        assert input_tokens is not None, "bias_vl routing requires input_tokens" """

    # Let's handle whitespace variations defensively:
    target1_pattern = 'assert input_tokens is not None, "bias_vl routing requires input_tokens"'
    replacement1 = """if input_tokens is None:
            bias_vl = None"""

    if target1_pattern in c:
        c = c.replace(target1_pattern, replacement1)
        print("fused_topk_bias patched (input_tokens None -> bias_vl=None)")
    else:
        print("target1_pattern not found, checking if already patched")

    target2 = "bias_vl=self.bias_vl.data if self.bias_vl is not None else None,"
    replacement2 = "bias_vl=self.bias_vl.data if (self.bias_vl is not None and input_ids is not None) else None,"

    if target2 in c:
        c = c.replace(target2, replacement2)
        print("_compute_routing patched")
    else:
        print("target2 not found or already patched")

    with open(path, 'w', encoding='utf-8') as f:
        f.write(c)

    return True

if __name__ == '__main__':
    if patch_router():
        print("Router patch complete.")
    else:
        sys.exit(1)
