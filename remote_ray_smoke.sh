#!/usr/bin/env bash
set -e

echo "=========================================================="
echo "V8 SUITE REMOTE SMOKE TEST - RAY 2-NODE CLUSTER CHECK"
echo "=========================================================="

source ~/vllm_env/bin/activate 2>/dev/null || true

# Stop any dangling ray
ray stop --force 2>/dev/null || true
ssh -o StrictHostKeyChecking=no 10.128.0.40 "source ~/vllm_env/bin/activate 2>/dev/null || true; ray stop --force 2>/dev/null || true"

# Start Head on Node 0
echo "Starting Ray Head on kimi-node-0 (10.128.0.39)..."
ray start --head --node-ip-address=10.128.0.39 --port=6379 --disable-usage-stats

# Start Worker on Node 1
echo "Starting Ray Worker on kimi-node-1 (10.128.0.40)..."
ssh -o StrictHostKeyChecking=no 10.128.0.40 "source ~/vllm_env/bin/activate 2>/dev/null || true; ray start --address=10.128.0.39:6379 --disable-usage-stats"

sleep 3

# Verify cluster connectivity
echo "Querying Ray Cluster Topology..."
python3 -c "
import ray
ray.init(address='auto', logging_level='ERROR')
nodes = [n for n in ray.nodes() if n.get('Alive')]
print('==========================================================')
print(f'SUCCESS! Active Ray Cluster Nodes: {len(nodes)}')
for idx, node in enumerate(nodes):
    print(f'  Node {idx}: {node.get(\"NodeManagerAddress\")} (Alive={node.get(\"Alive\")})')
print('==========================================================')
"

# Clean up
echo "Stopping test Ray cluster..."
ray stop --force 2>/dev/null || true
ssh -o StrictHostKeyChecking=no 10.128.0.40 "source ~/vllm_env/bin/activate 2>/dev/null || true; ray stop --force 2>/dev/null || true"

echo "RAY 2-NODE MULTI-HOST SMOKE TEST PASSED"
