#!/bin/bash
set -euo pipefail

CID=$(docker create rtx-smoke:latest)
docker cp "${CID}:/usr/local/cuda-13.0/targets" /opt/cuda-13.0/
docker cp "${CID}:/usr/include/nccl.h" /opt/cuda-13.0/include/ 2>/dev/null || true
docker rm "${CID}"

echo "Targets copied. Checking cuda_runtime.h:"
ls -la /opt/cuda-13.0/include/cuda_runtime.h
