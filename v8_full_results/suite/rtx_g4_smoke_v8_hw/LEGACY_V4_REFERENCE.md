# RTX PRO 6000 GCP 2-Node Smoke Test — V4
## End-to-end run, logging, summarization and analytical-model calibration

> **V8 audit warning:** the historical 2026-09-15 local NCCL TP4/TP8 logs used `NCCL_P2P_DISABLE=1` and `NCCL_SHM_DISABLE=1`. Those particular legacy NCCL numbers are forced-transport evidence and must not be treated as native. V8 native local NCCL explicitly clears all `NCCL_*` overrides before measurement.

**Purpose:** Use **2 GCP G4 nodes × 8 RTX PRO 6000 GPUs** to measure the hardware primitives needed to diagnose the separate **3-node / 24-GPU Kimi K3 vLLM deployment**.

This package deliberately runs **without Kimi K3**. It collects:

- GPU/CPU/NUMA/PCIe topology
- GPU↔GPU P2P bandwidth + latency
- CPU↔GPU H2D/D2H bandwidth
- GPU GDDR7 memory bandwidth
- TP4 vs TP8 NCCL AllReduce latency/bandwidth
- AllGather + ReduceScatter curves
- P2P `SYS` vs `PHB` vs P2P-disabled sensitivity
- node-to-node `iperf3`
- NCCL SendRecv as a PP-boundary proxy
- full network sweep at:
  - `GCP_NATIVE`
  - `GCP_CAPPED_100G`
  - `GCP_CAPPED_50G`
  - `GCP_CAPPED_20G`
  - `GCP_CAPPED_10G`
- optional CUTLASS compute roof
- GPU clocks, utilization, power and memory telemetry
- automatic CSV/JSON/Markdown summarization
- automatic alpha–beta / TP4-vs-TP8 / PP-network model analysis

---

# 1. Critical interpretation rule: GCP network ≠ local lab network

The GCP results have explicit provenance:

```text
GCP_NATIVE
GCP_CAPPED_100G
GCP_CAPPED_50G
GCP_CAPPED_20G
GCP_CAPPED_10G
LOCAL_REAL              # reserved for later local-lab measurements
```

**Never rename GCP data as LOCAL_REAL.**

Traffic capping means Linux `tc` limits egress bandwidth while the underlying GCP NIC, PCIe placement, TCP stack and fabric remain GCP's.

Therefore:

- capped GCP data is highly useful for the **serialization/bandwidth sensitivity (`beta`)**
- it does **not** reproduce the local 10GbE NIC's physical latency (`alpha`), queueing, NUMA affinity, DMA implementation, switch, MTU, RSS, offloads or firmware
- the final local Kimi model must replace GCP network inputs with real local `iperf3` + NCCL SendRecv data once available

Native GCP is also not to be labeled "400GbE measured". The automated sweep pins NCCL to the peer-facing interface used for the test, so `GCP_NATIVE` means **native throughput on that measured path**, not necessarily the VM's full aggregate network ceiling. G4 may support a high network ceiling, but **the benchmark result itself is the authority**.

---

# 2. Files in this package

```text
00_smoke_common.sh
    logging + GPU telemetry

01_prepare_node.sh
    inventory, dependencies and benchmark builds

02_run_node_local.sh
    NVBandwidth, BabelStream, NCCL TP4/TP8, AG/RS,
    P2P-policy sensitivity, optional CUTLASS

03_run_network_sweep.sh
    native + 100G + 50G + 20G + 10G
    iperf3 + NCCL SendRecv, with safe cleanup trap

04_summarize_results.py
    raw logs -> CSV + JSON + SUMMARY.md

05_analyze_model.py
    measured points -> MODEL_ANALYSIS.md

06_package_results.sh
    creates final .tgz
```

Every test produces:

- exact command
- hostname
- start/end timestamps
- stdout + stderr
- exit code
- a per-test `.log`
- one master log
- GPU telemetry files where relevant

---

# 3. Create the same script directory on BOTH nodes

Copy this entire package directory to both GCP nodes, for example:

```bash
mkdir -p ~/rtx_g4_smoke_v4
# copy files into ~/rtx_g4_smoke_v4/
cd ~/rtx_g4_smoke_v4
chmod +x *.sh *.py
```

---

# 4. Set environment on Node 0

```bash
export NODE0_IP=<NODE0_INTERNAL_IP>
export NODE1_IP=<NODE1_INTERNAL_IP>
export PEER_IP=$NODE1_IP

export BENCH_ROOT=$HOME/rtx_g4_smoke
export RUN_ID=$(date +%Y%m%d_%H%M%S)
export HOST_SHORT=$(hostname -s)
export RESULT_DIR=$BENCH_ROOT/results/$RUN_ID/$HOST_SHORT
```

**Record `RUN_ID`. Both nodes should use the same RUN_ID.**

Example:

```bash
echo "RUN_ID=$RUN_ID"
```

---

# 5. Set environment on Node 1

Use the **same RUN_ID copied from Node 0**:

```bash
export NODE0_IP=<NODE0_INTERNAL_IP>
export NODE1_IP=<NODE1_INTERNAL_IP>
export PEER_IP=$NODE0_IP

export BENCH_ROOT=$HOME/rtx_g4_smoke
export RUN_ID=<RUN_ID_FROM_NODE0>
export HOST_SHORT=$(hostname -s)
export RESULT_DIR=$BENCH_ROOT/results/$RUN_ID/$HOST_SHORT
```

---

# 6. Prepare both nodes

Run on **both nodes**:

```bash
cd ~/rtx_g4_smoke_v4
./01_prepare_node.sh
```

This may take time because it builds:

- NVIDIA NVBandwidth
- NVIDIA NCCL tests
- BabelStream
- CUTLASS profiler (default enabled)

To skip CUTLASS build:

```bash
export RUN_CUTLASS_BUILD=0
./01_prepare_node.sh
```

---

# 7. Determine the 4-GPU NUMA groups

On each node inspect:

```bash
nvidia-smi topo -m
numactl -H
```

Set the actual same-island GPU lists.

**Example only:**

```bash
export NUMA0_GPUS=0,1,2,3
export NUMA1_GPUS=4,5,6,7
```

Do not assume that example before checking the topology.

---

# 8. Run node-local benchmarks on both nodes

Run on **both nodes**:

```bash
cd ~/rtx_g4_smoke_v4
./02_run_node_local.sh
```

This collects the hardware model inputs independent of the GCP inter-node network.

Most important outputs:

```text
TP4 AllReduce @ 16K / 128M / 256M
TP8 AllReduce @ 16K / 128M / 256M
NVBandwidth H2D / D2H
same-NUMA P2P
cross-NUMA P2P
BabelStream GDDR bandwidth
CUTLASS large vs skinny GEMM
```

---

# 9. Configure Node 0 -> Node 1 noninteractive SSH

From Node 0:

```bash
ssh -o BatchMode=yes $NODE1_IP hostname
```

Must succeed without an interactive password.

The network sweep also needs noninteractive `sudo` for `tc` on both disposable benchmark nodes:

```bash
sudo -n true
ssh $NODE1_IP sudo -n true
```

If either fails, do **not** weaken security controls. Ask the project administrator to enable the approved benchmark path, or run the traffic-shaping steps manually.

---

# 10. Run the full network bandwidth sweep from Node 0

Node 0 only:

```bash
cd ~/rtx_g4_smoke_v4
./03_run_network_sweep.sh
```

The script runs, in order:

```text
GCP_NATIVE
100 Gb/s cap
50 Gb/s cap
20 Gb/s cap
10 Gb/s cap
```

At every condition it runs:

```text
iperf3 -P32
NCCL SendRecv:
    16K
    128K
    512K
    64M
    128M
    256M
```

A `trap` removes the custom cap even if the script exits abnormally. **Because replacing a root qdisc can change the VM's default qdisc, use disposable benchmark VMs and compare the logged pre/post qdisc state; recreate/reboot the VM after the sweep if you need the original networking state restored exactly.**

### Why these sizes?

Approximate K3 communication regimes:

```text
16K       decode batch ~1
128K      small decode batch
512K      larger decode batch
64M       ~4K-token prefill hidden-state scale
128M      ~8K-token prefill hidden-state scale
256M      ~16K-token prefill hidden-state scale
```

They are communication proxies, not claims about exact current vLLM tensor sizes.

---

# 11. What "capping to 10G" means

For the 10G pass, Linux traffic control effectively imposes:

```text
egress <= 10 Gb/s
```

on the peer-facing interface on **both nodes**.

The physical GCP networking underneath remains unchanged.

Therefore:

```text
GCP_CAPPED_10G
```

answers:

> How does this exact GCP software/network path respond when payload bandwidth is restricted to ~10 Gb/s?

It does **not** answer:

> What is the exact latency/performance of the team's physical 10GbE NIC?

The local lab test will later supply that.

---

# 12. Verify the caps from the logs

The script runs `iperf3` at every cap.

Approximate raw line ceilings:

```text
100 Gb/s = 12.50 GB/s
50 Gb/s  =  6.25 GB/s
20 Gb/s  =  2.50 GB/s
10 Gb/s  =  1.25 GB/s
```

Actual payload should be below those values.

If `iperf3` substantially exceeds the requested cap:

**do not use that capped NCCL result.**

The `tc` shaping likely did not apply to the traffic-bearing interface.

---

# 13. Combine Node 0 and Node 1 result directories

The easiest workflow is to copy Node 1's host directory into Node 0's same `RUN_ID` tree.

On Node 0:

```bash
mkdir -p "$BENCH_ROOT/results/$RUN_ID"
scp -r "$NODE1_IP:$BENCH_ROOT/results/$RUN_ID/"* \
  "$BENCH_ROOT/results/$RUN_ID/"
```

Verify:

```bash
find "$BENCH_ROOT/results/$RUN_ID" -maxdepth 2 -type f | sort | head -100
```

You should see directories/files from both hosts.

---

# 14. Automatically summarize all logs

On Node 0:

```bash
cd ~/rtx_g4_smoke_v4

python3 04_summarize_results.py \
  "$BENCH_ROOT/results/$RUN_ID" \
  --out "$BENCH_ROOT/results/$RUN_ID/summary"
```

Outputs:

```text
summary/SUMMARY.md
summary/summary.json
summary/nccl_points.csv
summary/iperf.csv
summary/nvbandwidth_metrics.csv
summary/babelstream.csv
summary/cutlass.csv
```

The summary script **never invents missing values**.
If a test failed or an output format could not be parsed, it remains missing and the original log stays authoritative.

---

# 15. Generate the architecture/model analysis

Basic:

```bash
python3 05_analyze_model.py \
  "$BENCH_ROOT/results/$RUN_ID/summary/summary.json" \
  --out "$BENCH_ROOT/results/$RUN_ID/summary/MODEL_ANALYSIS.md"
```

If you want to compare the GCP primitives with the currently observed local Kimi numbers:

```bash
python3 05_analyze_model.py \
  "$BENCH_ROOT/results/$RUN_ID/summary/summary.json" \
  --out "$BENCH_ROOT/results/$RUN_ID/summary/MODEL_ANALYSIS.md" \
  --local-tpot-ms 57.7 \
  --local-ttft-512-s 160 \
  --local-ttft-1m-s 900
```

Use the second command only if those local observations are still the numbers you want to compare against.

The analysis produces:

### TP4 vs TP8

```text
16K latency ratio
128M bandwidth ratio
256M bandwidth ratio
TP4/PP6 decision gate
```

### Network sensitivity

```text
Native / 100G / 50G / 20G / 10G
iperf throughput
16K SendRecv
128M SendRecv
256M SendRecv
```

### Alpha–beta fit

For each network condition:

```text
T(S) ≈ alpha + beta * S
```

and:

```text
fitted payload bandwidth = 1 / beta
```

### PP proxy

Using the fitted network curve and K3 hidden width:

```text
8K prefill hidden-state proxy
one PP boundary
two remote PP boundaries
512K network-only serialization proxy
1M network-only serialization proxy
```

### TP communication sensitivity

Because this synthetic test cannot know current vLLM's exact effective collective-equivalent count per K3 layer, it reports:

```text
K = 1
K = 1.5
K = 2
```

for both TP4 and TP8.

This is deliberate. The real Kimi profile later determines K/fusion/overlap.

---

# 16. How to interpret the generated analysis

## TP4 vs TP8

At 128 MiB:

```text
R = TP4 algbw / TP8 algbw
```

Suggested gate:

```text
<1.10×       topology probably secondary
1.10–1.30×   topology matters
1.30–1.50×   TP4/PP6 is high-priority real-model A/B
>1.50×       strong evidence against TP8 cross-domain communication
```

Also inspect 16K latency: prefill and decode can have different winners.

---

## Network

Large transfers should increasingly follow:

```text
T ~= alpha + size / bandwidth
```

If 128M/256M SendRecv scales approximately with the cap:

```text
100G -> 50G -> 20G -> 10G
```

then PP long-prefill traffic is bandwidth-sensitive.

If even 16K/128K changes sharply, software/network latency is also important.

---

## Memory

BabelStream provides the empirical local GDDR bandwidth roof.

NVBandwidth provides:

```text
GPU <-> GPU
CPU -> GPU
GPU -> CPU
```

These let the Kimi model separate:

```text
device-memory limit
PCIe/offload limit
collective limit
network limit
```

---

## Compute

CUTLASS gives a **reference compute roof** and shows how GEMM efficiency changes from small/skinny to large shapes.

It is **not** K3 MXFP4 performance.

Actual MXFP4, KDA and MLA kernels require the later Kimi/vLLM run.

---

# 17. Package everything

On Node 0:

```bash
export RUN_ID=<RUN_ID>
cd ~/rtx_g4_smoke_v4
./06_package_results.sh
```

Return:

```text
~/rtx_g4_smoke/rtx_g4_smoke_<RUN_ID>.tgz
```

The tarball contains:

- raw command logs
- exact commands
- stdout/stderr
- exit codes
- topology
- telemetry
- raw benchmark data
- CSV summaries
- JSON summary
- `SUMMARY.md`
- `MODEL_ANALYSIS.md`

---

# 18. What we should eventually repeat on the local 3-node cluster

The GCP sweep calibrates the theory, but the final model should replace these with `LOCAL_REAL`:

```text
local nvidia-smi topo -m
local TP4 AllReduce 16K / 128M / 256M
local TP8 AllReduce 16K / 128M / 256M
local H2D / D2H
local ping
local iperf P1/P8/P32
local SendRecv 16K / 128K / 512K / 64M / 128M / 256M
local NIC model
local NIC NUMA placement
local bonding mode
local MTU
local RSS / IRQ setup
local NCCL-selected network interface
```

Only then should `alpha_NET` and `BW_NET` in the production Kimi model be called authoritative.

---

# 19. What this end-to-end suite lets us answer before another Kimi run

After processing the data, we should be able to answer with measured evidence:

1. **How expensive is TP8 versus TP4 on RTX PRO 6000 G4 topology?**
2. **Is the penalty latency-dominated or bandwidth-dominated?**
3. **Does GCP's enhanced P2P hide a cross-NUMA penalty that could be worse locally?**
4. **How does PP-like communication respond from native bandwidth down to 10 Gb/s?**
5. **How much 10 Gb/s can plausibly contribute to 512K/1M TTFT?**
6. **What are the measured H2D/D2H ceilings for CPU KV offload?**
7. **What GDDR bandwidth is actually sustainable?**
8. **What is the reference compute efficiency for skinny vs large GEMM?**
9. **Is TP4/PP6 analytically justified before consuming local Kimi lab time?**
10. **Which remaining performance component requires an actual vLLM/K3 trace rather than more synthetic testing?**

That is the intended output of V4.
