#!/bin/bash
# Native execution without Docker isolation to preserve OpenMPI & PMIx environment
export LD_LIBRARY_PATH="/opt/cuda-13.0/lib64:/usr/mpi/gcc/openmpi-4.1.9a1/lib64:${LD_LIBRARY_PATH:-}"
exec /home/ayu23/rtx_g4_smoke/nccl-tests/build/sendrecv_perf "$@"
