#!/usr/bin/env bash
set -e
source /home/ayu23/vllm_env/bin/activate
export PATH=/home/ayu23/vllm_env/bin:/usr/local/cuda/bin:/usr/local/bin:/usr/bin:$PATH
cd /home/ayu23/V9_FULL

RUN_ROOT=/home/ayu23/v9_full_results/v9_full_production_20260930_143117
MODEL_PROFILE=$RUN_ROOT/logs/MODEL_PROFILE.json
MATRIX=$RUN_ROOT/logs/V9_MATRIX.json
CLUSTER=$RUN_ROOT/logs/CLUSTER_CONFIG.json
SUITE=$RUN_ROOT/logs/SUITE_CONFIG.json
SINGLE=$RUN_ROOT/vllm_single_node_v9_matrix
OPEN_MATRIX=$RUN_ROOT/logs/V9_OPENLOOP_MATRIX.json
OPEN=$RUN_ROOT/vllm_open_loop
SCALEOUT=$RUN_ROOT/vllm_scaleout_network_matrix

echo "=== Starting V9 Clean Serving Resweep at $(date) ==="

echo "0. Regenerating Matrix with base_tp=8..."
cp /home/ayu23/V9_FULL/configs/suite_native_20g.json "$SUITE"
python3 v9_core/matrix.py --model "$MODEL_PROFILE" --suite "$SUITE" --cluster "$CLUSTER" --out "$MATRIX"

echo "Clearing previous failed serving dirs..."
rm -rf "$SINGLE" "$OPEN" "$SCALEOUT"
mkdir -p "$SINGLE" "$OPEN" "$SCALEOUT"

echo "1. Running Single Node Matrix..."
python3 v9_core/run_single.py --model-profile "$MODEL_PROFILE" --matrix "$MATRIX" --out "$SINGLE" --all --port 8000 > "$RUN_ROOT/logs/vllm_single_resweep.stdout.log" 2> "$RUN_ROOT/logs/vllm_single_resweep.stderr.log"

echo "2. Generating Open-Loop Matrix..."
python3 v9_core/generate_openloop.py --single-results "$SINGLE" --model-profile "$MODEL_PROFILE" --suite "$SUITE" --out "$OPEN_MATRIX" > "$RUN_ROOT/logs/openloop_gen.log" 2>&1

echo "3. Running Open-Loop Matrix..."
python3 v9_core/run_single.py --model-profile "$MODEL_PROFILE" --matrix "$OPEN_MATRIX" --out "$OPEN" --all --port 8002 --seed-base 12000 > "$RUN_ROOT/logs/vllm_openloop.stdout.log" 2> "$RUN_ROOT/logs/vllm_openloop.stderr.log"

echo "4. Running Scale-Out Matrix..."
python3 v9_core/run_scaleout_matrix.py --model-profile "$MODEL_PROFILE" --matrix "$MATRIX" --cluster "$CLUSTER" --out "$SCALEOUT" > "$RUN_ROOT/logs/vllm_scaleout_resweep.stdout.log" 2> "$RUN_ROOT/logs/vllm_scaleout_resweep.stderr.log"

echo "5. Running Runtime Diagnostics..."
python3 tools/process_all_runtime.py --root "$RUN_ROOT"

echo "6. Running Profile Analysis..."
python3 tools/analyze_all_profiles.py --root "$RUN_ROOT"

echo "7. Running Final Collection & Validation..."
python3 90_collect_and_validate_v9.py --root "$RUN_ROOT" --matrix "$MATRIX" --openloop-matrix "$OPEN_MATRIX"

echo "8. Packaging Evidence..."
./99_package_v9_full_results.sh "$RUN_ROOT"

echo "9. Strict Gate Sign-Off..."
python3 90_collect_and_validate_v9.py --root "$RUN_ROOT" --matrix "$MATRIX" --openloop-matrix "$OPEN_MATRIX" --strict-exit
echo "=== V9 RESWEEP FINISHED WITH RC=$? AT $(date) ==="
