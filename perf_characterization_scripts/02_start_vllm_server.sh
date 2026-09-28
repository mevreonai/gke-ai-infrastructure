#!/usr/bin/env bash
# ==============================================================================
# 02_start_vllm_server.sh — Launch DeepSeek V4.1 Flash vLLM Server
# Target: kimi-node-0 (8× RTX PRO 6000)
# Model:  deepseek-ai/DeepSeek-V4.1-Flash (local: /data/models/deepseek-v4.1-flash)
# ==============================================================================
set -euo pipefail

BOLD="\033[1m"; GREEN="\033[32m"; RED="\033[31m"; YELLOW="\033[33m"; RESET="\033[0m"

CONTAINER_NAME="vllm-deepseek-perf"
CONTAINER_IMAGE="vllm/vllm-openai:deepseekv41-flash-0909"
MODEL_LOCAL="/data/models/deepseek-v4.1-flash"
MODEL_CONTAINER="/models/deepseek-ai/DeepSeek-V4.1-Flash"
SERVED_MODEL="deepseek-ai/DeepSeek-V4.1-Flash"
PORT=8000
STARTUP_TIMEOUT=1800  # 30 minutes max wait for model load

echo -e "\n${BOLD}═══════════════════════════════════════════════════════════════${RESET}"
echo -e "${BOLD}  DeepSeek V4.1 Flash — vLLM Server Launcher${RESET}"
echo -e "${BOLD}═══════════════════════════════════════════════════════════════${RESET}\n"

# ─── Stop any existing container ──────────────────────────────────────────────
if docker ps -q -f name="$CONTAINER_NAME" | grep -q .; then
    echo -e "${YELLOW}⚠ Stopping existing container: ${CONTAINER_NAME}${RESET}"
    docker stop "$CONTAINER_NAME" 2>/dev/null || true
    docker rm "$CONTAINER_NAME" 2>/dev/null || true
    sleep 2
fi

# ─── Verify model weights ────────────────────────────────────────────────────
if [ ! -d "$MODEL_LOCAL" ]; then
    echo -e "${RED}✘ Model weights not found at ${MODEL_LOCAL}${RESET}"
    echo "  Run: gcloud storage rsync -r gs://mevreon-deepseek-models/deepseek-ai/DeepSeek-V4.1-Flash ${MODEL_LOCAL}"
    exit 1
fi

echo -e "${GREEN}✔ Model weights found at ${MODEL_LOCAL}${RESET}"
echo ""

# ─── Launch vLLM container ───────────────────────────────────────────────────
echo -e "${BOLD}Launching vLLM server...${RESET}"
echo "  Container: ${CONTAINER_NAME}"
echo "  Image:     ${CONTAINER_IMAGE}"
echo "  Model:     ${SERVED_MODEL}"
echo "  TP:        8"
echo "  Port:      ${PORT}"
echo ""

docker run -d \
    --name "$CONTAINER_NAME" \
    --restart unless-stopped \
    --ipc host \
    --network host \
    --gpus all \
    -v "${MODEL_LOCAL}:${MODEL_CONTAINER}:ro" \
    "$CONTAINER_IMAGE" \
    vllm serve "${MODEL_CONTAINER}" \
        --tensor-parallel-size 8 \
        --tokenizer-mode deepseek_v41 \
        --language-model-only \
        --block-size 64 \
        --gpu-memory-utilization 0.92 \
        --served-model-name "${SERVED_MODEL}" \
        --trust-remote-code \
        --port ${PORT} \
        --host 0.0.0.0

echo -e "\n${BOLD}Waiting for server to be ready (up to ${STARTUP_TIMEOUT}s)...${RESET}"

# ─── Health check loop ───────────────────────────────────────────────────────
ELAPSED=0
INTERVAL=10
while [ $ELAPSED -lt $STARTUP_TIMEOUT ]; do
    # Check if container is still running
    if ! docker ps -q -f name="$CONTAINER_NAME" | grep -q .; then
        echo -e "\n${RED}✘ Container exited unexpectedly!${RESET}"
        echo "  Logs:"
        docker logs --tail 50 "$CONTAINER_NAME" 2>&1
        exit 1
    fi

    # Try the models endpoint
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:${PORT}/v1/models" 2>/dev/null || echo "000")
    if [ "$HTTP_CODE" = "200" ]; then
        echo -e "\n${GREEN}${BOLD}✔ Server is READY!${RESET}"
        echo ""
        echo "  Endpoint:  http://127.0.0.1:${PORT}/v1/completions"
        echo "  Model:     ${SERVED_MODEL}"
        echo "  Started in ~${ELAPSED}s"

        # Print served models
        echo ""
        echo -e "${BOLD}Served models:${RESET}"
        curl -s "http://127.0.0.1:${PORT}/v1/models" | python3 -m json.tool 2>/dev/null || true
        echo ""
        exit 0
    fi

    printf "  [%4ds / %ds] Waiting... (HTTP: %s)\r" "$ELAPSED" "$STARTUP_TIMEOUT" "$HTTP_CODE"
    sleep $INTERVAL
    ELAPSED=$((ELAPSED + INTERVAL))
done

echo -e "\n${RED}✘ Server did not become ready within ${STARTUP_TIMEOUT}s${RESET}"
echo "  Check logs: docker logs ${CONTAINER_NAME}"
exit 1
