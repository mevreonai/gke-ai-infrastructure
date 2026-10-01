import sys

file_path = '/home/ayu23/vllm_env/lib64/python3.12/site-packages/flashinfer/data/csrc/sparse_mla_sm120_prefill.cu'
with open(file_path, 'r') as f:
    content = f.read()

# 1. Update check in fulltile path
target1 = '(extra_page_block_size == 64 || extra_page_block_size == 128 || extra_page_block_size == 2)'
replacement1 = '(extra_page_block_size == 64 || extra_page_block_size == 128 || extra_page_block_size == 32 || extra_page_block_size == 2)'

if target1 in content:
    content = content.replace(target1, replacement1)
    print("Patched target1")
elif replacement1 in content:
    print("target1 already patched")
else:
    print("Warning: target1 not found")

# 2. Update dispatch in fulltile path
target2 = """    if (extra_page_block_size == 64) {
      DISPATCH_FULLTILE_BY_NH_PBSX(64);
    } else if (extra_page_block_size == 128) {
      DISPATCH_FULLTILE_BY_NH_PBSX(128);
    } else {
      DISPATCH_FULLTILE_BY_NH_PBSX(2);
    }"""

replacement2 = """    if (extra_page_block_size == 64) {
      DISPATCH_FULLTILE_BY_NH_PBSX(64);
    } else if (extra_page_block_size == 128) {
      DISPATCH_FULLTILE_BY_NH_PBSX(128);
    } else if (extra_page_block_size == 32) {
      DISPATCH_FULLTILE_BY_NH_PBSX(32);
    } else {
      DISPATCH_FULLTILE_BY_NH_PBSX(2);
    }"""

if target2 in content:
    content = content.replace(target2, replacement2)
    print("Patched target2")
elif replacement2 in content:
    print("target2 already patched")
else:
    print("Warning: target2 not found")

# 3. Update dispatch in general path
target3 = """  if (topk != 128) return false;
  if (extra_page_block_size == 64) {
    DISPATCH_BY_NH_PBSX(64);
  } else if (extra_page_block_size == 128) {
    DISPATCH_BY_NH_PBSX(128);
  } else if (extra_page_block_size == 2) {
    DISPATCH_BY_NH_PBSX(2);
  }
  return false;"""

replacement3 = """  if (topk != 128) return false;
  if (extra_page_block_size == 64) {
    DISPATCH_BY_NH_PBSX(64);
  } else if (extra_page_block_size == 128) {
    DISPATCH_BY_NH_PBSX(128);
  } else if (extra_page_block_size == 32) {
    DISPATCH_BY_NH_PBSX(32);
  } else if (extra_page_block_size == 2) {
    DISPATCH_BY_NH_PBSX(2);
  }
  return false;"""

if target3 in content:
    content = content.replace(target3, replacement3)
    print("Patched target3")
elif replacement3 in content:
    print("target3 already patched")
else:
    print("Warning: target3 not found")

with open(file_path, 'w') as f:
    f.write(content)

print("Successfully wrote updated sparse_mla_sm120_prefill.cu!")
