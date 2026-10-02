import sys
import subprocess
import base64

patch_code = """
with open('/home/ayu23/vllm_env/lib64/python3.12/site-packages/vllm/v1/engine/async_llm.py', 'r') as f:
    c = f.read()

old_start = '''    async def start_profile(self, profile_prefix: str | None = None) -> None:
        coros = [self.engine_core.profile_async(True, profile_prefix)]
        if self.profiler is not None:
            coros.append(asyncio.to_thread(self.profiler.start))
        await asyncio.gather(*coros)

    async def stop_profile(self) -> None:
        coros = [self.engine_core.profile_async(False)]
        if self.profiler is not None:
            coros.append(asyncio.to_thread(self.profiler.stop))
        await asyncio.gather(*coros)'''

new_start = '''    async def start_profile(self, profile_prefix: str | None = None) -> None:
        coros = [self.engine_core.profile_async(True, profile_prefix)]
        if getattr(self, 'profiler', None) is not None:
            coros.append(asyncio.to_thread(self.profiler.start))
        await asyncio.gather(*coros)

    async def stop_profile(self) -> None:
        coros = [self.engine_core.profile_async(False)]
        if getattr(self, 'profiler', None) is not None:
            coros.append(asyncio.to_thread(self.profiler.stop))
        await asyncio.gather(*coros)'''

if old_start in c:
    with open('/home/ayu23/vllm_env/lib64/python3.12/site-packages/vllm/v1/engine/async_llm.py', 'w') as f:
        f.write(c.replace(old_start, new_start))
    print('SUCCESSFULLY PATCHED async_llm.py')
elif new_start in c:
    print('ALREADY PATCHED async_llm.py')
else:
    print('COULD NOT MATCH TARGET BLOCK')
"""

from exec_node import run_on_node

for node in ["kimi-node-0", "kimi-node-1"]:
    print(f"Patching {node}...")
    rc, out, err = run_on_node(node, patch_code, as_python=True)
    print(f"[{node}] rc={rc}")
    if out: print(f"[{node}] stdout: {out}")
    if err: print(f"[{node}] stderr: {err}")
