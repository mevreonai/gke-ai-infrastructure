#!/usr/bin/env bash
set -e

echo "=== Extracting NVVM and NCCL headers from container ==="
CID=$(sudo docker create rtx-smoke:latest)
sudo docker cp "${CID}:/usr/local/cuda-13.0/nvvm" /opt/cuda-13.0/
sudo docker cp "${CID}:/usr/include/nccl.h" /opt/cuda-13.0/include/
sudo docker cp "${CID}:/usr/include/nccl_device.h" /opt/cuda-13.0/include/
sudo docker cp "${CID}:/usr/include/nccl_device" /opt/cuda-13.0/include/ || true
sudo docker rm "${CID}"

echo "=== NVVM contents ==="
ls -la /opt/cuda-13.0/nvvm/bin/

echo "=== Building nccl-tests with MPI on Host ==="
cd /home/ayu23/rtx_g4_smoke/nccl-tests
make clean
make -j$(nproc) \
  CUDA_HOME=/opt/cuda-13.0 \
  MPI=1 \
  MPI_HOME=/usr/mpi/gcc/openmpi-4.1.9a1 \
  CUDA_LIB=/opt/cuda-13.0/lib64 \
  NCCL_HOME=/opt/cuda-13.0

echo "=== Verifying build ==="
ls -lh build/
nm -D build/all_reduce_perf | grep -i MPI_Init || true
