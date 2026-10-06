#!/usr/bin/env bash
# Stage 2: Failed Runs Rerun, Multi-Node Load & Capped Profiles (~3.5 hours)
# Format and execution conventions strictly match the V8 benchmark suite.
# Fully updated per Code Review v1.4.
set -euo pipefail

SUITE_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
VLLM_DIR="$SUITE_ROOT/rtx_g4_smoke_v5"
HW_DIR="$SUITE_ROOT/rtx_g4_smoke_v8_hw"

: "${VENV_DIR:=$HOME/vllm_env}"
: "${SSH_KEY:=$HOME/.ssh/google_compute_engine}"
: "${RUN_ID:=$(date +%Y%m%d_%H%M%S)}"
: "${STAGE2_ROOT:=$HOME/v8_additional_runs/$RUN_ID/stage2}"
: "${STAGE2_RESUME:=1}"

mkdir -p "$STAGE2_ROOT" "$STAGE2_ROOT/logs" "$STAGE2_ROOT/.done"
MASTER="$STAGE2_ROOT/logs/STAGE2_MASTER.log"
exec > >(tee -a "$MASTER") 2>&1

echo "================================================================="
echo "  V8 ADDITIONAL RUNS — STAGE 2: FAILED RERUNS & SCALE-OUT"
echo "  RUN_ID      : $RUN_ID"
echo "  STAGE2_ROOT : $STAGE2_ROOT"
echo "  SUITE_ROOT  : $SUITE_ROOT"
echo "================================================================="

# Discover GCP configuration if present
if [[ -f "$PWD/RUN_CONFIG.env" ]]; then source "$PWD/RUN_CONFIG.env"
elif [[ -f "$SUITE_ROOT/RUN_CONFIG.env" ]]; then source "$SUITE_ROOT/RUN_CONFIG.env"
elif [[ -f "$HOME/rtx_g4_smoke/RUN_CONFIG.env" ]]; then source "$HOME/rtx_g4_smoke/RUN_CONFIG.env"
fi

if [[ -f "$VENV_DIR/bin/activate" ]]; then
  source "$VENV_DIR/bin/activate"
fi

step(){
  local name="$1"; shift
  local marker="$STAGE2_ROOT/.done/$name"
  if [[ "$STAGE2_RESUME" == 1 && -f "$marker" ]]; then
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
  printf '{"step":"%s","rc":%s,"start":%s,"end":%s}\n' "$name" "$rc" "$s" "$e" >> "$STAGE2_ROOT/step_status.jsonl"
  [[ "$rc" == 0 ]] && touch "$marker"
  return "$rc"
}

# -----------------------------------------------------------------------------
# Part 1: Single-Node Failed Runs Rerun
# -----------------------------------------------------------------------------
# 1A. FP8 KV Rerun with 1M Point included (35 min)
FP8_DIR="$STAGE2_ROOT/01_fp8_kv_rerun"
step s2_01_fp8_kv_rerun env NCCL_POLICY_LOG="$FP8_DIR/NCCL_ENV.txt" \
  "$VLLM_DIR/20_run_single_node_v6_aligned.sh" python3 "$VLLM_DIR/11_run_vllm_surrogate.py" \
  --cases "$SUITE_ROOT/stage2_cases_single_node.json" --case tp4_fp8_kv_fixed --out "$FP8_DIR" --port 8060
step s2_01_fp8_summarize python3 "$VLLM_DIR/15_summarize_vllm.py" "$FP8_DIR" --out "$FP8_DIR/summary"

# 1B. CPU KV Offload True Reuse Test (45 min)
OFFLOAD_DIR="$STAGE2_ROOT/02_cpu_offload_reuse"
step s2_02_cpu_offload_reuse env NCCL_POLICY_LOG="$OFFLOAD_DIR/NCCL_ENV.txt" \
  "$VLLM_DIR/20_run_single_node_v6_aligned.sh" python3 "$VLLM_DIR/11_run_vllm_surrogate.py" \
  --cases "$SUITE_ROOT/stage2_cases_single_node.json" --case tp4_native_offload_reuse_test --out "$OFFLOAD_DIR" --port 8070
step s2_02_offload_summarize python3 "$VLLM_DIR/15_summarize_vllm.py" "$OFFLOAD_DIR" --out "$OFFLOAD_DIR/summary"

# -----------------------------------------------------------------------------
# Part 2: Two-Node Distributed Concurrency Under Load (75 min)
# -----------------------------------------------------------------------------
if [[ -n "${NODE1_IP:-}" ]]; then
  # Verify no lingering traffic control caps exist before running native benchmarks
  LOCAL_IFACE=$(ip route get "$NODE1_IP" | awk '{for(i=1;i<=NF;i++) if($i=="dev"){print $(i+1); exit}}')
  sudo -n tc qdisc del dev "$LOCAL_IFACE" root 2>/dev/null || true
  ssh -i "$SSH_KEY" -o BatchMode=yes -o StrictHostKeyChecking=no "$NODE1_IP" \
    "sudo -n tc qdisc del dev \$(ip route get '$NODE0_IP' | awk '{for(i=1;i<=NF;i++) if(\$i==\"dev\"){print \$(i+1); exit}}') root 2>/dev/null || true" || true

  LOAD_DIR="$STAGE2_ROOT/03_multi_node_load"
  step s2_03_multi_node_load env OUT_ROOT="$LOAD_DIR" \
    CASES_FILE="$SUITE_ROOT/stage2_cases_multi_node_load.json" \
    V8_GCP_NETWORK_PROVENANCE_OVERRIDE="GCP_NATIVE" \
    GCP_NETWORK_PROVENANCE="GCP_NATIVE" \
    V8_VLLM_NETWORK_MODE="native" \
    "$VLLM_DIR/12_run_vllm_multi_node.sh" --group scaleout_load

  step s2_03_load_summarize python3 "$VLLM_DIR/15_summarize_vllm.py" "$LOAD_DIR" --out "$LOAD_DIR/summary"

  # ---------------------------------------------------------------------------
  # Part 3: Two-Node PP2 15/12 Layer Split Evaluation (30 min)
  # ---------------------------------------------------------------------------
  PP2_EVAL_DIR="$STAGE2_ROOT/04_pp2_split_evaluation"
  # (a) Run with VLLM_PP_LAYER_PARTITION=15,12
  step s2_04_pp2_split_15_12 env OUT_ROOT="$PP2_EVAL_DIR/split_15_12" \
    CASES_FILE="$SUITE_ROOT/stage2_cases_multi_node_load.json" \
    V8_GCP_NETWORK_PROVENANCE_OVERRIDE="GCP_NATIVE" \
    GCP_NETWORK_PROVENANCE="GCP_NATIVE" \
    V8_VLLM_NETWORK_MODE="native" \
    VLLM_PP_LAYER_PARTITION="15,12" \
    "$VLLM_DIR/12_run_vllm_multi_node.sh" --group pp2_split

  # (b) Run same cases with default 14/13 split as session control
  step s2_04_pp2_split_control env OUT_ROOT="$PP2_EVAL_DIR/split_control_default" \
    CASES_FILE="$SUITE_ROOT/stage2_cases_multi_node_load.json" \
    V8_GCP_NETWORK_PROVENANCE_OVERRIDE="GCP_NATIVE" \
    GCP_NETWORK_PROVENANCE="GCP_NATIVE" \
    V8_VLLM_NETWORK_MODE="native" \
    "$VLLM_DIR/12_run_vllm_multi_node.sh" --group pp2_split

  # Compare PP2 split delta
  python3 - <<'PY' "$PP2_EVAL_DIR"
import json, sys
from pathlib import Path
root = Path(sys.argv[1])
s15_file = list((root / "split_15_12").rglob("*128k_c1*.json"))
sdef_file = list((root / "split_control_default").rglob("*128k_c1*.json"))
res = {"split_15_12": {}, "split_default": {}, "delta_pct": {}}
if s15_file and sdef_file:
    try:
        d15 = json.load(open(s15_file[0]))
        ddef = json.load(open(sdef_file[0]))
        t15 = d15.get("mean_tpot_ms") or d15.get("median_tpot_ms")
        tdef = ddef.get("mean_tpot_ms") or ddef.get("median_tpot_ms")
        res["split_15_12"]["tpot_ms"] = t15
        res["split_default"]["tpot_ms"] = tdef
        if t15 and tdef:
            res["delta_pct"]["tpot_speedup_pct"] = ((tdef - t15) / tdef) * 100.0
    except Exception as e: res["error"] = str(e)
(root / "PP2_SPLIT_COMPARISON.json").write_text(json.dumps(res, indent=2))
print("PP2 Split Comparison:\n", json.dumps(res, indent=2))
PY

  # ---------------------------------------------------------------------------
  # Part 4: Capped Profiles & TP16 512K with Fixed Nsys Report Wait (45 min)
  # ---------------------------------------------------------------------------
  CAPPED_DIR="$STAGE2_ROOT/05_capped_profiles"
  step s2_05_capped_profiles env OUT_ROOT="$CAPPED_DIR" CAPPED_PROFILE_MODES="100g 20g" \
    "$VLLM_DIR/21_run_vllm_capped_profiles.sh"

  TP16_DIR="$STAGE2_ROOT/06_tp16_512k_prefill"
  step s2_06_tp16_512k_profile env OUT_ROOT="$TP16_DIR" PROFILE_TOPOLOGY_FILTER=tp16_pp1_dist \
    PROFILE_MODE_FILTER=long_prefill_512k RUN_HEAVY_PROFILE=1 \
    "$VLLM_DIR/18_run_vllm_multi_node_profiles.sh"
else
  echo "Skipping multi-node steps (NODE1_IP not configured in RUN_CONFIG.env)"
fi

echo "================================================================="
echo "  STAGE 2 COMPLETE: $STAGE2_ROOT"
echo "================================================================="
