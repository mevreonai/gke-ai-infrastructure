# Disaggregated TPU vLLM Serving with llm-d on GKE

A modular, production-tested implementation of **Prefill/Decode (P/D) Disaggregation** on Google Cloud TPUs using **`llm-d`**, **vLLM**, and the **Kubernetes Gateway API Inference Extension**.

This repository tones down the official Google Cloud Next AI Infra Codelab (`screen2-advanced-inferencing-part-2`) into an accessible, cost-effective 2-node cluster that proves distributed cross-node KV-cache transfer without requiring expensive multi-slice reservations.

---

## 🏛️ Architecture

```
                       [ Client / Benchmark / Gradio ]
                                      │
                                      ▼ (HTTP Port 80)
                       [ GKE Inference Gateway ]
                                      │
                                      ▼
                      [ llm-d Routing Sidecar Proxy ]
                    ┌─────────────────┴─────────────────┐
 (1) Send Prompt    │                                   │ (3) Stream Output Tokens
                    ▼                                   ▼
        ┌───────────────────────┐           ┌───────────────────────┐
        │   vLLM Prefill Node   │           │   vLLM Decode Node    │
        │    (kv_producer)      │           │    (kv_consumer)      │
        │   1 Node (4 TPUs)     │           │   1 Node (4 TPUs)     │
        └───────────┬───────────┘           └───────────▲───────────┘
                    │                                   │
                    └──────── (2) KV Transfer ──────────┘
                            (Port 9100 / 9600)
                           High-Speed MTU 8896
```

### Key Engineering Features:
1. **Physical Decoupling:** Compute-dense prompt prefilling (`kv_producer`) is separated from memory-bound autoregressive token decoding (`kv_consumer`).
2. **Network KV Streaming:** vLLM's `TPUConnector` streams KV-cache state directly across nodes via dedicated TCP ports (`9100` for KV tensors, `9600` for TPU side-channel coordination).
3. **`llm-d` Routing Proxy:** Intercepts client prompts, orchestrates prefill completion, coordinates the KV handoff, and streams decoded tokens back to the user.
4. **Automated Cost Protection:** Integrated trap teardown deletes clusters and TPU nodes immediately upon exit.

---

## 🚀 Quickstart

### 1. Launch Automated 1-Click Deployment:
```powershell
cd disaggregated_tpu_llmd
.\run.ps1
```

### 2. Live Interactive Controls:
Once deployed, the script opens `http://localhost:8080` in your browser. From your terminal, you can interactively:
* **`[T]`**: Trigger a real-time TTFT and TPOT latency benchmark.
* **`[P]`**: Follow live Prefill logs (`kv_producer`).
* **`[D]`**: Follow live Decode logs (`kv_consumer`).
* **`[ENTER]`**: Gracefully terminate all cloud resources to stop billing.

### 3. Run Benchmark Manually:
```powershell
python client/benchmark_disaggregated.py
```

### 4. Emergency Teardown:
```powershell
.\cleanup.ps1
```
