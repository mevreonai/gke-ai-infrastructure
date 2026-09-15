# RTX PRO 6000 — GCP 2-Node Smoke-Test Runbook (v2)
## Calibrate the 3-node Kimi K3 performance model without loading Kimi K3

**Audience:** intern / lab engineer  
**Target:** 2 × GCP `g4-standard-384`, each with 8 × NVIDIA RTX PRO 6000 Blackwell Server Edition 96 GB  
**Goal:** collect reproducible measurements for the separate **3-node / 24-GPU Kimi K3 TP8×PP3 system**, especially:
- TP4 vs TP8 intra-node communication
- dual-NUMA / cross-socket penalty
- PP-like node-to-node transfer cost
- 10/20 GbE sensitivity
- host↔GPU PCIe bandwidth relevant to CPU KV offload
- GPU DRAM bandwidth
- GPU GEMM/compute capability
- clocks/power/utilization during each test

> **Do not download Kimi K3 or run vLLM for this smoke test.**
> This runbook measures the primitives used by the analytical model. It does **not** replace a later Kimi/vLLM end-to-end benchmark.

---

# A. Coverage: what this smoke test does and does not measure

| Area | Covered? | Tool / test |
|---|---:|---|
| GPU topology / NUMA / PCIe routing | **Yes** | `nvidia-smi topo -m`, `numactl`, `lspci` |
| TP4 collective latency / bandwidth | **Yes** | `nccl-tests all_reduce_perf` |
| TP8 collective latency / bandwidth | **Yes** | `nccl-tests all_reduce_perf` |
| AllGather / ReduceScatter sensitivity | **Yes** | `nccl-tests` |
| Cross-node PP-like transfer | **Yes** | `sendrecv_perf` |
| Native GCP host networking | **Yes** | `iperf3`, ping |
| 20 Gb/s and 10 Gb/s sensitivity | **Yes** | Linux `tc` + NCCL send/recv |
| GPU↔GPU PCIe P2P bandwidth / latency | **Yes** | NVIDIA NVBandwidth |
| CPU↔GPU H2D/D2H | **Yes** | NVIDIA NVBandwidth |
| GPU local DRAM bandwidth | **Yes** | BabelStream CUDA |
| GPU GEMM / Tensor Core compute | **Yes, reference only** | NVIDIA CUTLASS profiler |
| GPU clocks / power / utilization | **Yes** | `nvidia-smi dmon` + query logger |
| PCIe / DRAM / tensor profiling counters | **Optional** | NVIDIA DCGM if installed |
| Kimi MXFP4 kernel performance | **No** | requires actual vLLM/K3 path |
| KDA / MLA kernel behavior | **No** | requires actual Kimi model |
| vLLM scheduler / KV-block eviction | **No** | requires vLLM |
| CPU-offload cache lookup / restore overhead | **Partially** | raw H2D/D2H only; connector overhead requires vLLM |
| Actual 512K / 1M TTFT | **No** | later end-to-end test |

**Key point:** after this run we should have enough real data to replace the assumed
`alpha`/`beta` communication terms and the raw PCIe/DRAM/compute ceilings in the Kimi performance model.

---


# A1. CRITICAL: GCP network results are NOT directly transferable to the local 3-node lab

This is a **calibration experiment**, not a hardware clone.

The GCP and local systems have materially different network stacks:

### GCP `g4-standard-384`

- up to **400 Gb/s** VM network bandwidth
- **2 physical NICs**
- Google Titanium/gVNIC-based networking
- G4 multi-host networking uses **standard TCP/IP**
- G4 does **not** provide the A3/A4 GPUDirect-TCPX/TCPXO/RDMA path
- GCP has its own virtualization/offload, queueing, NUMA, MTU and routing characteristics

### Local 3-node Kimi system

Current information:

- **2 × 10 GbE per node**
- exact NIC model: **TBD**
- exact bonding/LACP/ECMP configuration: **TBD**
- exact MTU: **TBD**
- NIC-to-socket affinity: **TBD**
- RSS / queue configuration: **TBD**
- RDMA/RoCE support: **TBD**
- GPU-direct / peer-memory support: **TBD**
- actual NCCL network transport: **TBD**

Therefore:

> **Do NOT plug GCP native network bandwidth/latency directly into the local Kimi model.**

The benchmark output must be tagged and interpreted using three distinct classes.

| Result class | Example | How it is used |
|---|---|---|
| **GCP_NATIVE** | native `iperf3`, native NCCL send/recv | GCP reference only; do **not** use as local-cluster input |
| **GCP_CAPPED_20G / GCP_CAPPED_10G** | `tc`-limited send/recv | bandwidth-sensitivity experiment; useful mainly for the **beta / serialization** term |
| **LOCAL_REAL** | later results from team's 3-node nodes | authoritative input for the final local Kimi model |

## What the 10/20 Gb/s GCP shaping experiment DOES model

It helps answer:

```text
How much does reducing available payload bandwidth from hundreds of Gb/s
to approximately 20 Gb/s or 10 Gb/s increase a PP-like transfer time?
```

This is useful for estimating the bandwidth term:

```text
T_network(S) ≈ alpha + S / BW_effective
```

especially for 64 MiB / 128 MiB / 256 MiB transfers.

## What the GCP shaping experiment DOES NOT reproduce

Linux `tc` limiting a GCP NIC to 10 Gb/s does **not** turn it into the team's 10-GbE NIC.

It does not reproduce:

- local NIC hardware latency
- PCIe placement of the NIC
- CPU socket crossing to reach the NIC
- NIC DMA efficiency
- IRQ / RSS behavior
- TCP segmentation/offload implementation
- MTU / jumbo-frame behavior
- number of hardware queues
- bonding/LACP implementation
- switch buffering
- oversubscription
- NIC firmware
- local kernel tuning
- local NCCL socket-thread behavior
- congestion on the physical switch
- packet loss / retransmission behavior

Consequently:

> Treat `GCP_CAPPED_10G` as a **bandwidth-controlled reference / optimistic lower bound**, not as a prediction of the real local 10-GbE PP latency.

The final local-network model must replace both `alpha_NET` and `BW_NET` using the local team's measurements.

---

# A2. Which GCP measurements are portable to the local performance model?

Use this hierarchy.

| Measurement | Portability | Reason |
|---|---:|---|
| RTX PRO 6000 local GDDR bandwidth | **High-ish** | same GPU SKU, but clocks/power/thermal limits can differ |
| CUTLASS compute roof | **High-ish** | same GPU architecture; system power/clocks still matter |
| GPU H2D/D2H | **Medium** | depends strongly on CPU, NUMA and PCIe topology |
| TP4 same-island NCCL | **Medium** | useful reference if local PCIe topology is similar |
| TP8 cross-NUMA NCCL | **Low–Medium** | GCP has enhanced P2P behavior that local OEM may not match |
| GCP native network | **Very Low** | different NIC/platform and much higher line rate |
| GCP 10/20G capped network | **Medium for bandwidth sensitivity only** | line-rate effect modeled; latency/offload stack not reproduced |
| Local team's actual `iperf3` / NCCL sendrecv | **Authoritative** | final network inputs |
| Local team's actual TP4/TP8 NCCL | **Authoritative** | final TP communication inputs |

---

# A3. Network parameters the local team must later provide

When the local team responds, collect these before finalizing the Kimi model:

```text
NIC vendor/model:
NIC firmware:
PCIe generation / width:
NIC NUMA node / CPU socket:
Number of 10-GbE NICs:
Bonded? yes/no:
Bonding mode:
LACP? yes/no:
MTU:
RSS queue count:
IRQ affinity:
ethtool offload settings:
NCCL_SOCKET_IFNAME:
NCCL_SOCKET_NTHREADS:
NCCL_NSOCKS_PERTHREAD:
RoCE/RDMA available?:
GPUDirect RDMA available?:
iperf3 P1:
iperf3 P8:
iperf3 P32:
iperf3 reverse:
ping RTT:
NCCL sendrecv @ 16K:
NCCL sendrecv @ 128K:
NCCL sendrecv @ 512K:
NCCL sendrecv @ 64M:
NCCL sendrecv @ 128M:
NCCL sendrecv @ 256M:
```

Run on the local machines:

```bash
lspci -nn | egrep -i "Ethernet|Network"
lspci -tv
ip -br link
ip route
ethtool <iface>
ethtool -i <iface>
ethtool -k <iface>
ethtool -l <iface>
ethtool -g <iface>
cat /proc/interrupts | grep -i <iface>
numactl -H
nvidia-smi topo -m
```

The NIC's NUMA/socket placement is especially important because PP traffic can incur:

```text
GPU -> PCIe root -> CPU/NUMA path -> NIC
```

and potentially cross the socket fabric before reaching Ethernet.

---

# A4. Required provenance tag in every network result

Before every network test, log a provenance tag.

For native GCP:

```bash
export NETWORK_PROVENANCE=GCP_NATIVE
log_note "NETWORK_PROVENANCE=$NETWORK_PROVENANCE"
```

For 20-Gb/s shaping:

```bash
export NETWORK_PROVENANCE=GCP_CAPPED_20G
log_note "NETWORK_PROVENANCE=$NETWORK_PROVENANCE"
```

For 10-Gb/s shaping:

```bash
export NETWORK_PROVENANCE=GCP_CAPPED_10G
log_note "NETWORK_PROVENANCE=$NETWORK_PROVENANCE"
```

When the team's local cluster is eventually tested:

```bash
export NETWORK_PROVENANCE=LOCAL_REAL
log_note "NETWORK_PROVENANCE=$NETWORK_PROVENANCE"
```

Do not merge results from different provenance classes in a single averaged metric.


# B. Official references

- Google Cloud G4 / GPU VM documentation  
  https://cloud.google.com/compute/docs/gpus

- Google Cloud accelerator-optimized machines / G4 P2P  
  https://cloud.google.com/compute/docs/accelerator-optimized-machines

- Google G4 P2P architecture  
  https://cloud.google.com/blog/products/compute/g4-vms-p2p-fabric-boosts-multi-gpu-workloads

- NVIDIA NCCL tests  
  https://github.com/NVIDIA/nccl-tests

- NCCL performance definitions (`time`, `algbw`, `busbw`)  
  https://github.com/NVIDIA/nccl-tests/blob/master/doc/PERFORMANCE.md

- NVIDIA NCCL environment variables  
  https://docs.nvidia.com/deeplearning/nccl/user-guide/docs/env.html

- NVIDIA NVBandwidth  
  https://github.com/NVIDIA/nvbandwidth

- NVIDIA CUTLASS profiler  
  https://github.com/NVIDIA/cutlass  
  https://github.com/NVIDIA/cutlass/blob/main/media/docs/cpp/profiler.md

- BabelStream GPU memory-bandwidth benchmark  
  https://github.com/UoB-HPC/BabelStream

- NVIDIA DCGM profiling metrics  
  https://docs.nvidia.com/datacenter/dcgm/latest/learn/modules/profiling.html

---

# 1. Required GCP setup

Use:

```text
2 × g4-standard-384
8 × RTX PRO 6000 per VM
16 GPUs total
```

Both VMs must be:

- in the **same GCP zone**
- same VPC/subnet
- reachable using **internal IP**
- same OS image
- same NVIDIA driver / CUDA / NCCL stack

If possible, use the same driver/CUDA/NCCL versions as the local 3-node cluster.
If not possible, record versions exactly and **do not change them halfway through**.

---

# 2. One-time shell setup on BOTH nodes

Set node-specific addresses manually.

### Node 0

```bash
export NODE0_IP=<NODE0_INTERNAL_IP>
export NODE1_IP=<NODE1_INTERNAL_IP>
export PEER_IP=$NODE1_IP
```

### Node 1

```bash
export NODE0_IP=<NODE0_INTERNAL_IP>
export NODE1_IP=<NODE1_INTERNAL_IP>
export PEER_IP=$NODE0_IP
```

Now create the benchmark directory:

```bash
export BENCH_ROOT=$HOME/rtx_g4_smoke
export RUN_ID=$(date +%Y%m%d_%H%M%S)
export HOST_SHORT=$(hostname -s)
export RESULT_DIR=$BENCH_ROOT/results/$RUN_ID/$HOST_SHORT
mkdir -p "$RESULT_DIR"
```

---

# 3. REQUIRED: enable command logging before running tests

This section is important.

Every benchmark command will:

1. print the **test name**
2. print the **exact command**
3. record host / start / end time
4. record stdout + stderr
5. record exit code
6. append to one **master log**
7. also write a **per-test log file**

Paste this block exactly into the shell on both nodes:

```bash
export MASTER_LOG="$RESULT_DIR/MASTER_${RUN_ID}_${HOST_SHORT}.log"

touch "$MASTER_LOG"

log_note() {
  local msg="$*"
  {
    echo
    echo "================================================================"
    echo "NOTE"
    echo "HOST      : $(hostname -f)"
    echo "TIME      : $(date --iso-8601=seconds)"
    echo "MESSAGE   : $msg"
    echo "================================================================"
  } | tee -a "$MASTER_LOG"
}

run_logged() {
  local label="$1"
  shift
  local cmd="$*"
  local outfile="$RESULT_DIR/${label}.log"

  {
    echo
    echo "================================================================"
    echo "TEST      : $label"
    echo "HOST      : $(hostname -f)"
    echo "START     : $(date --iso-8601=seconds)"
    echo "PWD       : $(pwd)"
    echo "COMMAND   : $cmd"
    echo "----------------------------------------------------------------"
  } | tee -a "$MASTER_LOG" "$outfile"

  set +e
  bash -lc "set -o pipefail; $cmd" \
    > >(tee -a "$MASTER_LOG" "$outfile") \
    2> >(tee -a "$MASTER_LOG" "$outfile" >&2)
  local rc=$?
  set -e

  {
    echo "----------------------------------------------------------------"
    echo "END       : $(date --iso-8601=seconds)"
    echo "EXIT_CODE : $rc"
    echo "================================================================"
  } | tee -a "$MASTER_LOG" "$outfile"

  return $rc
}
```

Test the logger:

```bash
run_logged 000_logger_test 'echo "logger works"; hostname; date'
```

The file should exist:

```bash
ls -lh "$RESULT_DIR/000_logger_test.log"
```

---

# 4. GPU telemetry logger used during benchmarks

We want utilization, memory usage, power, temperature and clocks during each benchmark.

Paste this on both nodes:

```bash
start_gpu_telemetry() {
  local label="$1"

  nvidia-smi dmon \
    -s pcu \
    -d 1 \
    -o DT \
    -f "$RESULT_DIR/${label}_nvsmi_dmon.log" \
    >/dev/null 2>&1 &
  export DMON_PID=$!

  (
    while true; do
      nvidia-smi \
        --query-gpu=timestamp,index,name,pstate,utilization.gpu,utilization.memory,memory.used,memory.total,power.draw,temperature.gpu,clocks.sm,clocks.mem \
        --format=csv,noheader,nounits
      sleep 1
    done
  ) > "$RESULT_DIR/${label}_gpu_query.csv" 2>&1 &
  export GPUQUERY_PID=$!
}

stop_gpu_telemetry() {
  if [ -n "${DMON_PID:-}" ]; then
    kill "$DMON_PID" 2>/dev/null || true
    wait "$DMON_PID" 2>/dev/null || true
  fi
  if [ -n "${GPUQUERY_PID:-}" ]; then
    kill "$GPUQUERY_PID" 2>/dev/null || true
    wait "$GPUQUERY_PID" 2>/dev/null || true
  fi
  unset DMON_PID GPUQUERY_PID
}
```

Usage:

```bash
start_gpu_telemetry test_name
run_logged test_name 'COMMAND HERE'
stop_gpu_telemetry
```

> For short tests (<1 s), telemetry may not sample enough points.  
> NCCL test sweeps and compute/memory loops are intentionally long enough to generate useful telemetry.

---

# 5. P0 — Full system inventory and topology

Run on **both nodes**.

```bash
run_logged 010_system_inventory '
echo "===== HOST ====="
hostname -f
date --iso-8601=seconds

echo "===== GCP ZONE ====="
curl -s -H "Metadata-Flavor: Google" \
  http://metadata.google.internal/computeMetadata/v1/instance/zone || true

echo "===== OS ====="
uname -a
cat /etc/os-release

echo "===== NVIDIA-SMI ====="
nvidia-smi

echo "===== GPU LIST ====="
nvidia-smi -L

echo "===== GPU TOPOLOGY ====="
nvidia-smi topo -m

echo "===== NUMA ====="
numactl -H || true

echo "===== CPU ====="
lscpu

echo "===== PCI TREE ====="
lspci -tv

echo "===== PCI GPU/NIC DEVICES ====="
lspci -nn | egrep -i "NVIDIA|Ethernet|Network"

echo "===== NETWORK ====="
ip -br addr
ip -br link
ip route

echo "===== DRIVER/CUDA ====="
nvidia-smi --query-gpu=driver_version --format=csv,noheader | head -1
nvcc --version || true

echo "===== NCCL ====="
ldconfig -p | grep -i nccl || true
dpkg -l | grep -i nccl || true

echo "===== ENV NCCL/CUDA ====="
env | egrep "^(NCCL|CUDA|UCX|OMPI|FI_|LD_LIBRARY_PATH|PATH)=" | sort || true
'
```

Detailed PCI report:

```bash
run_logged 011_nvidia_pci 'nvidia-smi -q -d PCI'
```

Power / clocks / limits:

```bash
run_logged 012_gpu_power_clock_info 'nvidia-smi -q -d POWER,CLOCK,PERFORMANCE,TEMPERATURE,MEMORY'
```

---

# 6. Identify the 4-GPU NUMA islands

Inspect:

```bash
grep -A30 -B5 -i "TOPOLOGY" "$RESULT_DIR/010_system_inventory.log"
```

From `nvidia-smi topo -m`, set the actual GPU groups.

**Example only — do not assume this mapping:**

```bash
export NUMA0_GPUS=0,1,2,3
export NUMA1_GPUS=4,5,6,7
```

Log what was selected:

```bash
log_note "NUMA0_GPUS=$NUMA0_GPUS ; NUMA1_GPUS=$NUMA1_GPUS"
```

---

# 7. Install benchmark dependencies

Run on both nodes:

```bash
run_logged 020_install_packages '
sudo apt-get update &&
sudo apt-get install -y \
  git build-essential cmake \
  openmpi-bin libopenmpi-dev \
  iperf3 numactl pciutils ethtool iproute2 jq
'
```

Record tool versions:

```bash
run_logged 021_tool_versions '
git --version
gcc --version
g++ --version
cmake --version
mpirun --version
iperf3 --version
nvcc --version
'
```

---

# 8. Build NVIDIA NVBandwidth

Run on both nodes:

```bash
run_logged 030_clone_nvbandwidth '
cd "$BENCH_ROOT" &&
if [ ! -d nvbandwidth/.git ]; then
  git clone https://github.com/NVIDIA/nvbandwidth.git
fi &&
cd nvbandwidth &&
git rev-parse HEAD
'
```

Build:

```bash
run_logged 031_build_nvbandwidth '
cd "$BENCH_ROOT/nvbandwidth" &&
cmake -S . -B build &&
cmake --build build -j"$(nproc)"
'
```

Find binary:

```bash
run_logged 032_nvbandwidth_help '
cd "$BENCH_ROOT/nvbandwidth" &&
(find . -type f -name nvbandwidth -perm -111 -print) &&
BIN=$(find . -type f -name nvbandwidth -perm -111 | head -1) &&
"$BIN" --version &&
"$BIN" -l
'
```

For the following sections:

```bash
export NVBW_BIN=$(find "$BENCH_ROOT/nvbandwidth" -type f -name nvbandwidth -perm -111 | head -1)
echo "$NVBW_BIN"
```

Log it:

```bash
log_note "NVBW_BIN=$NVBW_BIN"
```

---

# 9. P0 — PCIe / P2P / host↔GPU memory measurements

## 9.1 Host → GPU and GPU → Host

```bash
start_gpu_telemetry 040_nvbandwidth_host_gpu
run_logged 040_nvbandwidth_host_gpu '
"$NVBW_BIN" \
  -t host_to_device_memcpy_ce device_to_host_memcpy_ce \
  -i 10 \
  --format json
'
stop_gpu_telemetry
```

## 9.2 Full GPU↔GPU bandwidth family

```bash
start_gpu_telemetry 041_nvbandwidth_d2d
run_logged 041_nvbandwidth_d2d '
"$NVBW_BIN" \
  -p device_to_device \
  -i 10 \
  --format json
'
stop_gpu_telemetry
```

## 9.3 GPU↔GPU latency

```bash
start_gpu_telemetry 042_nvbandwidth_d2d_latency
run_logged 042_nvbandwidth_d2d_latency '
"$NVBW_BIN" \
  -t device_to_device_latency_sm \
  -i 20 \
  --format json
'
stop_gpu_telemetry
```

## 9.4 Save text output as well for easy human reading

```bash
run_logged 043_nvbandwidth_d2d_text '
"$NVBW_BIN" \
  -p device_to_device \
  -i 5
'
```

**Model inputs to extract later:**

- same-NUMA GPU↔GPU GB/s
- cross-NUMA GPU↔GPU GB/s
- same-NUMA latency
- cross-NUMA latency
- H2D GB/s
- D2H GB/s

---

# 10. P0 — GPU local DRAM bandwidth with BabelStream

NVBandwidth is excellent for PCIe/P2P paths, but we also need the **local GDDR7 bandwidth ceiling**.

Clone:

```bash
run_logged 050_clone_babelstream '
cd "$BENCH_ROOT" &&
if [ ! -d BabelStream/.git ]; then
  git clone https://github.com/UoB-HPC/BabelStream.git
fi &&
cd BabelStream &&
git rev-parse HEAD
'
```

Build CUDA version:

```bash
run_logged 051_build_babelstream '
cd "$BENCH_ROOT/BabelStream" &&
rm -rf build_cuda &&
cmake -S . -B build_cuda \
  -DMODEL=cuda \
  -DCMAKE_CUDA_COMPILER="$(which nvcc)" &&
cmake --build build_cuda -j"$(nproc)"
'
```

Find executable:

```bash
run_logged 052_babelstream_help '
cd "$BENCH_ROOT/BabelStream" &&
find build_cuda -type f -name "cuda-stream" -perm -111 -print
'
```

Set:

```bash
export BABEL_BIN=$(find "$BENCH_ROOT/BabelStream/build_cuda" -type f -name cuda-stream -perm -111 | head -1)
log_note "BABEL_BIN=$BABEL_BIN"
```

Run GPU 0:

```bash
start_gpu_telemetry 053_babelstream_gpu0
run_logged 053_babelstream_gpu0 '
CUDA_VISIBLE_DEVICES=0 "$BABEL_BIN"
'
stop_gpu_telemetry
```

Run one GPU from the other NUMA island:

```bash
export NUMA1_FIRST_GPU=$(echo "$NUMA1_GPUS" | cut -d, -f1)

start_gpu_telemetry 054_babelstream_numa1_gpu
run_logged 054_babelstream_numa1_gpu '
CUDA_VISIBLE_DEVICES='"$NUMA1_FIRST_GPU"' "$BABEL_BIN"
'
stop_gpu_telemetry
```

Optional all-8 concurrent stress:

```bash
start_gpu_telemetry 055_babelstream_all8
run_logged 055_babelstream_all8 '
for g in 0 1 2 3 4 5 6 7; do
  CUDA_VISIBLE_DEVICES=$g "$BABEL_BIN" \
    > "$RESULT_DIR/babel_gpu${g}.txt" 2>&1 &
done
wait
cat "$RESULT_DIR"/babel_gpu*.txt
'
stop_gpu_telemetry
```

**Use `Copy`, `Add`, `Triad`, `Dot` MB/s as local DRAM-bandwidth references.**

This is a **memory roof**, not Kimi throughput.

---

# 11. Build NCCL tests

Run on both nodes.

Check headers:

```bash
run_logged 060_check_nccl_headers '
ls -l /usr/include/nccl.h 2>/dev/null || true
find /usr -name nccl.h 2>/dev/null | head -20
'
```

Install development headers only if required:

```bash
run_logged 061_install_nccl_dev_if_needed '
if ! find /usr -name nccl.h 2>/dev/null | grep -q nccl.h; then
  sudo apt-get install -y libnccl2 libnccl-dev
fi
'
```

Clone/build:

```bash
run_logged 062_clone_nccl_tests '
cd "$BENCH_ROOT" &&
if [ ! -d nccl-tests/.git ]; then
  git clone https://github.com/NVIDIA/nccl-tests.git
fi &&
cd nccl-tests &&
git rev-parse HEAD
'
```

```bash
run_logged 063_build_nccl_tests '
cd "$BENCH_ROOT/nccl-tests" &&
make -j"$(nproc)" MPI=1 MPI_HOME=/usr
'
```

Verify binaries:

```bash
run_logged 064_list_nccl_binaries '
ls -lh "$BENCH_ROOT/nccl-tests/build/"*perf
'
```

---

# 12. NCCL baseline environment

For GCP 8-GPU G4:

```bash
export NCCL_P2P_LEVEL=SYS
```

Find interface used to reach peer:

```bash
export IFACE=$(ip route get "$PEER_IP" \
  | awk '{for(i=1;i<=NF;i++) if($i=="dev"){print $(i+1); exit}}')
export NCCL_SOCKET_IFNAME="=$IFACE"
```

Log:

```bash
log_note "NCCL_P2P_LEVEL=$NCCL_P2P_LEVEL ; IFACE=$IFACE ; NCCL_SOCKET_IFNAME=$NCCL_SOCKET_IFNAME"
```

---

# 13. P0 — NCCL TP4 vs TP8 all-reduce

NCCL `algbw` is useful for the model because:

```text
algbw = message_size / operation_time
```

`busbw` is useful for interconnect efficiency comparison.

For prediction, we will primarily use **operation time** and **algbw**.

## 13.1 TP4 — small messages: decode / low-batch regime

```bash
start_gpu_telemetry 070_ar4_small
run_logged 070_ar4_small '
cd "$BENCH_ROOT/nccl-tests" &&
CUDA_VISIBLE_DEVICES='"$NUMA0_GPUS"' \
NCCL_P2P_LEVEL=SYS \
./build/all_reduce_perf \
  -b 8 -e 1M -f 2 -g 4
'
stop_gpu_telemetry
```

## 13.2 TP4 — large messages: prefill regime

```bash
start_gpu_telemetry 071_ar4_large
run_logged 071_ar4_large '
cd "$BENCH_ROOT/nccl-tests" &&
CUDA_VISIBLE_DEVICES='"$NUMA0_GPUS"' \
NCCL_P2P_LEVEL=SYS \
./build/all_reduce_perf \
  -b 1M -e 512M -f 2 -g 4
'
stop_gpu_telemetry
```

## 13.3 TP8 — small messages

```bash
start_gpu_telemetry 072_ar8_small
run_logged 072_ar8_small '
cd "$BENCH_ROOT/nccl-tests" &&
NCCL_P2P_LEVEL=SYS \
./build/all_reduce_perf \
  -b 8 -e 1M -f 2 -g 8
'
stop_gpu_telemetry
```

## 13.4 TP8 — large messages

```bash
start_gpu_telemetry 073_ar8_large
run_logged 073_ar8_large '
cd "$BENCH_ROOT/nccl-tests" &&
NCCL_P2P_LEVEL=SYS \
./build/all_reduce_perf \
  -b 1M -e 512M -f 2 -g 8
'
stop_gpu_telemetry
```

---

# 14. P0 — exact Kimi-model-relevant NCCL message sizes

Using hidden size ≈7168 and a BF16-like hidden tensor, useful reference payloads are approximately:

| Workload proxy | Payload |
|---|---:|
| Decode batch 1 | ~16 KiB test point |
| Decode batch 8 | ~128 KiB |
| Decode batch 32 | ~512 KiB |
| 4K prefill chunk | ~64 MiB |
| 8K prefill chunk | ~128 MiB |
| 16K prefill chunk | ~256 MiB |

Run both TP4 and TP8:

```bash
start_gpu_telemetry 074_ar_exact_sizes
run_logged 074_ar_exact_sizes '
cd "$BENCH_ROOT/nccl-tests" &&
for S in 16K 128K 512K 64M 128M 256M; do
  echo
  echo "========== TP4 $S =========="
  CUDA_VISIBLE_DEVICES='"$NUMA0_GPUS"' \
  NCCL_P2P_LEVEL=SYS \
  ./build/all_reduce_perf -b $S -e $S -g 4

  echo
  echo "========== TP8 $S =========="
  NCCL_P2P_LEVEL=SYS \
  ./build/all_reduce_perf -b $S -e $S -g 8
done
'
stop_gpu_telemetry
```

---

# 15. P1 — AllGather and ReduceScatter reference curves

Current/future TP implementations can use AllReduce directly or decompose communication into ReduceScatter + AllGather.

Characterize all three so the performance model is not tied to one implementation.

TP8 first:

```bash
start_gpu_telemetry 080_ar_ag_rs_tp8
run_logged 080_ar_ag_rs_tp8 '
cd "$BENCH_ROOT/nccl-tests" &&
for exe in all_reduce_perf all_gather_perf reduce_scatter_perf; do
  echo
  echo "========== $exe / TP8 =========="
  NCCL_P2P_LEVEL=SYS \
  ./build/$exe -b 16K -e 256M -f 2 -g 8
done
'
stop_gpu_telemetry
```

TP4:

```bash
start_gpu_telemetry 081_ar_ag_rs_tp4
run_logged 081_ar_ag_rs_tp4 '
cd "$BENCH_ROOT/nccl-tests" &&
for exe in all_reduce_perf all_gather_perf reduce_scatter_perf; do
  echo
  echo "========== $exe / TP4 =========="
  CUDA_VISIBLE_DEVICES='"$NUMA0_GPUS"' \
  NCCL_P2P_LEVEL=SYS \
  ./build/$exe -b 16K -e 256M -f 2 -g 4
done
'
stop_gpu_telemetry
```

---

# 16. P1 — isolate GCP cross-NUMA P2P benefit

This is useful because GCP G4's enhanced PCIe P2P may be better than the local OEM server.

## 16.1 Recommended GCP mode

```bash
start_gpu_telemetry 090_ar8_p2p_SYS
run_logged 090_ar8_p2p_SYS '
cd "$BENCH_ROOT/nccl-tests" &&
NCCL_P2P_LEVEL=SYS \
./build/all_reduce_perf -b 16K -e 256M -f 2 -g 8
'
stop_gpu_telemetry
```

## 16.2 Restrict P2P distance

```bash
start_gpu_telemetry 091_ar8_p2p_PHB
run_logged 091_ar8_p2p_PHB '
cd "$BENCH_ROOT/nccl-tests" &&
NCCL_P2P_LEVEL=PHB \
./build/all_reduce_perf -b 16K -e 256M -f 2 -g 8
'
stop_gpu_telemetry
```

## 16.3 Disable P2P — diagnostic bound only

```bash
start_gpu_telemetry 092_ar8_p2p_OFF
run_logged 092_ar8_p2p_OFF '
cd "$BENCH_ROOT/nccl-tests" &&
NCCL_P2P_DISABLE=1 \
./build/all_reduce_perf -b 16K -e 256M -f 2 -g 8
'
stop_gpu_telemetry
```

> P2P-off is **not** a literal emulation of the local server.  
> It provides a lower-bound / host-bounce sensitivity point.

---

# 17. P0 — raw node-to-node network

Node 1:

```bash
run_logged 100_start_iperf_server 'iperf3 -s -D'
```

Node 0:

```bash
run_logged 101_ping_node1 'ping -c 100 "$NODE1_IP"'
```

```bash
run_logged 102_iperf_P1 'iperf3 -c "$NODE1_IP" -t 30 -P 1'
```

```bash
run_logged 103_iperf_P8 'iperf3 -c "$NODE1_IP" -t 30 -P 8'
```

```bash
run_logged 104_iperf_P32 'iperf3 -c "$NODE1_IP" -t 30 -P 32'
```

```bash
run_logged 105_iperf_reverse 'iperf3 -c "$NODE1_IP" -t 30 -P 32 -R'
```

Record NIC state:

```bash
run_logged 106_nic_details '
ip -s link show dev "$IFACE"
ethtool "$IFACE" || true
ethtool -S "$IFACE" || true
'
```

---

# 18. MPI / SSH prerequisite

From Node 0:

```bash
run_logged 110_ssh_peer 'ssh -o BatchMode=yes "$NODE1_IP" hostname -f'
```

If it fails, configure project-approved SSH / OS Login first.

Create host file on Node 0:

```bash
cat > "$BENCH_ROOT/hosts" <<EOF
$NODE0_IP slots=8
$NODE1_IP slots=8
EOF
```

Log:

```bash
run_logged 111_show_hostfile 'cat "$BENCH_ROOT/hosts"'
```

MPI sanity:

```bash
run_logged 112_mpi_hostname '
mpirun \
  --hostfile "$BENCH_ROOT/hosts" \
  -np 2 --map-by ppr:1:node --bind-to none \
  hostname -f
'
```

---

# 19. P0 — cross-node NCCL send/recv: PP-boundary proxy

This is the most useful synthetic network test for PP.

## 19.1 Native GCP

```bash
start_gpu_telemetry 120_sendrecv_native
run_logged 120_sendrecv_native '
cd "$BENCH_ROOT/nccl-tests" &&
mpirun \
  --hostfile "$BENCH_ROOT/hosts" \
  -np 2 --map-by ppr:1:node --bind-to none \
  -x PATH -x LD_LIBRARY_PATH \
  -x NCCL_SOCKET_IFNAME \
  -x NCCL_DEBUG=WARN \
  ./build/sendrecv_perf \
  -b 8 -e 256M -f 2 -g 1
'
stop_gpu_telemetry
```

## 19.2 Exact Kimi-like sizes

```bash
start_gpu_telemetry 121_sendrecv_exact_native
run_logged 121_sendrecv_exact_native '
cd "$BENCH_ROOT/nccl-tests" &&
for S in 16K 128K 512K 64M 128M 256M; do
  echo
  echo "========== SENDRECV $S =========="
  mpirun \
    --hostfile "$BENCH_ROOT/hosts" \
    -np 2 --map-by ppr:1:node --bind-to none \
    -x PATH -x LD_LIBRARY_PATH \
    -x NCCL_SOCKET_IFNAME \
    -x NCCL_DEBUG=WARN \
    ./build/sendrecv_perf -b $S -e $S -g 1
done
'
stop_gpu_telemetry
```

---

# 20. P0 — emulate the local 20 Gb/s and 10 Gb/s fabric

The local system reports `2 × 10 GbE` per node, but we do not yet know whether a PP flow receives:

- ~10 Gb/s effective bandwidth, or
- ~20 Gb/s through bonding/striping.

Therefore test both.

> **WARNING:** traffic shaping affects the chosen NIC, including SSH.  
> Run this only on disposable benchmark VMs and keep the GCP console available.

Confirm interface:

```bash
run_logged 130_route_to_peer 'ip route get "$PEER_IP"'
```

Save qdisc:

```bash
run_logged 131_qdisc_before 'sudo tc qdisc show dev "$IFACE"'
```

## 20.1 20 Gb/s cap — run on BOTH nodes

```bash
run_logged 132_set_20g_cap '
sudo tc qdisc replace dev "$IFACE" root handle 1: htb default 10 &&
sudo tc class replace dev "$IFACE" parent 1: classid 1:10 \
  htb rate 20gbit ceil 20gbit
'
```

Node 0 sanity:

```bash
run_logged 133_iperf_20g 'iperf3 -c "$NODE1_IP" -t 20 -P 16'
```

Node 0 NCCL:

```bash
start_gpu_telemetry 134_sendrecv_20g
run_logged 134_sendrecv_20g '
cd "$BENCH_ROOT/nccl-tests" &&
mpirun \
  --hostfile "$BENCH_ROOT/hosts" \
  -np 2 --map-by ppr:1:node --bind-to none \
  -x PATH -x LD_LIBRARY_PATH \
  -x NCCL_SOCKET_IFNAME \
  -x NCCL_DEBUG=WARN \
  ./build/sendrecv_perf -b 8 -e 256M -f 2 -g 1
'
stop_gpu_telemetry
```

## 20.2 10 Gb/s cap — run on BOTH nodes

```bash
run_logged 135_set_10g_cap '
sudo tc class replace dev "$IFACE" parent 1: classid 1:10 \
  htb rate 10gbit ceil 10gbit
'
```

Node 0 sanity:

```bash
run_logged 136_iperf_10g 'iperf3 -c "$NODE1_IP" -t 20 -P 16'
```

Node 0 NCCL:

```bash
start_gpu_telemetry 137_sendrecv_10g
run_logged 137_sendrecv_10g '
cd "$BENCH_ROOT/nccl-tests" &&
mpirun \
  --hostfile "$BENCH_ROOT/hosts" \
  -np 2 --map-by ppr:1:node --bind-to none \
  -x PATH -x LD_LIBRARY_PATH \
  -x NCCL_SOCKET_IFNAME \
  -x NCCL_DEBUG=WARN \
  ./build/sendrecv_perf -b 8 -e 256M -f 2 -g 1
'
stop_gpu_telemetry
```

Also exact large transfer sizes at 10 Gb/s:

```bash
start_gpu_telemetry 138_sendrecv_10g_exact
run_logged 138_sendrecv_10g_exact '
cd "$BENCH_ROOT/nccl-tests" &&
for S in 64M 128M 256M; do
  echo "========== 10G SENDRECV $S =========="
  mpirun \
    --hostfile "$BENCH_ROOT/hosts" \
    -np 2 --map-by ppr:1:node --bind-to none \
    -x PATH -x LD_LIBRARY_PATH \
    -x NCCL_SOCKET_IFNAME \
    -x NCCL_DEBUG=WARN \
    ./build/sendrecv_perf -b $S -e $S -g 1
done
'
stop_gpu_telemetry
```

Remove shaping on BOTH nodes:

```bash
run_logged 139_remove_tc_cap 'sudo tc qdisc del dev "$IFACE" root || true'
```

Verify:

```bash
run_logged 140_qdisc_after 'sudo tc qdisc show dev "$IFACE"'
```

Sanity limits:

```text
10 Gb/s raw line rate = 1.25 GB/s before overhead
20 Gb/s raw line rate = 2.50 GB/s before overhead
```

If `iperf3` exceeds the cap materially, the shaping is on the wrong interface.

---

# 21. P1 — cross-node AllReduce stress test

This is **not** the current local TP8/PP3 design.
It is a reference showing what happens if TP is allowed to span Ethernet.

Native:

```bash
start_gpu_telemetry 150_ar16_native
run_logged 150_ar16_native '
cd "$BENCH_ROOT/nccl-tests" &&
mpirun \
  --hostfile "$BENCH_ROOT/hosts" \
  -np 2 --map-by ppr:1:node --bind-to none \
  -x PATH -x LD_LIBRARY_PATH \
  -x NCCL_SOCKET_IFNAME \
  -x NCCL_P2P_LEVEL=SYS \
  -x NCCL_DEBUG=WARN \
  ./build/all_reduce_perf \
  -b 16K -e 256M -f 2 -g 8
'
stop_gpu_telemetry
```

Repeat at 20 Gb/s and 10 Gb/s only if lab time permits, using Section 20's shaping steps.

---

# 22. P1 — NVIDIA CUTLASS compute reference

This section measures **GEMM compute behavior**, not Kimi MXFP4 kernel performance.

Use it for:
- large GEMM throughput ceiling
- skinny-vs-large GEMM shape sensitivity
- checking whether clocks/power/compute behave normally

**Do not use BF16/FP16 CUTLASS results as a claim for K3 MXFP4 throughput.**

Check CUDA version first:

```bash
run_logged 160_cuda_version_for_cutlass 'nvcc --version'
```

Clone CUTLASS:

```bash
run_logged 161_clone_cutlass '
cd "$BENCH_ROOT" &&
if [ ! -d cutlass/.git ]; then
  git clone https://github.com/NVIDIA/cutlass.git
fi &&
cd cutlass &&
git rev-parse HEAD
'
```

Build profiler for SM120:

```bash
run_logged 162_build_cutlass_profiler '
cd "$BENCH_ROOT/cutlass" &&
rm -rf build_sm120 &&
cmake -S . -B build_sm120 \
  -DCUTLASS_NVCC_ARCHS=120a \
  -DCUTLASS_ENABLE_TESTS=OFF \
  -DCUTLASS_UNITY_BUILD_ENABLED=ON &&
cmake --build build_sm120 --target cutlass_profiler -j"$(nproc)"
'
```

Device info:

```bash
run_logged 163_cutlass_device_info '
"$BENCH_ROOT/cutlass/build_sm120/tools/profiler/cutlass_profiler" \
  --device-info
'
```

Check available Tensor Core kernels:

```bash
run_logged 164_cutlass_enumerate '
"$BENCH_ROOT/cutlass/build_sm120/tools/profiler/cutlass_profiler" \
  --mode=enumerate \
  --operation=gemm | head -200
'
```

## 22.1 Large BF16/FP16 GEMM reference

Use a large shape to approach compute saturation:

```bash
start_gpu_telemetry 165_cutlass_large_gemm
run_logged 165_cutlass_large_gemm '
CUDA_VISIBLE_DEVICES=0 \
"$BENCH_ROOT/cutlass/build_sm120/tools/profiler/cutlass_profiler" \
  --operation=gemm \
  --op_class=tensorop \
  --A=f16:row \
  --B=f16:column \
  --C=f32 \
  --accum=f32 \
  --m=8192 --n=8192 --k=8192 \
  --profiling-iterations=20 \
  --output="$RESULT_DIR/cutlass_large_gemm"
'
stop_gpu_telemetry
```

## 22.2 Kimi-width shape sensitivity

K3 hidden width is ~7168. Sweep M to represent decode/small batch through prefill-like matrix sizes:

```bash
start_gpu_telemetry 166_cutlass_kimi_width_sweep
run_logged 166_cutlass_kimi_width_sweep '
CUDA_VISIBLE_DEVICES=0 \
"$BENCH_ROOT/cutlass/build_sm120/tools/profiler/cutlass_profiler" \
  --operation=gemm \
  --op_class=tensorop \
  --A=f16:row \
  --B=f16:column \
  --C=f32 \
  --accum=f32 \
  --m=8,32,128,512,2048,8192 \
  --n=7168 \
  --k=7168 \
  --profiling-iterations=20 \
  --output="$RESULT_DIR/cutlass_kimi_width"
'
stop_gpu_telemetry
```

If a requested kernel shape is unsupported, **do not modify the test silently**.
Keep the failure log; it is useful.

---

# 23. P1 — optional DCGM profiling counters

If `dcgmi` is already installed:

```bash
run_logged 170_dcgm_version 'dcgmi --version'
```

List supported profile groups on GPU 0:

```bash
run_logged 171_dcgm_profile_list 'dcgmi profile -l -i 0'
```

Useful fields, if supported:

```text
1002  SM activity
1003  SM occupancy
1004  Tensor activity
1005  DRAM activity
1009  PCIe TX bytes
1010  PCIe RX bytes
```

Run:

```bash
run_logged 172_dcgm_dmon_help 'dcgmi dmon --help'
```

Then use the syntax shown by the installed version to stream those fields during:
- BabelStream
- TP8 all-reduce
- CUTLASS large GEMM

> DCGM syntax can vary by installed release.  
> **Do not install or upgrade DCGM just for this smoke test unless the lab owner approves it.**
> The benchmark remains valid without DCGM because NVBandwidth/NCCL/BabelStream/CUTLASS provide the primary quantitative data.

---

# 24. P1 — capture NCCL algorithm / topology decisions

One TP8 run:

```bash
start_gpu_telemetry 180_nccl_debug_tp8
run_logged 180_nccl_debug_tp8 '
cd "$BENCH_ROOT/nccl-tests" &&
NCCL_DEBUG=INFO \
NCCL_DEBUG_SUBSYS=INIT,GRAPH,NET \
NCCL_P2P_LEVEL=SYS \
./build/all_reduce_perf \
  -b 128M -e 128M -g 8
'
stop_gpu_telemetry
```

One cross-node sendrecv:

```bash
start_gpu_telemetry 181_nccl_debug_sendrecv
run_logged 181_nccl_debug_sendrecv '
cd "$BENCH_ROOT/nccl-tests" &&
mpirun \
  --hostfile "$BENCH_ROOT/hosts" \
  -np 2 --map-by ppr:1:node --bind-to none \
  -x PATH -x LD_LIBRARY_PATH \
  -x NCCL_SOCKET_IFNAME \
  -x NCCL_DEBUG=INFO \
  -x NCCL_DEBUG_SUBSYS=INIT,GRAPH,NET \
  ./build/sendrecv_perf -b 128M -e 128M -g 1
'
stop_gpu_telemetry
```

We want to record:

- P2P path selected
- algorithm selected
- channel count
- network interface
- socket transport selection
- warnings/fallbacks

---

# 25. Minimum test sequence if lab time is limited

Run in this exact order:

1. `010` inventory/topology
2. `040–043` NVBandwidth
3. `053–054` BabelStream
4. `070–074` TP4 / TP8 NCCL
5. `101–106` raw network
6. `120–121` native PP-like SendRecv
7. `133–139` 20G + 10G SendRecv
8. `080–081` AllGather / ReduceScatter
9. `090–092` SYS / PHB / P2P-off
10. `165–166` CUTLASS compute
11. `180–181` NCCL debug traces

If time is very short, **do not skip 1–7**.

---

# 26. How the measurements map to the 3-node Kimi model

## 26.1 TP model

Fit TP4 and TP8 separately:

```text
T_collective(S) = alpha + beta × S
```

Use:

- `16K / 128K / 512K` → latency-dominated region
- `64M / 128M / 256M` → bandwidth-dominated region

Primary outputs:

```text
alpha_TP4
BW_TP4
alpha_TP8
BW_TP8
TP8 / TP4 penalty
```

---

## 26.2 PP network model

From `sendrecv_perf`:

```text
T_PP(S) = alpha_NET + beta_NET × S
```

Fit curves for:

```text
native GCP
20 Gb/s
10 Gb/s
```

For the real 3-node Kimi TP8/PP3 cluster there are two remote PP boundaries.

The final model will compose two boundary costs and then account for overlap/pipeline scheduling.

---

## 26.3 CPU-offload model input

From NVBandwidth:

```text
H2D_GBps
D2H_GBps
```

These provide the physical lower-level bandwidth terms for CPU KV offload.

They **do not** include:
- LMCache / SimpleCPUOffloadConnector lookup time
- block allocation
- LRU/eviction
- page pinning policy
- scheduler preemption
- cache miss logic

Those require the real vLLM run.

---

## 26.4 GPU memory roof

From BabelStream:

```text
Copy GB/s
Add GB/s
Triad GB/s
Dot GB/s
```

Compare those numbers against the RTX PRO 6000 theoretical GDDR bandwidth to derive an empirical efficiency factor:

```text
eta_DRAM = measured_stream_bandwidth / theoretical_bandwidth
```

We can use that to bound weight-streaming / bandwidth-limited phases.

---

## 26.5 GPU compute roof

From CUTLASS:

```text
GFLOP/s or TFLOP/s by GEMM shape
```

We are most interested in the difference between:

```text
large M  -> prefill-like compute efficiency
small M  -> decode-like GEMM efficiency
```

Again: **this is BF16/FP16 reference compute, not K3 MXFP4 kernel throughput**.

---

# 27. Model decision rules

These are engineering gates, not vendor guarantees.

## TP4 vs TP8

At 128 MiB:

```text
R_BW = TP4 algbw / TP8 algbw
```

and compare 16 KiB operation latency.

Interpretation:

- **<10% TP4 advantage** → topology probably secondary
- **10–30%** → topology matters
- **30–50%** → TP4/PP6 should be a priority real-model A/B
- **>50% plus lower small-message latency** → strong evidence against TP8 across the dual-NUMA path

---

## Network sensitivity

At 64/128/256 MiB compare:

```text
native
20 Gb/s
10 Gb/s
```

If time scales closely with the imposed line rate, PP is bandwidth-limited.

If small 16/128/512 KiB messages also worsen materially, network latency affects decode / low-batch traffic too.

---

## Memory vs compute diagnosis

Use:

```text
BabelStream DRAM utilization / bandwidth
CUTLASS GEMM throughput
NCCL collective time
```

to build a simple roofline classification:

```text
compute-bound
device-memory-bound
PCIe/collective-bound
network-bound
```

for each synthetic phase.

---

# 28. What this test cannot prove

Do **not** claim the following from this smoke test:

- actual Kimi K3 tokens/sec
- actual 512K / 1M TTFT
- MXFP4 kernel efficiency
- KDA recurrent-state performance
- MLA attention performance
- vLLM scheduler efficiency
- actual CPU KV-offload cache hit/miss behavior
- LMCache performance

The smoke test tells us whether the **hardware-level assumptions** in the model are correct.

---

# 29. Package all results

On each node:

```bash
run_logged 200_final_tree '
echo "===== RESULT FILES ====="
find "$BENCH_ROOT/results/$RUN_ID" -maxdepth 3 -type f \
  -printf "%p %s bytes\n" | sort
'
```

Create archive:

```bash
run_logged 201_create_archive '
cd "$BENCH_ROOT" &&
tar -czf "rtx_g4_smoke_${RUN_ID}_${HOST_SHORT}.tgz" \
  "results/$RUN_ID"
'
```

Confirm:

```bash
run_logged 202_archive_info '
ls -lh "$BENCH_ROOT/rtx_g4_smoke_${RUN_ID}_${HOST_SHORT}.tgz" &&
sha256sum "$BENCH_ROOT/rtx_g4_smoke_${RUN_ID}_${HOST_SHORT}.tgz"
'
```

Return **both node archives**.

Also return a short text note with:

```text
GCP zone:
VM type:
Node0 internal IP:
Node1 internal IP:
Driver version:
CUDA version:
NCCL version:
CUTLASS commit:
NVBandwidth commit:
BabelStream commit:
NUMA0 GPU list:
NUMA1 GPU list:
Native GCP NIC/interface:
Native GCP iperf3 P1/P8/P32:
NETWORK_PROVENANCE values tested:
Any failed tests:
Any manual changes:
```

**Important:** all GCP network results remain tagged `GCP_NATIVE`, `GCP_CAPPED_20G`,
or `GCP_CAPPED_10G`. They must not be renamed or interpreted as `LOCAL_REAL`.

---

# 30. The most valuable numbers for the architecture model

If only a subset can be extracted, send these first:

```text
1. TP4 all-reduce time @ 16 KiB
2. TP8 all-reduce time @ 16 KiB
3. TP4 algbw/time @ 128 MiB
4. TP8 algbw/time @ 128 MiB
5. TP4 algbw/time @ 256 MiB
6. TP8 algbw/time @ 256 MiB
7. same-NUMA P2P GB/s + latency
8. cross-NUMA P2P GB/s + latency
9. H2D GB/s
10. D2H GB/s
11. native SendRecv time @ 128 MiB
12. 20 Gb/s SendRecv time @ 128 MiB
13. 10 Gb/s SendRecv time @ 128 MiB
14. ping RTT
15. BabelStream Copy/Triad GB/s
16. CUTLASS large-GEMM TFLOP/s
17. CUTLASS M=8/32/128 vs M=8192 GEMM throughput
18. GPU clocks / power while running
```

Those values are sufficient to replace most provisional hardware assumptions in the current TP8/PP3 versus TP4/PP6 Kimi model.

---

# 31. Expected architectural question answered by this run

After these measurements, the architecture team should be able to answer:

```text
A. Is TP8 materially slower than TP4 because TP8 crosses NUMA/socket domains?
B. How much of the local Kimi prefill cost can 10 GbE plausibly explain?
C. Is decode likely limited by collective latency rather than bandwidth?
D. What is the measured H2D/D2H ceiling for CPU KV offload?
E. What local GDDR bandwidth is actually sustainable?
F. What GEMM efficiency is achievable for large vs skinny shapes?
G. Is TP4/PP6 analytically justified before spending real Kimi lab time?
```

That is the purpose of this smoke-test suite.
