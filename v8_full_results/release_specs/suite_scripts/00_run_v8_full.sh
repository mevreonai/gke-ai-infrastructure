#!/usr/bin/env bash
# V8-FULL one-command characterization orchestrator.
# Core principles:
#   * Preserve the proven V6 single-node vLLM path and case definitions.
#   * For single-node/local native evidence, inherit NO NCCL_* overrides.
#   * For multi-node GCP, preserve the V6 Socket-network workaround if configured,
#     but explicitly clear NCCL_P2P_DISABLE/NCCL_SHM_DISABLE/NCCL_P2P_LEVEL.
#   * vLLM scale-out network matrix: native + 100G + 20G only.
#   * hardware/NCCL transport sensitivity remains native + 100/50/20/10G.
#   * retain full raw + processed + profiler evidence and fail loudly on missing coverage.
set -euo pipefail

SUITE_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
VLLM_DIR="$SUITE_ROOT/rtx_g4_smoke_v5"
HW_DIR="$SUITE_ROOT/rtx_g4_smoke_v8_hw"
: "${VENV_DIR:=$HOME/vllm_env}"
: "${SSH_KEY:=$HOME/.ssh/google_compute_engine}"
: "${NUMA0_GPUS:=0,1,2,3}"
: "${NUMA1_GPUS:=4,5,6,7}"
: "${RUN_NETWORK_CAPS:=1}"
: "${VLLM_NETWORK_MODES:=native 100g 20g}"
: "${RUN_HEAVY_PROFILE:=1}"
: "${RUN_CAPPED_PROFILE:=1}"
: "${RUN_HW_PREP:=1}"
: "${V8FULL_RUN_ID:=$(date +%Y%m%d_%H%M%S)}"
: "${V8FULL_ROOT:=$HOME/v8_full_results/$V8FULL_RUN_ID}"
: "${V8FULL_RESUME:=1}"
mkdir -p "$V8FULL_ROOT" "$V8FULL_ROOT/logs" "$V8FULL_ROOT/.done"
MASTER="$V8FULL_ROOT/logs/V8_FULL_MASTER.log"
exec > >(tee -a "$MASTER") 2>&1

echo "V8-FULL RUN_ID=$V8FULL_RUN_ID"
echo "SUITE_ROOT=$SUITE_ROOT"
echo "RESULT_ROOT=$V8FULL_ROOT"
echo "VLLM_NETWORK_MODES=$VLLM_NETWORK_MODES"

# Use existing V6-compatible node configuration if available; otherwise discover nodes.
if [[ -f "$PWD/RUN_CONFIG.env" ]]; then source "$PWD/RUN_CONFIG.env"
elif [[ -f "$HOME/rtx_g4_smoke/RUN_CONFIG.env" ]]; then source "$HOME/rtx_g4_smoke/RUN_CONFIG.env"
else
  (cd "$SUITE_ROOT" && "$VLLM_DIR/00_init_gcp_config.sh")
  source "$SUITE_ROOT/RUN_CONFIG.env"
fi
: "${NODE0_IP:?NODE0_IP missing}"; : "${NODE1_IP:?NODE1_IP missing}"
mkdir -p "$HOME/rtx_g4_smoke"
if [[ -f "$SUITE_ROOT/RUN_CONFIG.env" ]]; then cp "$SUITE_ROOT/RUN_CONFIG.env" "$HOME/rtx_g4_smoke/RUN_CONFIG.env"; fi
if [[ -f "$PWD/RUN_CONFIG.env" ]]; then cp "$PWD/RUN_CONFIG.env" "$HOME/rtx_g4_smoke/RUN_CONFIG.env"; fi
source "$HOME/rtx_g4_smoke/RUN_CONFIG.env"
# Preserve the exact runtime configuration and release-source manifest with the evidence.
cp "$HOME/rtx_g4_smoke/RUN_CONFIG.env" "$V8FULL_ROOT/RUN_CONFIG.env"
chmod 600 "$V8FULL_ROOT/RUN_CONFIG.env" || true
[[ -f "$SUITE_ROOT/SOURCE_SHA256SUMS.txt" ]] && cp "$SUITE_ROOT/SOURCE_SHA256SUMS.txt" "$V8FULL_ROOT/SUITE_SOURCE_SHA256SUMS.txt"
[[ -f "$SUITE_ROOT/V8_FULL_RELEASE.json" ]] && cp "$SUITE_ROOT/V8_FULL_RELEASE.json" "$V8FULL_ROOT/V8_FULL_RELEASE.json"
export V8FULL_RUN_ID V8FULL_ROOT RUN_NETWORK_CAPS RUN_HEAVY_PROFILE RUN_CAPPED_PROFILE VLLM_NETWORK_MODES NUMA0_GPUS NUMA1_GPUS
source "$VENV_DIR/bin/activate"

step(){
  local name="$1"; shift
  local marker="$V8FULL_ROOT/.done/$name"
  if [[ "$V8FULL_RESUME" == 1 && -f "$marker" ]]; then
    echo; echo "================ STEP: $name (RESUME SKIP) ================"
    return 0
  fi
  echo; echo "================ STEP: $name ================"
  local s rc e
  s=$(date +%s)
  set +e
  "$@"
  rc=$?
  set -e
  e=$(date +%s)
  printf '{"step":"%s","rc":%s,"start":%s,"end":%s}\n' "$name" "$rc" "$s" "$e" >> "$V8FULL_ROOT/step_status.jsonl"
  [[ "$rc" == 0 ]] && touch "$marker"
  return "$rc"
}

# Static QA before any GPU/cloud work.
step static_validate python3 "$SUITE_ROOT/21_static_validate_suite.py" --root "$SUITE_ROOT" --out "$V8FULL_ROOT/STATIC_VALIDATION.json"

SSH=(ssh -i "$SSH_KEY" -o BatchMode=yes -o ConnectTimeout=20 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null)
SCP=(scp -i "$SSH_KEY" -o BatchMode=yes -o ConnectTimeout=20 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null)

# Fail before expensive work if node1 or noninteractive privilege escalation is unavailable.
step ssh_node1_access "${SSH[@]}" "$NODE1_IP" true
if [[ "$RUN_HW_PREP" == 1 || "$RUN_NETWORK_CAPS" == 1 || "$RUN_CAPPED_PROFILE" == 1 ]]; then
  step sudo_noninteractive_check bash -lc "sudo -n true && ${SSH[*]} '$NODE1_IP' sudo -n true"
fi

# Sync exact bundle to node1.
REMOTE_SUITE="$HOME/v8_full_suite_$V8FULL_RUN_ID"
step sync_suite bash -lc "tar -C '$SUITE_ROOT' -czf - rtx_g4_smoke_v5 rtx_g4_smoke_v8_hw | ${SSH[*]} '$NODE1_IP' \"mkdir -p '$REMOTE_SUITE' && tar -xzf - -C '$REMOTE_SUITE'\""
"${SCP[@]}" "$HOME/rtx_g4_smoke/RUN_CONFIG.env" "$NODE1_IP:/tmp/V8FULL_RUN_CONFIG.env"
"${SSH[@]}" "$NODE1_IP" "mkdir -p '$HOME/rtx_g4_smoke'; cp /tmp/V8FULL_RUN_CONFIG.env '$HOME/rtx_g4_smoke/RUN_CONFIG.env'"

# Fail-fast capability checks.
step preflight_node0 python3 "$VLLM_DIR/07_preflight_v5.py" --out "$V8FULL_ROOT/preflight_node0" --require-ray --require-nsys
step preflight_node1 bash -lc "${SSH[*]} '$NODE1_IP' \"source '$VENV_DIR/bin/activate'; python3 '$REMOTE_SUITE/rtx_g4_smoke_v5/07_preflight_v5.py' --out /tmp/v8full_preflight --require-ray --require-nsys\""
"${SCP[@]}" -r "$NODE1_IP:/tmp/v8full_preflight" "$V8FULL_ROOT/preflight_node1" || true
step validate_model python3 "$VLLM_DIR/08_validate_kimi_linear.py" --out "$V8FULL_ROOT/model_validation.json"

# V8-specific readiness: exact known-good V6 core stack by default plus the extra
# distributed/profiler capabilities required by V8.  Run it on BOTH nodes before
# hardware preparation or long vLLM work.
: "${V8_REQUIRE_V6_CORE_STACK:=1}"
: "${V8_EXPECTED_GPUS_PER_NODE:=8}"
: "${V8_MIN_FREE_GIB:=100}"
export V8_REQUIRE_V6_CORE_STACK V8_EXPECTED_GPUS_PER_NODE V8_MIN_FREE_GIB
step readiness_node0 python3 "$VLLM_DIR/22_v8_readiness.py" --out "$V8FULL_ROOT/readiness_node0"
step readiness_node1 "${SSH[@]}" "$NODE1_IP" "source '$HOME/rtx_g4_smoke/RUN_CONFIG.env' 2>/dev/null || true; unset NCCL_P2P_DISABLE NCCL_SHM_DISABLE NCCL_P2P_LEVEL; source '$VENV_DIR/bin/activate'; V8_REQUIRE_V6_CORE_STACK='$V8_REQUIRE_V6_CORE_STACK' V8_EXPECTED_GPUS_PER_NODE='$V8_EXPECTED_GPUS_PER_NODE' V8_MIN_FREE_GIB='$V8_MIN_FREE_GIB' python3 '$REMOTE_SUITE/rtx_g4_smoke_v5/22_v8_readiness.py' --out /tmp/v8full_readiness"
"${SCP[@]}" -r "$NODE1_IP:/tmp/v8full_readiness" "$V8FULL_ROOT/readiness_node1"

# Hardware tool preparation.
if [[ "$RUN_HW_PREP" == 1 ]]; then
  step hw_prepare_node0 env PEER_IP="$NODE1_IP" BENCH_ROOT="$HOME/rtx_g4_smoke" RESULT_DIR="$V8FULL_ROOT/hardware_prepare/node0" "$HW_DIR/01_prepare_node.sh"
  step hw_prepare_node1 bash -lc "${SSH[*]} '$NODE1_IP' \"export PEER_IP='$NODE0_IP' BENCH_ROOT='$HOME/rtx_g4_smoke' RESULT_DIR='/tmp/v8full_hw_prepare'; '$REMOTE_SUITE/rtx_g4_smoke_v8_hw/01_prepare_node.sh'\""
  "${SCP[@]}" -r "$NODE1_IP:/tmp/v8full_hw_prepare" "$V8FULL_ROOT/hardware_prepare/node1" || true
fi

# Hardware/fabric characterization. Local primary NCCL rows explicitly clear all NCCL_* overrides.
mkdir -p "$V8FULL_ROOT/hardware_raw"
step hw_node0 env PEER_IP="$NODE1_IP" NUMA0_GPUS="$NUMA0_GPUS" NUMA1_GPUS="$NUMA1_GPUS" BENCH_ROOT="$HOME/rtx_g4_smoke" RESULT_DIR="$V8FULL_ROOT/hardware_raw/node0" RUN_ID="$V8FULL_RUN_ID" "$HW_DIR/02_run_node_local.sh"
step hw_node1 bash -lc "${SSH[*]} '$NODE1_IP' \"export PEER_IP='$NODE0_IP' NUMA0_GPUS='$NUMA0_GPUS' NUMA1_GPUS='$NUMA1_GPUS' BENCH_ROOT='$HOME/rtx_g4_smoke' RESULT_DIR='/tmp/v8full_hw_node1' RUN_ID='$V8FULL_RUN_ID'; '$REMOTE_SUITE/rtx_g4_smoke_v8_hw/02_run_node_local.sh'\""
"${SCP[@]}" -r "$NODE1_IP:/tmp/v8full_hw_node1" "$V8FULL_ROOT/hardware_raw/node1"
step hw_network env NODE0_IP="$NODE0_IP" NODE1_IP="$NODE1_IP" SSH_KEY="$SSH_KEY" BENCH_ROOT="$HOME/rtx_g4_smoke" RESULT_DIR="$V8FULL_ROOT/hardware_raw/network_node0" RUN_ID="$V8FULL_RUN_ID" RUN_NETWORK_CAPS="$RUN_NETWORK_CAPS" "$HW_DIR/03_run_network_sweep.sh"
step hw_summarize python3 "$HW_DIR/04_summarize_results.py" "$V8FULL_ROOT/hardware_raw" --out "$V8FULL_ROOT/hardware_processed"
step hw_validate python3 "$HW_DIR/07_validate_results.py" "$V8FULL_ROOT/hardware_raw" --out "$V8FULL_ROOT/hardware_processed/validation_hw.json"

# V6-stable single-node matrix. Wrapper strips ALL NCCL_* variables to reproduce the actual V6 qualification environment.
SINGLE="$V8FULL_ROOT/vllm_single_node_v6_matrix"
step vllm_single_v6 env NCCL_POLICY_LOG="$SINGLE/NCCL_ENV_BEFORE_RUN.txt" "$VLLM_DIR/20_run_single_node_v6_aligned.sh" python3 "$VLLM_DIR/11_run_vllm_surrogate.py" --cases "$VLLM_DIR/10_vllm_surrogate_cases.json" --out "$SINGLE" --all
step vllm_single_v6_summary python3 "$VLLM_DIR/15_summarize_vllm.py" "$SINGLE" --out "$SINGLE/summary_v8full"

# V8 1M single-node extensions, under the same clean local NCCL policy.
EXT="$V8FULL_ROOT/vllm_single_node_v8_1m_extensions"
step vllm_1m_extensions env NCCL_POLICY_LOG="$EXT/NCCL_ENV_BEFORE_RUN.txt" "$VLLM_DIR/20_run_single_node_v6_aligned.sh" python3 "$VLLM_DIR/11_run_vllm_surrogate.py" --cases "$VLLM_DIR/10d_v8_1m_extended_cases.json" --out "$EXT" --all --port 8001 --seed-base 9000
step vllm_1m_extensions_summary python3 "$VLLM_DIR/15_summarize_vllm.py" "$EXT" --out "$EXT/summary_v8full"

# Evidence-derived open-loop single-node sweep.
LOAD_CASES="$V8FULL_ROOT/10c_v8_generated_load_cases.json"
step generate_openloop python3 "$VLLM_DIR/13_generate_load_cases.py" --summary-json "$SINGLE/summary_v8full/vllm_runs.json" --base-cases "$VLLM_DIR/10_vllm_surrogate_cases.json" --out "$LOAD_CASES" --contexts 8192,131072 --include-probe
OPEN="$V8FULL_ROOT/vllm_open_loop"
step vllm_openloop env NCCL_POLICY_LOG="$OPEN/NCCL_ENV_BEFORE_RUN.txt" "$VLLM_DIR/20_run_single_node_v6_aligned.sh" python3 "$VLLM_DIR/11_run_vllm_surrogate.py" --cases "$LOAD_CASES" --out "$OPEN" --all --port 8002 --seed-base 12000
step vllm_openloop_summary python3 "$VLLM_DIR/15_summarize_vllm.py" "$OPEN" --out "$OPEN/summary_v8full"

# Scale-out model matrix: exactly native / 100G / 20G for all four topologies and 128K/512K/1M (1M safety-gated).
MULTI="$V8FULL_ROOT/vllm_scaleout_network_matrix"
step vllm_scaleout_network_matrix env OUT_ROOT="$MULTI" CASES_FILE="$VLLM_DIR/10b_vllm_multi_node_cases.json" VLLM_NETWORK_MODES="$VLLM_NETWORK_MODES" "$VLLM_DIR/20_run_vllm_network_matrix.sh"

# Single-node profiling, again with no NCCL_* overrides.
PROF1="$V8FULL_ROOT/profiles_single_node"; mkdir -p "$PROF1"
for TPV in 4 8; do
  for MODE in prefill decode batched_decode; do
    step "profile_single_tp${TPV}_${MODE}" env NCCL_POLICY_LOG="$PROF1/tp${TPV}_${MODE}/NCCL_ENV_BEFORE_RUN.txt" "$VLLM_DIR/20_run_single_node_v6_aligned.sh" env TP="$TPV" PROFILE_MODE="$MODE" PROFILE_ROOT="$PROF1/tp${TPV}_${MODE}" PORT=$((8100+TPV)) "$VLLM_DIR/14_run_vllm_nsys_profile.sh"
  done
done
step profile_single_analyze python3 "$VLLM_DIR/16_analyze_vllm_profiles.py" --profile-dir "$PROF1" --out "$PROF1/PROFILE_ANALYSIS.json"

# Dedicated single-node PyTorch profiler captures.
TORCHP="$V8FULL_ROOT/profiles_torch_single_node"; mkdir -p "$TORCHP"
for TPV in 4 8; do
  step "profile_torch_tp${TPV}" env NCCL_POLICY_LOG="$TORCHP/tp${TPV}_8k_decode/NCCL_ENV_BEFORE_RUN.txt" "$VLLM_DIR/20_run_single_node_v6_aligned.sh" env TP="$TPV" INPUT_LEN=8192 OUTPUT_LEN=128 CONCURRENCY=1 PORT=$((8200+TPV)) PROFILE_ROOT="$TORCHP/tp${TPV}_8k_decode" "$VLLM_DIR/14b_run_vllm_torch_profile.sh"
done

# Full distributed profile matrix on uncapped GCP native network.
PROFM="$V8FULL_ROOT/profiles_multi_node_native"
step profile_multi_node_native env OUT_ROOT="$PROFM" RUN_HEAVY_PROFILE="$RUN_HEAVY_PROFILE" V8_GCP_NETWORK_PROVENANCE_OVERRIDE=GCP_NATIVE GCP_NETWORK_PROVENANCE=GCP_NATIVE V8_VLLM_NETWORK_MODE=native V8_VLLM_NETWORK_CAP_GBPS=0 "$VLLM_DIR/18_run_vllm_multi_node_profiles.sh"

# Targeted capped-network profiles: 128K prefill for all four topologies at 100G and 20G.
if [[ "$RUN_CAPPED_PROFILE" == 1 ]]; then
  PROFC="$V8FULL_ROOT/profiles_multi_node_capped"
  step profile_multi_node_capped env OUT_ROOT="$PROFC" "$VLLM_DIR/21_run_vllm_capped_profiles.sh"
fi

# Unified processing / coverage / provenance validation.
step final_collect python3 "$SUITE_ROOT/90_collect_and_validate.py" --root "$V8FULL_ROOT" --suite "$SUITE_ROOT"
step package_results "$SUITE_ROOT/99_package_v8_full_results.sh" "$V8FULL_ROOT"
# Strict sign-off runs after packaging so partial evidence is preserved if a safety gate blocks a 1M case.
step final_strict_signoff python3 "$SUITE_ROOT/90_collect_and_validate.py" --root "$V8FULL_ROOT" --suite "$SUITE_ROOT" --strict-exit

echo "V8-FULL COMPLETE: $V8FULL_ROOT"
