#!/usr/bin/env bash
# ==============================================================================
# 01_preflight.sh — Environment Preflight Checks
# Target: kimi-node-0 (8× RTX PRO 6000, DeepSeek V4.1 Flash)
# ==============================================================================
set -euo pipefail

BOLD="\033[1m"; GREEN="\033[32m"; RED="\033[31m"; YELLOW="\033[33m"; RESET="\033[0m"
PASS="${GREEN}✔ PASS${RESET}"
FAIL="${RED}✘ FAIL${RESET}"
WARN="${YELLOW}⚠ WARN${RESET}"

MODEL_PATH="/data/models/deepseek-v4.1-flash"
GCS_BUCKET="gs://mevreon-deepseek-models/deepseek-ai/DeepSeek-V4.1-Flash"
CONTAINER_IMAGE="vllm/vllm-openai:deepseekv41-flash-0909"

echo -e "\n${BOLD}═══════════════════════════════════════════════════════════════${RESET}"
echo -e "${BOLD}  DeepSeek V4.1 Flash — Preflight Environment Check${RESET}"
echo -e "${BOLD}═══════════════════════════════════════════════════════════════${RESET}\n"

ERRORS=0

# ─── 1. GPU Check ─────────────────────────────────────────────────────────────
echo -e "${BOLD}[1/6] GPU Detection${RESET}"
GPU_COUNT=$(nvidia-smi --query-gpu=index --format=csv,noheader,nounits 2>/dev/null | wc -l || echo 0)
if [ "$GPU_COUNT" -ge 8 ]; then
    echo -e "  ${PASS}  ${GPU_COUNT} GPUs detected"
    nvidia-smi --query-gpu=index,name,memory.total --format=csv,noheader | head -8 | while read line; do
        echo "       GPU $line"
    done
else
    echo -e "  ${FAIL}  Expected 8 GPUs, found ${GPU_COUNT}"
    ERRORS=$((ERRORS+1))
fi

# ─── 2. Model Weights ────────────────────────────────────────────────────────
echo -e "\n${BOLD}[2/6] Model Weights${RESET}"
if [ -d "$MODEL_PATH" ]; then
    FILE_COUNT=$(find "$MODEL_PATH" -type f | wc -l)
    DIR_SIZE=$(du -sh "$MODEL_PATH" 2>/dev/null | cut -f1)
    if [ "$FILE_COUNT" -gt 10 ]; then
        echo -e "  ${PASS}  Model directory exists: ${MODEL_PATH}"
        echo "       Files: ${FILE_COUNT}, Size: ${DIR_SIZE}"
    else
        echo -e "  ${WARN}  Model directory exists but only ${FILE_COUNT} files (may be incomplete)"
        echo "       Run: gcloud storage rsync -r ${GCS_BUCKET} ${MODEL_PATH}"
    fi
else
    echo -e "  ${FAIL}  Model not found at ${MODEL_PATH}"
    echo "       Run: mkdir -p ${MODEL_PATH} && gcloud storage rsync -r ${GCS_BUCKET} ${MODEL_PATH}"
    ERRORS=$((ERRORS+1))
fi

# ─── 3. Docker ────────────────────────────────────────────────────────────────
echo -e "\n${BOLD}[3/6] Docker Runtime${RESET}"
if command -v docker &>/dev/null; then
    DOCKER_VER=$(docker --version 2>/dev/null)
    echo -e "  ${PASS}  ${DOCKER_VER}"
else
    echo -e "  ${FAIL}  Docker not found"
    ERRORS=$((ERRORS+1))
fi

# Check NVIDIA container toolkit
if docker info 2>/dev/null | grep -q "nvidia"; then
    echo -e "  ${PASS}  NVIDIA Container Toolkit detected"
else
    echo -e "  ${WARN}  NVIDIA Container Toolkit not detected in docker info (may still work with --gpus)"
fi

# Check if container image is available
if docker image inspect "$CONTAINER_IMAGE" &>/dev/null; then
    echo -e "  ${PASS}  Container image present: ${CONTAINER_IMAGE}"
else
    echo -e "  ${WARN}  Container image not cached locally: ${CONTAINER_IMAGE}"
    echo "       Will be pulled on first server start."
fi

# ─── 4. Traffic Control (tc) ─────────────────────────────────────────────────
echo -e "\n${BOLD}[4/6] Traffic Control (tc)${RESET}"
if command -v tc &>/dev/null; then
    echo -e "  ${PASS}  tc is available ($(which tc))"
else
    echo -e "  ${FAIL}  tc not found — install iproute2: apt-get install -y iproute2"
    ERRORS=$((ERRORS+1))
fi

# ─── 5. Python ────────────────────────────────────────────────────────────────
echo -e "\n${BOLD}[5/6] Python Environment${RESET}"
if command -v python3 &>/dev/null; then
    PY_VER=$(python3 --version 2>&1)
    echo -e "  ${PASS}  ${PY_VER}"
else
    echo -e "  ${FAIL}  python3 not found"
    ERRORS=$((ERRORS+1))
fi

# Check required modules
for mod in json subprocess pathlib urllib.request csv; do
    if python3 -c "import ${mod}" 2>/dev/null; then
        echo -e "  ${PASS}  Module: ${mod}"
    else
        echo -e "  ${FAIL}  Missing module: ${mod}"
        ERRORS=$((ERRORS+1))
    fi
done

# ─── 6. Network Interface ────────────────────────────────────────────────────
echo -e "\n${BOLD}[6/6] Network Interface${RESET}"
DEFAULT_IFACE=$(ip route show default 2>/dev/null | awk '{print $5}' | head -1 || echo "unknown")
if [ "$DEFAULT_IFACE" != "unknown" ] && [ -n "$DEFAULT_IFACE" ]; then
    echo -e "  ${PASS}  Default interface: ${DEFAULT_IFACE}"
    LINK_SPEED=$(ethtool "$DEFAULT_IFACE" 2>/dev/null | grep "Speed:" | awk '{print $2}' || echo "unknown")
    echo "       Link speed: ${LINK_SPEED}"
else
    echo -e "  ${WARN}  Could not detect default network interface"
fi

# ─── Summary ──────────────────────────────────────────────────────────────────
echo -e "\n${BOLD}═══════════════════════════════════════════════════════════════${RESET}"
if [ "$ERRORS" -eq 0 ]; then
    echo -e "  ${GREEN}${BOLD}ALL CHECKS PASSED${RESET} — Ready to run benchmarks."
else
    echo -e "  ${RED}${BOLD}${ERRORS} CHECK(S) FAILED${RESET} — Fix the above issues before proceeding."
    exit 1
fi
echo -e "${BOLD}═══════════════════════════════════════════════════════════════${RESET}\n"
