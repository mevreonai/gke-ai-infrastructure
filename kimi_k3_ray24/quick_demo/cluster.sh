#!/usr/bin/env bash
# ==============================================================================
# cluster.sh - Automated Management for Kimi-K3 24-GPU Cluster
#
# Usage:
#   ./cluster.sh start   - Power ON all 3 nodes (Ray & vLLM boot automatically)
#   ./cluster.sh status  - Inspect VM states, Ray 24-GPU topology, & API endpoint
#   ./cluster.sh logs    - Stream real-time model loading logs (Ctrl+C to exit)
#   ./cluster.sh query   - Send a live completion query to the 24-GPU model
#   ./cluster.sh stop    - Power OFF all 3 nodes to pause compute billing
# ==============================================================================

set -euo pipefail

PROJECT="mevreon"
ACTION="${1:-status}"

case "$ACTION" in
    start)
        echo -e "\n========================================================"
        echo " Starting Kimi-K3 Distributed Cluster (24x RTX 6000 Pro)"
        echo "========================================================"
        NODES=("kimi-node-0:us-central1-b:Head" "kimi-node-1:us-central1-b:Worker-1" "kimi-node-2:us-west1-a:Worker-2")
        for ENTRY in "${NODES[@]}"; do
            IFS=":" read -r NODE ZONE ROLE <<< "$ENTRY"
            ATTEMPT=1
            SUCCESS=0
            while [ $SUCCESS -eq 0 ]; do
                echo ">> Starting $NODE ($ROLE) in $ZONE..."
                if gcloud compute instances start "$NODE" --zone="$ZONE" --project="$PROJECT" --quiet; then
                    SUCCESS=1
                    echo "   [OK] $NODE is RUNNING!"
                else
                    echo "   [!] Zone capacity lock. Retrying in 10s (Attempt $ATTEMPT)..."
                    sleep 10
                    ATTEMPT=$((ATTEMPT + 1))
                fi
            done
        done
        echo -e "\n========================================================"
        echo " Auto-Boot Sequence Initialized"
        echo " - Ray Cluster and vLLM are automatically launching via systemd."
        echo " - To watch weight loading: ./cluster.sh logs"
        echo " - To test the endpoint:     ./cluster.sh query"
        echo "========================================================\n"
        ;;

    status)
        echo -e "\n=== [1/3] Compute Engine VM Status ==="
        gcloud compute instances list --project="$PROJECT" --filter="name ~ kimi-node" \
            --format="table(name, zone, status, machineType.basename(), networkInterfaces[0].networkIP:label=INTERNAL_IP, networkInterfaces[0].accessConfigs[0].natIP:label=EXTERNAL_IP)"

        echo -e "\n=== [2/3] Ray 24-GPU Cluster Health ==="
        gcloud compute ssh kimi-node-0 --zone=us-central1-b --project="$PROJECT" \
            --command="docker exec ray-head ray status 2>/dev/null || echo 'Ray cluster starting up...'"

        echo -e "\n=== [3/3] vLLM Inference API Server (Port 8000) ==="
        gcloud compute ssh kimi-node-0 --zone=us-central1-b --project="$PROJECT" \
            --command="curl -s http://localhost:8000/v1/models 2>/dev/null || echo 'vLLM is currently loading weights into GPUs (Port 8000 not yet open)'"
        ;;

    logs)
        echo -e "\n=== Streaming Live Loading Logs (Ctrl+C to exit) ==="
        gcloud compute ssh kimi-node-0 --zone=us-central1-b --project="$PROJECT" \
            --command="docker exec ray-head bash -c 'tail -f \$(ls -S /tmp/ray/session_latest/logs/worker-*.err | head -n 1)'"
        ;;

    query)
        echo -e "\n=== Querying Kimi-K3 (24 GPUs) ==="
        PROMPT="Explain quantum computing and why 24 GPUs are needed for 1.45 TB MoE models in 2 concise sentences."
        echo -e "Prompt: $PROMPT\n"
        gcloud compute ssh kimi-node-0 --zone=us-central1-b --project="$PROJECT" \
            --command="curl -s -X POST http://localhost:8000/v1/chat/completions -H 'Content-Type: application/json' -d '{\"model\": \"moonshotai/Kimi-K3\", \"messages\": [{\"role\": \"system\", \"content\": \"You are Moonshot AI Kimi-K3 running on a 24-GPU cluster.\"}, {\"role\": \"user\", \"content\": \"$PROMPT\"}], \"max_tokens\": 120, \"temperature\": 0.6}' | jq ."
        ;;

    stop)
        echo -e "\n=== Stopping Cluster Nodes (Pausing Billing) ==="
        gcloud compute instances stop kimi-node-0 --zone=us-central1-b --project="$PROJECT" --quiet &
        gcloud compute instances stop kimi-node-1 --zone=us-central1-b --project="$PROJECT" --quiet &
        gcloud compute instances stop kimi-node-2 --zone=us-west1-a --project="$PROJECT" --quiet &
        wait
        echo -e "\nAll 3 nodes stopped. GPU billing paused. Model disks preserved."
        ;;

    *)
        echo "Usage: ./cluster.sh [start | status | logs | query | stop]"
        exit 1
        ;;
esac
