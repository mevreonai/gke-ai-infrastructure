#!/bin/bash
set -euo pipefail

CID=$(docker create rtx-smoke:latest)
mkdir -p /opt/cuda-13.0/lib64
docker cp "${CID}:/usr/local/cuda/lib64/." /opt/cuda-13.0/lib64/
docker cp "${CID}:/lib/x86_64-linux-gnu/libnccl.so.2" /opt/cuda-13.0/lib64/
docker rm "${CID}"

echo '/opt/cuda-13.0/lib64' > /etc/ld.so.conf.d/cuda-13.conf
ldconfig
echo "CUDA 13 and NCCL installed to /opt/cuda-13.0/lib64 on $(hostname)"
