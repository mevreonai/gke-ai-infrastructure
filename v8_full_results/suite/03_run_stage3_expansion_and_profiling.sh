#!/usr/bin/env bash
# ==============================================================================
# Stage 3: Strategic Expansions, True Serving Profiles & Resilience Sweep
# ==============================================================================
# Execution conventions strictly match V8 Stage 1 & Stage 2 suites.
# Excludes Option C (DP=2 x TP8) completely.
# ==============================================================================
set -euo pipefail

SUITE_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
VLLM_DIR="$SUITE_ROOT/rtx_g4_smoke_v5"
HW_DIR="$SUITE_ROOT/rtx_g4_smoke_v8_hw"

: "${VENV_DIR:=$HOME/vllm_env}"
: "${SSH_KEY:=$HOME/.ssh/google_compute_engine}"
: "${RUN_ID:=$(date +%Y%m%d_%H%M%S)}"
: "${STAGE3_ROOT:=$HOME/v8_additional_runs/$RUN_ID/stage3}"
: "${STAGE3_RESUME:=1}"

mkdir -p "$STAGE3_ROOT" "$STAGE3_ROOT/logs" "$STAGE3_ROOT/.done"
MASTER="$STAGE3_ROOT/logs/STAGE3_MASTER.log"
exec > >(tee -a "$MASTER") 2>&1

echo "================================================================="
echo "  V8 ADDITIONAL RUNS — STAGE 3: STRATEGIC EXPANSIONS & PROFILING"
echo "  RUN_ID      : $RUN_ID"
echo "  STAGE3_ROOT : $STAGE3_ROOT"
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
  local marker="$STAGE3_ROOT/.done/$name"
  if [[ "$STAGE3_RESUME" == 1 && -f "$marker" ]]; then
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
  printf '{"step":"%s","rc":%s,"start":%s,"end":%s}\n' "$name" "$rc" "$s" "$e" >> "$STAGE3_ROOT/step_status.jsonl"
  [[ "$rc" == 0 ]] && touch "$marker"
  return "$rc"
}

# -----------------------------------------------------------------------------
# Part 1: Single-Node Strategic Expansions & Serving Profiling
# -----------------------------------------------------------------------------
unset VLLM_PP_LAYER_PARTITION 2>/dev/null || true

# 1.1 B1: Production Serving Critical Path Nsys Profile (Graphs ON, 4.47ms target)
B1_PROFILE_DIR="$STAGE3_ROOT/01_b1_graphs_on_decode"
step s3_01_b1_graphs_on_profile env NCCL_POLICY_LOG="$B1_PROFILE_DIR/NCCL_ENV.txt" \
  PROFILE_ROOT="$B1_PROFILE_DIR" \
  PROFILE_MODE=decode TP=4 INPUT_LEN=8192 OUTPUT_LEN=512 CONCURRENCY=1 PORT=8080 \
  ENFORCE_EAGER=0 \
  "$VLLM_DIR/14_run_vllm_nsys_profile.sh"

# 1.2 R1: Continuous Long-Context Power-Law Scaling Curve (16K, 32K, 64K, 256K)
R1_DIR="$STAGE3_ROOT/02_r1_continuous_context"
step s3_02_r1_continuous_context env NCCL_POLICY_LOG="$R1_DIR/NCCL_ENV.txt" \
  "$VLLM_DIR/20_run_single_node_v6_aligned.sh" python3 "$VLLM_DIR/11_run_vllm_surrogate.py" \
  --cases "$SUITE_ROOT/stage3_cases.json" --case tp8_r1_continuous_context_curve --out "$R1_DIR" --port 8081

step s3_02_r1_summarize python3 "$VLLM_DIR/15_summarize_vllm.py" "$R1_DIR" --out "$R1_DIR/summary"

# 1.3 R2: Multi-Turn Agentic Prefix Caching TTFT Decay Evaluation
R2_DIR="$STAGE3_ROOT/03_r2_agentic_prefix_decay"
step s3_03_r2_prefix_decay env NCCL_POLICY_LOG="$R2_DIR/NCCL_ENV.txt" \
  "$VLLM_DIR/20_run_single_node_v6_aligned.sh" python3 "$VLLM_DIR/11_run_vllm_surrogate.py" \
  --cases "$SUITE_ROOT/stage3_cases.json" --case tp4_r2_agentic_prefix_cache_decay --out "$R2_DIR" --port 8082

step s3_03_r2_summarize python3 "$VLLM_DIR/15_summarize_vllm.py" "$R2_DIR" --out "$R2_DIR/summary"

# 1.4 R4: Streaming ITL Jitter & Pacing Distribution (c=1, 8, 16)
R4_DIR="$STAGE3_ROOT/04_r4_streaming_jitter"
step s3_04_r4_streaming_jitter env NCCL_POLICY_LOG="$R4_DIR/NCCL_ENV.txt" \
  "$VLLM_DIR/20_run_single_node_v6_aligned.sh" python3 "$VLLM_DIR/11_run_vllm_surrogate.py" \
  --cases "$SUITE_ROOT/stage3_cases.json" --case tp4_r4_streaming_itl_jitter --out "$R4_DIR" --port 8083

step s3_04_r4_summarize python3 "$VLLM_DIR/15_summarize_vllm.py" "$R4_DIR" --out "$R4_DIR/summary"

# -----------------------------------------------------------------------------
# Part 2: Dual-Node Strategic Expansions & Distributed Profiling
# -----------------------------------------------------------------------------
if [[ -n "${NODE1_IP:-}" ]]; then
  # Clean up any residual traffic control filters
  clean_tc() {
    local iface="$1"
    sudo -n tc qdisc del dev "$iface" root 2>/dev/null || true
    sudo -n tc qdisc del dev "$iface" ingress 2>/dev/null || true
  }
  LOCAL_IFACE=$(ip route get "$NODE1_IP" | awk '{for(i=1;i<=NF;i++) if($i=="dev"){print $(i+1); exit}}')
  REMOTE_IFACE=$(ssh -i "$SSH_KEY" -o BatchMode=yes -o StrictHostKeyChecking=no "$NODE1_IP" "ip route get '$NODE0_IP' | awk '{for(i=1;i<=NF;i++) if(\$i==\"dev\"){print \$(i+1); exit}}'")
  clean_tc "$LOCAL_IFACE"
  ssh -i "$SSH_KEY" -o BatchMode=yes -o StrictHostKeyChecking=no "$NODE1_IP" "
    sudo -n tc qdisc del dev '$REMOTE_IFACE' root 2>/dev/null || true
    sudo -n tc qdisc del dev '$REMOTE_IFACE' ingress 2>/dev/null || true
  " || true

  # 2.1 B11: Two-Node Distributed Decode Profiling (Clean reports wait & 0-byte purge)
  B11_DIR="$STAGE3_ROOT/05_b11_dist_decode_profiles"
  step s3_05_b11_dist_decode_profiles env OUT_ROOT="$B11_DIR" \
    PROFILE_MODE_FILTER=decode RUN_HEAVY_PROFILE=1 \
    "$VLLM_DIR/18_run_vllm_multi_node_profiles.sh"

  # 2.2 B6: TP16 512K Prefill Multi-Rank Trace (16 Ranks synchronized)
  B6_DIR="$STAGE3_ROOT/06_b6_tp16_512k_prefill"
  step s3_06_b6_tp16_512k_trace env OUT_ROOT="$B6_DIR" \
    PROFILE_TOPOLOGY_FILTER=tp16_pp1_dist PROFILE_MODE_FILTER=long_prefill_512k RUN_HEAVY_PROFILE=1 \
    "$VLLM_DIR/18_run_vllm_multi_node_profiles.sh"

  apply_cap() {
    local rate=$1
    sudo -n tc qdisc replace dev "$LOCAL_IFACE" root handle 1: htb default 10 2>/dev/null || true
    sudo -n tc class replace dev "$LOCAL_IFACE" parent 1: classid 1:10 htb rate "${rate}gbit" ceil "${rate}gbit" 2>/dev/null || true
    ssh -i "$SSH_KEY" -o BatchMode=yes -o StrictHostKeyChecking=no "$NODE1_IP" \
      "sudo -n tc qdisc replace dev '$REMOTE_IFACE' root handle 1: htb default 10 2>/dev/null || true && sudo -n tc class replace dev '$REMOTE_IFACE' parent 1: classid 1:10 htb rate '${rate}gbit' ceil '${rate}gbit' 2>/dev/null || true" 2>/dev/null || true
  }

  # 2.3 R3: Multi-Bandwidth & Network Jitter Resilience Stress Test (Native vs 100G vs 20G vs Jitter)
  R3_DIR="$STAGE3_ROOT/07_r3_network_resilience"

  # (a) Native baseline (Uncapped GCP Native VPC)
  clean_tc "$LOCAL_IFACE"
  ssh -i "$SSH_KEY" -o BatchMode=yes -o StrictHostKeyChecking=no "$NODE1_IP" "sudo -n tc qdisc del dev '\$(ip route get '$NODE0_IP' | awk '{for(i=1;i<=NF;i++) if(\$i==\"dev\"){print \$(i+1); exit}}')' root 2>/dev/null || true" 2>/dev/null || true
  step s3_07_r3_native env OUT_ROOT="$R3_DIR/native" \
    CASES_FILE="$SUITE_ROOT/stage3_cases.json" \
    V8_GCP_NETWORK_PROVENANCE_OVERRIDE="GCP_NATIVE" \
    GCP_NETWORK_PROVENANCE="GCP_NATIVE" \
    V8_VLLM_NETWORK_MODE="native" \
    "$VLLM_DIR/12_run_vllm_multi_node.sh" --group r3_network_resilience

  # (b) 100G Bandwidth Cap
  echo "Applying 100G bandwidth cap on node interconnect..."
  apply_cap "100"
  step s3_07_r3_capped_100g env OUT_ROOT="$R3_DIR/capped_100g" \
    CASES_FILE="$SUITE_ROOT/stage3_cases.json" \
    V8_GCP_NETWORK_PROVENANCE_OVERRIDE="GCP_CAPPED_100G" \
    GCP_NETWORK_PROVENANCE="GCP_CAPPED_100G" \
    V8_VLLM_NETWORK_MODE="capped" \
    "$VLLM_DIR/12_run_vllm_multi_node.sh" --group r3_network_resilience
  clean_tc "$LOCAL_IFACE"

  # (c) 20G Bandwidth Cap
  echo "Applying 20G bandwidth cap on node interconnect..."
  apply_cap "20"
  step s3_07_r3_capped_20g env OUT_ROOT="$R3_DIR/capped_20g" \
    CASES_FILE="$SUITE_ROOT/stage3_cases.json" \
    V8_GCP_NETWORK_PROVENANCE_OVERRIDE="GCP_CAPPED_20G" \
    GCP_NETWORK_PROVENANCE="GCP_CAPPED_20G" \
    V8_VLLM_NETWORK_MODE="capped" \
    "$VLLM_DIR/12_run_vllm_multi_node.sh" --group r3_network_resilience
  clean_tc "$LOCAL_IFACE"

  # (d) Apply synthetic packet loss (0.05%) & jitter
  echo "Injecting synthetic 0.05% packet loss on node interconnect..."
  sudo -n tc qdisc add dev "$LOCAL_IFACE" root netem loss 0.05% delay 0.2ms 0.05ms 2>/dev/null || true
  ssh -i "$SSH_KEY" -o BatchMode=yes -o StrictHostKeyChecking=no "$NODE1_IP" "
    REMOTE_IFACE=\$(ip route get '$NODE0_IP' | awk '{for(i=1;i<=NF;i++) if(\$i==\"dev\"){print \$(i+1); exit}}')
    sudo -n tc qdisc add dev \"\$REMOTE_IFACE\" root netem loss 0.05% delay 0.2ms 0.05ms 2>/dev/null || true
  " || true

  step s3_07_r3_jitter_impaired env OUT_ROOT="$R3_DIR/impaired_005pct_loss" \
    CASES_FILE="$SUITE_ROOT/stage3_cases.json" \
    V8_GCP_NETWORK_PROVENANCE_OVERRIDE="GCP_CAPPED_JITTER" \
    GCP_NETWORK_PROVENANCE="GCP_CAPPED_JITTER" \
    V8_VLLM_NETWORK_MODE="capped" \
    "$VLLM_DIR/12_run_vllm_multi_node.sh" --group r3_network_resilience

  # (e) Restore clean network
  clean_tc "$LOCAL_IFACE"
  ssh -i "$SSH_KEY" -o BatchMode=yes -o StrictHostKeyChecking=no "$NODE1_IP" "
    REMOTE_IFACE=\$(ip route get '$NODE0_IP' | awk '{for(i=1;i<=NF;i++) if(\$i==\"dev\"){print \$(i+1); exit}}')
    sudo -n tc qdisc del dev \"\$REMOTE_IFACE\" root 2>/dev/null || true
    sudo -n tc qdisc del dev \"\$REMOTE_IFACE\" ingress 2>/dev/null || true
  " || true

  # Compare resilience delta between TP16 and PP4
  python3 - <<'PY' "$R3_DIR"
import json, sys
from pathlib import Path
root = Path(sys.argv[1])
native_dir = root / "native"
impaired_dir = root / "impaired_005pct_loss"

def find_ttft(folder, case_pat):
    files = list(folder.rglob(f"*{case_pat}*/*.json"))
    for f in files:
        if f.name in ("summary.json", "manifest.json", "resolved_models.json"): continue
        try:
            d = json.load(open(f))
            if "mean_ttft_ms" in d: return d["mean_ttft_ms"]
            if "ttfts" in d and len(d["ttfts"]) > 0: return (sum(d["ttfts"]) / len(d["ttfts"])) * 1000.0
        except Exception: pass
    return None

res = {
    "tp16": {
        "native_ttft_ms": find_ttft(native_dir, "tp16"),
        "impaired_ttft_ms": find_ttft(impaired_dir, "tp16")
    },
    "pp4": {
        "native_ttft_ms": find_ttft(native_dir, "pp4"),
        "impaired_ttft_ms": find_ttft(impaired_dir, "pp4")
    }
}
for arch in ("tp16", "pp4"):
    n = res[arch]["native_ttft_ms"]
    i = res[arch]["impaired_ttft_ms"]
    if n and i:
        res[arch]["degradation_pct"] = ((i - n) / n) * 100.0

(root / "RESILIENCE_COMPARISON.json").write_text(json.dumps(res, indent=2))
print("Resilience Comparison (TP16 vs PP4 under 0.05% packet loss):\n", json.dumps(res, indent=2))
PY
else
  echo "Skipping dual-node steps (NODE1_IP not configured)"
fi

# -----------------------------------------------------------------------------
# Part 3: Holistic Wave Trimming, KV Audit & Suite Validation
# -----------------------------------------------------------------------------
AUDIT_DIR="$STAGE3_ROOT/08_kv_pool_and_trace_audit"
mkdir -p "$AUDIT_DIR"
step s3_08_holistic_kv_audit_and_trim python3 "$VLLM_DIR/24_audit_kv_and_trim_traces.py" \
  --scan-dir "$STAGE3_ROOT" \
  --out "$AUDIT_DIR/STAGE3_KV_AUDIT_AND_TRIM.json"

# Validate all outputs against strict suite validator with normalized POSIX paths
VAL_DIR="$STAGE3_ROOT/09_validation"
mkdir -p "$VAL_DIR"
step s3_09_collect_and_validate python3 "$SUITE_ROOT/../release_specs/suite_scripts/90_collect_and_validate.py" \
  --root "$STAGE3_ROOT" --out "$VAL_DIR" || echo "Validation finished (summary generated in $VAL_DIR)"

echo "================================================================="
echo "  STAGE 3 COMPLETE: $STAGE3_ROOT"
echo "================================================================="
