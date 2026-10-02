import json
from exec_node import run_on_node

prep_script = """
import json
from pathlib import Path

spec = {
  "topology": "tp8_pp1",
  "tp": 8,
  "pp": 1,
  "mode": "decode_8k",
  "input": 8192,
  "output": 128,
  "concurrency": 1,
  "prompts": 1,
  "instrument": "nsys"
}

p = Path("/tmp/test_tp8_nsys_spec.json")
p.write_text(json.dumps(spec, indent=2))
print("Wrote spec successfully to", p)
"""

print("Writing spec on kimi-node-0...")
rc, out, err = run_on_node("kimi-node-0", prep_script, as_python=True)
print(out)
if rc != 0:
    print("Err:", err)
    exit(1)

run_cmd = """#!/usr/bin/env bash
set -e
pkill -9 -f vllm || true
sleep 2
rm -rf /tmp/tp8_nsys_out
mkdir -p /tmp/tp8_nsys_out

echo "Executing profile_case.py for nsys decode_8k..."
/home/ayu23/vllm_env/bin/python3 /home/ayu23/V9_FULL/v9_core/profile_case.py \
  --model-profile /home/ayu23/v9_full_results/v9_full_production_20260930_143117/logs/MODEL_PROFILE.json \
  --cluster /home/ayu23/v9_full_results/v9_full_production_20260930_143117/logs/CLUSTER_CONFIG.json \
  --spec-json /tmp/test_tp8_nsys_spec.json \
  --out /tmp/tp8_nsys_out \
  --port 8402 \
  --instrument nsys
"""

print("Running profile_case.py for nsys...")
rc, out, err = run_on_node("kimi-node-0", run_cmd)
print(f"rc={rc}")
print("STDOUT:")
print(out)
if err:
    print("STDERR:")
    print(err)
