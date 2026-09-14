#!/usr/bin/env bash
# ==============================================================================
# 03_setup_ray.sh
# Form a 3-node, 24-GPU Ray Cluster for Kimi-K3 Inference
# Usage:
#   ./03_setup_ray.sh head                  (Run on kimi-node-0)
#   ./03_setup_ray.sh worker <HEAD_IP>      (Run on kimi-node-1 and kimi-node-2)
#   ./03_setup_ray.sh status                (Check cluster health)
# ==============================================================================

set -euo pipefail

ROLE="${1:-status}"

case "$ROLE" in
    head)
        echo "=== Initializing Ray Head Node on $(hostname) ==="
        docker rm -f ray-head 2>/dev/null || true

        docker run -d --name ray-head \
            --net=host \
            --ipc=host \
            --gpus all \
            --ulimit nofile=1048576:1048576 \
            -v /data/models/kimi-k3:/models/kimi-k3 \
            --entrypoint /bin/bash \
            vllm-ray:latest \
            -c "ray start --head --port=6379 --num-gpus=8 --block"

        HEAD_IP=$(hostname -I | awk '{print $1}')
        echo "======================================================================"
        echo " Ray Head is RUNNING!"
        echo " Head Internal IP: $HEAD_IP"
        echo " Join command for worker nodes:"
        echo "   ./03_setup_ray.sh worker $HEAD_IP"
        echo "======================================================================"
        ;;

    worker)
        HEAD_IP="${2:-10.128.0.39}"
        echo "=== Joining Ray Cluster at $HEAD_IP:6379 from $(hostname) ==="
        
        CONTAINER_NAME="ray-worker"
        docker rm -f "$CONTAINER_NAME" 2>/dev/null || true

        docker run -d --name "$CONTAINER_NAME" \
            --net=host \
            --ipc=host \
            --gpus all \
            --ulimit nofile=1048576:1048576 \
            -v /data/models/kimi-k3:/models/kimi-k3 \
            --entrypoint /bin/bash \
            vllm-ray:latest \
            -c "ray start --address=$HEAD_IP:6379 --num-gpus=8 --block"

        echo "======================================================================"
        echo " Worker node successfully joined the Ray Cluster!"
        echo "======================================================================"
        ;;

    status)
        echo "=== Ray Cluster Status ==="
        docker exec ray-head ray status
        ;;

    *)
        echo "Unknown option: $ROLE"
        echo "Usage: ./03_setup_ray.sh [head | worker <HEAD_IP> | status]"
        exit 1
        ;;
esac
