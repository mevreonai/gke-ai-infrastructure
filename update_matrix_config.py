import json, re

# 1. Update configs/suite_native_20g.json and configs/suite_default.json
for cfg_path in ['/home/ayu23/V9_FULL/configs/suite_native_20g.json', '/home/ayu23/V9_FULL/configs/suite_default.json']:
    try:
        with open(cfg_path, 'r') as f:
            cfg = json.load(f)
        cfg['base_tp'] = 8
        with open(cfg_path, 'w') as f:
            json.dump(cfg, f, indent=2)
        print(f"Updated base_tp to 8 in {cfg_path}")
    except Exception as e:
        print(f"Error updating {cfg_path}: {e}")

# 2. Update v9_core/matrix.py
matrix_path = '/home/ayu23/V9_FULL/v9_core/matrix.py'
with open(matrix_path, 'r') as f:
    code = f.read()

target = "    for tp in tpvals:\n        single.append(case(f'tp{tp}_context_baseline',tp,['baseline','context_scaling','tp_compare'],f'TP{tp} context scaling baseline.',[make_bench(f'{ctx}_c1',ctx,1) for ctx in contexts]))"
replacement = """    for tp in tpvals:
        tp_contexts = [ctx for ctx in contexts if ctx <= 131072] if tp < 8 else contexts
        extra_args = {'max_model_len': 131072} if tp < 8 else {}
        single.append(case(f'tp{tp}_context_baseline',tp,['baseline','context_scaling','tp_compare'],f'TP{tp} context scaling baseline.',[make_bench(f'{ctx}_c1',ctx,1) for ctx in tp_contexts],**extra_args))"""

if target in code:
    code = code.replace(target, replacement)
    with open(matrix_path, 'w') as f:
        f.write(code)
    print("Successfully patched v9_core/matrix.py for TP4 context scaling")
else:
    print("Target block not found in v9_core/matrix.py, checking if already modified")
