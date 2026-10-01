file_path = '/home/ayu23/vllm_env/lib64/python3.12/site-packages/flashinfer/data/csrc/sparse_mla_sm120_prefill.cu'
content = open(file_path).read()

target1 = 'topk_extra % BI == 0 && (extra_page_block_size == 64 || extra_page_block_size == 2)'
replacement1 = 'topk_extra % BI == 0 && (extra_page_block_size == 64 || extra_page_block_size == 128 || extra_page_block_size == 2)'

target2 = """    if (extra_page_block_size == 64) {
      DISPATCH_FULLTILE_BY_NH_PBSX(64);
    } else {
      DISPATCH_FULLTILE_BY_NH_PBSX(2);
    }"""
replacement2 = """    if (extra_page_block_size == 64) {
      DISPATCH_FULLTILE_BY_NH_PBSX(64);
    } else if (extra_page_block_size == 128) {
      DISPATCH_FULLTILE_BY_NH_PBSX(128);
    } else {
      DISPATCH_FULLTILE_BY_NH_PBSX(2);
    }"""

target3 = """  if (topk != 128) return false;
  if (extra_page_block_size == 64) {
    DISPATCH_BY_NH_PBSX(64);
  } else if (extra_page_block_size == 2) {
    DISPATCH_BY_NH_PBSX(2);
  }
  return false;"""
replacement3 = """  if (topk != 128) return false;
  if (extra_page_block_size == 64) {
    DISPATCH_BY_NH_PBSX(64);
  } else if (extra_page_block_size == 128) {
    DISPATCH_BY_NH_PBSX(128);
  } else if (extra_page_block_size == 2) {
    DISPATCH_BY_NH_PBSX(2);
  }
  return false;"""

if target1 not in content:
    print("Warning: target1 not found, checking if already patched...")
    if replacement1 in content:
        print("Already patched!")
    else:
        raise RuntimeError("target1 not found in content!")
else:
    content = content.replace(target1, replacement1).replace(target2, replacement2).replace(target3, replacement3)
    with open(file_path, 'w') as f:
        f.write(content)
    print("Successfully patched sparse_mla_sm120_prefill.cu with PBSX=128 support!")
