# DeepSeek V4.1 Characterization Results Directory

## Target Architecture & Model Specification
- **Model**: `deepseek-ai/DeepSeek-V4.1-Flash`
- **Revision**: `main` (pinned commit SHA upon launch)
- **Architecture**: Multi-Head Latent Attention (MLA) + DeepSeekMoE (routed + shared experts)
- **Total Layers**: 40 layers
- **Pipeline Parallel Partition**: `10, 10, 10, 10` across 4 stages (PP4)
- **Tensor Parallel**: TP4 per stage (4 GPUs per TP group)
- **Total GPUs**: 16x NVIDIA RTX PRO 6000 Blackwell (2 Nodes × 8 GPUs)
- **Network Shaping**: 20 Gbps rate cap (`tc HTB` on `ens3`)
- **MoE Backend**: FlashInfer CUTLASS / Triton

## Execution Command
```bash
# On Primary Node 0:
export MODEL="deepseek-ai/DeepSeek-V4.1-Flash"
export VLLM_PP_LAYER_PARTITION="10,10,10,10"
export OUT_ROOT="c:/Users/ayu23/OneDrive/Desktop/tpu/Performance_Intelligence_Platform/data/results/deepseek-ai_DeepSeek-V4.1-Flash"

# Run 20-minute TP4/PP4 Campaign:
bash scripts/run_20min_tp4pp4_campaign.sh <NODE1_IP>
```

## Isolation Guarantee
All benchmark outputs, Nsight traces, PyTorch Chrome profiles, and latency distributions for DeepSeek V4.1 will be written directly into this directory, guaranteeing that Kimi-Linear 48B empirical results remain 100% intact and unchanged.
