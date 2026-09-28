# DeepSeek V4.1 Flash — Performance Characterization Suite

## Overview

This suite benchmarks **DeepSeek-V4.1-Flash** (`deepseek-ai/DeepSeek-V4.1-Flash`)
on a single **kimi-node-0** VM equipped with **8× NVIDIA RTX PRO 6000 Blackwell
Server Edition** (96 GB GDDR7 each, 768 GB total VRAM).

The model weights are pre-staged on GCS and mounted via GCS FUSE — no download
flags or model selection is needed. Every script is self-contained and
pre-configured.

### Network Conditions Tested

| Condition | Description |
|-----------|-------------|
| **Native** | Unrestricted PCIe Gen5 / VPC bandwidth (baseline) |
| **100 Gbps** | `tc` egress cap simulating 100 Gbps NIC |
| **20 Gbps** | `tc` egress cap simulating 20 Gbps standard tier |

---

## Hardware & Environment

| Component | Specification |
|-----------|---------------|
| VM | `kimi-node-0` (GCP `a3-megagpu-8g` equivalent) |
| GPUs | 8× NVIDIA RTX PRO 6000 Blackwell SE (96 GB GDDR7) |
| Interconnect | PCIe Gen5 x16 per GPU |
| System RAM | 1,920 GB DDR5 |
| NVMe | 2× 1 TB local SSD |
| Model Path | `/data/models/deepseek-v4.1-flash` |
| GCS Source | `gs://mevreon-deepseek-models/deepseek-ai/DeepSeek-V4.1-Flash` |
| Container | `vllm/vllm-openai:deepseekv41-flash-0909` |
| vLLM | `0.29.0` |

---

## Directory Structure

```
perf_characterization_scripts/
├── README.md                  # ← You are here
├── config.json                # Benchmark test-case definitions
├── 01_preflight.sh            # Environment validation (GPU, model, docker)
├── 02_start_vllm_server.sh    # Launch the vLLM inference server
├── 03_run_benchmarks.py       # Execute all benchmark cases across network conditions
├── 04_collect_results.py      # Aggregate results into CSV + summary markdown
└── run_all.sh                 # One-command end-to-end orchestrator
```

---

## Quick Start

### 1. SSH into kimi-node-0

```bash
gcloud compute ssh kimi-node-0 --zone us-central1-b
```

### 2. Clone / Copy the scripts

```bash
# From your local machine:
gcloud compute scp --recurse perf_characterization_scripts/ \
  kimi-node-0:~/perf_characterization_scripts/ --zone us-central1-b
```

### 3. Run Everything (one command)

```bash
cd ~/perf_characterization_scripts
chmod +x *.sh
sudo ./run_all.sh
```

This will:
1. Run preflight checks (GPU count, model weights, docker)
2. Start the vLLM server container
3. Run all benchmarks across **Native → 100Gbps → 20Gbps** conditions
4. Collect and summarize results into `results/` directory
5. Shut down the server

> **Note:** `sudo` is required for `tc` network shaping commands.

---

## Running Individual Steps

### Step 1: Preflight Validation

```bash
sudo ./01_preflight.sh
```

Checks:
- 8 GPUs detected via `nvidia-smi`
- Model weights exist at `/data/models/deepseek-v4.1-flash`
- GCS FUSE mount is active (or weights are locally synced)
- Docker and `docker compose` are available
- `tc` (traffic control) is available for network shaping

### Step 2: Start vLLM Server

```bash
sudo ./02_start_vllm_server.sh
```

Launches the vLLM server in a Docker container with:
- TP=8 (tensor parallelism across all 8 GPUs)
- DeepSeek V4.1 tokenizer mode
- Language-model-only mode (no vision)
- GPU memory utilization at 92%
- Listening on port 8000

The script waits until the `/v1/models` endpoint returns 200 before exiting.

### Step 3: Run Benchmarks

```bash
sudo python3 03_run_benchmarks.py
```

Runs the benchmark matrix defined in `config.json` across all three network
conditions. For each condition:
1. Applies network shaping via `tc` (or removes it for Native)
2. Runs each benchmark case via the OpenAI-compatible `/v1/completions` API
3. Saves raw JSON results per case

### Step 4: Collect Results

```bash
python3 04_collect_results.py
```

Parses all raw result JSONs and generates:
- `results/summary.csv` — One row per benchmark run
- `results/SUMMARY.md` — Markdown table with key metrics
- `results/comparison.json` — Machine-readable comparison across conditions

---

## Benchmark Matrix

The suite runs the following workloads (defined in `config.json`):

### TP8 Context Baseline (all 8 GPUs)

| Case | Input Tokens | Output Tokens | Concurrency | Prompts |
|------|-------------|---------------|-------------|---------|
| `8k_c1` | 8,192 | 256 | 1 | 12 |
| `8k_c8` | 8,192 | 256 | 8 | 32 |
| `128k_c1` | 131,072 | 128 | 1 | 5 |
| `512k_c1` | 524,288 | 64 | 1 | 3 |

### TP8 Decode Focus (high-output characterization)

| Case | Input Tokens | Output Tokens | Concurrency | Prompts |
|------|-------------|---------------|-------------|---------|
| `8k_decode_c1` | 8,192 | 512 | 1 | 8 |
| `8k_decode_c8` | 8,192 | 512 | 8 | 24 |

### TP8 Prefill Focus (TTFT isolation)

| Case | Input Tokens | Output Tokens | Concurrency | Prompts |
|------|-------------|---------------|-------------|---------|
| `8k_prefill` | 8,192 | 4 | 1 | 8 |
| `128k_prefill` | 131,072 | 4 | 1 | 5 |

Each of these 8 cases is run **3 times** (Native, 100Gbps, 20Gbps) = **24 total runs**.

---

## Network Shaping

Network bandwidth caps are applied using Linux `tc` (traffic control):

```bash
# Apply 100 Gbps cap:
tc qdisc replace dev eth0 root tbf rate 100gbit burst 256mb latency 1ms

# Apply 20 Gbps cap:
tc qdisc replace dev eth0 root tbf rate 20gbit burst 64mb latency 1ms

# Remove cap (restore Native):
tc qdisc del dev eth0 root 2>/dev/null || true
```

> Network shaping only affects inter-node traffic. Since we are running
> single-node TP8, the primary effect is on GCS FUSE model weight loading
> and any cross-NIC NCCL traffic if the system uses network-backed NCCL
> transports. The main purpose is to characterize sensitivity.

---

## Output Structure

```
results/
├── native/
│   ├── tp8_context_baseline/
│   │   ├── 8k_c1.json
│   │   ├── 8k_c8.json
│   │   ├── 128k_c1.json
│   │   └── 512k_c1.json
│   ├── tp8_decode_focus/
│   │   ├── 8k_decode_c1.json
│   │   └── 8k_decode_c8.json
│   └── tp8_prefill_focus/
│       ├── 8k_prefill.json
│       └── 128k_prefill.json
├── 100gbps/
│   └── ... (same structure)
├── 20gbps/
│   └── ... (same structure)
├── summary.csv
├── comparison.json
└── SUMMARY.md
```

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `nvidia-smi` shows < 8 GPUs | Reboot the VM or check GPU driver installation |
| Model weights missing at `/data/models/` | Run `gcloud storage rsync gs://mevreon-deepseek-models/deepseek-ai/DeepSeek-V4.1-Flash /data/models/deepseek-v4.1-flash` |
| vLLM server won't start | Check `docker logs vllm-deepseek` for OOM or CUDA errors |
| `tc` command not found | Install `iproute2`: `apt-get install -y iproute2` |
| Port 8000 already in use | Stop existing containers: `docker stop vllm-deepseek` |

---

## Contact

For questions about this characterization suite, refer to the parent project
documentation in the `rtx_g4_smoke_v5/` directory or contact the Mevreon
infrastructure team.
