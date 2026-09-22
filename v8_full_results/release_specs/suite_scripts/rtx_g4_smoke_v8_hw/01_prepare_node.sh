#!/usr/bin/env bash
# Run on BOTH GCP nodes once.
set -euo pipefail
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
source "$SCRIPT_DIR/00_smoke_common.sh"
init_smoke_env

: "${PEER_IP:?Set PEER_IP to the other node INTERNAL IP before running.}"
: "${V8_REBUILD_HW_TOOLS:=0}"

run_logged 010_system_inventory '
echo "===== HOST ====="
hostname -f
date --iso-8601=seconds
echo "===== GCP ZONE ====="
curl -s -H "Metadata-Flavor: Google" http://metadata.google.internal/computeMetadata/v1/instance/zone || true
echo
echo "===== OS ====="
uname -a
cat /etc/os-release
echo "===== NVIDIA ====="
nvidia-smi
nvidia-smi -L
echo "===== TOPOLOGY ====="
nvidia-smi topo -m
echo "===== NUMA ====="
numactl -H || true
echo "===== CPU ====="
lscpu
echo "===== PCI TREE ====="
lspci -tv
echo "===== GPU/NIC PCI ====="
lspci -nn | egrep -i "NVIDIA|Ethernet|Network"
echo "===== NETWORK ====="
ip -br addr
ip -br link
ip route
echo "===== CUDA/NCCL ====="
nvcc --version || true
ldconfig -p | grep -i nccl || true
dpkg -l | grep -i nccl || true
echo "===== ENV ====="
env | egrep "^(NCCL|CUDA|UCX|OMPI|FI_|LD_LIBRARY_PATH|PATH)=" | sort || true
'

run_logged 011_nvidia_pci 'nvidia-smi -q -d PCI'
run_logged 012_gpu_power_clock_info 'nvidia-smi -q -d POWER,CLOCK,PERFORMANCE,TEMPERATURE,MEMORY'

run_logged 020_install_packages '
sudo -n env DEBIAN_FRONTEND=noninteractive apt-get update &&
sudo -n env DEBIAN_FRONTEND=noninteractive apt-get install -y git build-essential cmake openmpi-bin libopenmpi-dev \
  iperf3 numactl pciutils ethtool iproute2 jq python3
'

run_logged 021_tool_versions '
git --version
gcc --version
g++ --version
cmake --version
mpirun --version
iperf3 --version
python3 --version
nvcc --version || true
'

# NCCL dev headers if missing.
run_logged 022_nccl_dev_headers '
if ! find /usr -name nccl.h 2>/dev/null | grep -q nccl.h; then
  sudo -n env DEBIAN_FRONTEND=noninteractive apt-get install -y libnccl2 libnccl-dev
fi
find /usr -name nccl.h 2>/dev/null | head -20
'

# NVBandwidth
run_logged 030_clone_nvbandwidth '
cd "$BENCH_ROOT"
if [ ! -d nvbandwidth/.git ]; then git clone https://github.com/NVIDIA/nvbandwidth.git; fi
cd nvbandwidth
git rev-parse HEAD
'
run_logged 031_build_nvbandwidth '
cd "$BENCH_ROOT/nvbandwidth"
if [ "${V8_REBUILD_HW_TOOLS:-0}" = "1" ] || ! find . -type f -name nvbandwidth -perm -111 | grep -q .; then
  cmake -S . -B build
  cmake --build build -j"$(nproc)"
else
  echo "Reusing existing nvbandwidth executable; set V8_REBUILD_HW_TOOLS=1 to rebuild."
fi
'

# NCCL tests
run_logged 040_clone_nccl_tests '
cd "$BENCH_ROOT"
if [ ! -d nccl-tests/.git ]; then git clone https://github.com/NVIDIA/nccl-tests.git; fi
cd nccl-tests
git rev-parse HEAD
'
run_logged 041_build_nccl_tests '
cd "$BENCH_ROOT/nccl-tests"
if [ "${V8_REBUILD_HW_TOOLS:-0}" = "1" ] || [ ! -x build/all_reduce_perf ] || [ ! -x build/sendrecv_perf ]; then
  make -j"$(nproc)" MPI=1 MPI_HOME=/usr
else
  echo "Reusing existing nccl-tests executables; set V8_REBUILD_HW_TOOLS=1 to rebuild."
fi
'
run_logged 042_list_nccl_binaries 'ls -lh "$BENCH_ROOT/nccl-tests/build/"*perf'

# BabelStream
run_logged 050_clone_babelstream '
cd "$BENCH_ROOT"
if [ ! -d BabelStream/.git ]; then git clone https://github.com/UoB-HPC/BabelStream.git; fi
cd BabelStream
git rev-parse HEAD
'
run_logged 051_build_babelstream '
cd "$BENCH_ROOT/BabelStream"
if [ "${V8_REBUILD_HW_TOOLS:-0}" = "1" ] || ! find build_cuda -type f -name cuda-stream -perm -111 2>/dev/null | grep -q .; then
  rm -rf build_cuda
  cmake -S . -B build_cuda -DMODEL=cuda -DCMAKE_CUDA_COMPILER="$(which nvcc)"
  cmake --build build_cuda -j"$(nproc)"
else
  echo "Reusing existing BabelStream executable; set V8_REBUILD_HW_TOOLS=1 to rebuild."
fi
'
run_logged 052_find_babelstream '
find "$BENCH_ROOT/BabelStream/build_cuda" -type f -name "cuda-stream" -perm -111 -print
'

# CUTLASS is useful but can take time. Set RUN_CUTLASS_BUILD=0 to skip.
if [ "${RUN_CUTLASS_BUILD:-1}" = "1" ]; then
  run_logged 060_clone_cutlass '
  cd "$BENCH_ROOT"
  if [ ! -d cutlass/.git ]; then git clone https://github.com/NVIDIA/cutlass.git; fi
  cd cutlass
  git rev-parse HEAD
  '
  run_logged 061_build_cutlass_profiler '
  cd "$BENCH_ROOT/cutlass"
  if [ "${V8_REBUILD_HW_TOOLS:-0}" = "1" ] || [ ! -x build_sm120/tools/profiler/cutlass_profiler ]; then
    rm -rf build_sm120
    cmake -S . -B build_sm120 \
      -DCUTLASS_NVCC_ARCHS=120a \
      -DCUTLASS_ENABLE_TESTS=OFF \
      -DCUTLASS_UNITY_BUILD_ENABLED=ON
    cmake --build build_sm120 --target cutlass_profiler -j"$(nproc)"
  else
    echo "Reusing existing CUTLASS profiler; set V8_REBUILD_HW_TOOLS=1 to rebuild."
  fi
  '
fi

log_note "PREPARE COMPLETE. RESULT_DIR=$RESULT_DIR"
