#!/bin/bash
set -euo pipefail

sudo chown -R $(id -u):$(id -g) $HOME/rtx_g4_smoke/nccl-tests
cd $HOME/rtx_g4_smoke/nccl-tests
export PATH="/opt/cuda-13.0/bin:$PATH"
export CUDA_HOME="/opt/cuda-13.0"
export MPI_HOME="/usr/mpi/gcc/openmpi-4.1.9a1"

make clean
# Build core collectives with MPI
make -C src BUILDDIR=$HOME/rtx_g4_smoke/nccl-tests/build \
    MPI=1 MPI_HOME="$MPI_HOME" CUDA_HOME="$CUDA_HOME" \
    CUDA_INC="$CUDA_HOME/include" -j$(nproc)

echo "=== Host nccl-tests build complete ==="
/usr/bin/ldd $HOME/rtx_g4_smoke/nccl-tests/build/all_reduce_perf
