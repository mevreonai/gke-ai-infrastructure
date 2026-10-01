import os

def patch():
    path = "/home/ayu23/vllm_env/lib/python3.12/site-packages/vllm/model_executor/warmup/kernel_warmup.py"
    with open(path, "r") as f:
        content = f.read()

    target = """    group = world.cpu_group if world.world_size > 1 else None"""
    replacement = """    from vllm.distributed.parallel_state import get_pp_group, get_tp_group
    if get_pp_group().world_size > 1:
        tp_grp = get_tp_group()
        group = tp_grp.cpu_group if tp_grp.world_size > 1 else None
    else:
        group = world.cpu_group if world.world_size > 1 else None"""

    if target in content:
        content = content.replace(target, replacement)
        with open(path, "w") as f:
            f.write(content)
        print("Successfully patched kernel_warmup.py for PP autotuning")
    elif "get_pp_group().world_size > 1" in content:
        print("kernel_warmup.py already patched for PP autotuning")
    else:
        print("WARNING: target not found in kernel_warmup.py")

if __name__ == "__main__":
    patch()
