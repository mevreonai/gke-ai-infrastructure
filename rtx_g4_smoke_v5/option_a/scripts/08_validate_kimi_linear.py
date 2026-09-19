#!/usr/bin/env python3
"""
Fetch and record exact Kimi-Linear model provenance/config.
No performance inference is made here.
"""
import argparse, json, sys
from pathlib import Path

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="moonshotai/Kimi-Linear-48B-A3B-Instruct")
    ap.add_argument("--out", default="kimi_linear_provenance.json")
    args = ap.parse_args()

    try:
        from huggingface_hub import HfApi, hf_hub_download
    except Exception as e:
        raise SystemExit(f"huggingface_hub unavailable: {e}")

    api = HfApi()
    info = api.model_info(args.model)
    cfg_path = hf_hub_download(args.model, "config.json", revision=info.sha)
    cfg = json.loads(Path(cfg_path).read_text())

    lin = cfg.get("linear_attn_config", {})
    record = {
        "model": args.model,
        "resolved_revision": info.sha,
        "config": cfg,
        "surrogate_architecture_fields": {
            "hidden_size": cfg.get("hidden_size"),
            "num_hidden_layers": cfg.get("num_hidden_layers"),
            "num_experts": cfg.get("num_experts"),
            "num_experts_per_token": cfg.get("num_experts_per_token"),
            "moe_intermediate_size": cfg.get("moe_intermediate_size"),
            "model_max_length": cfg.get("model_max_length"),
            "kv_lora_rank": cfg.get("kv_lora_rank"),
            "q_lora_rank": cfg.get("q_lora_rank"),
            "qk_nope_head_dim": cfg.get("qk_nope_head_dim"),
            "qk_rope_head_dim": cfg.get("qk_rope_head_dim"),
            "v_head_dim": cfg.get("v_head_dim"),
            "kda_layers": lin.get("kda_layers"),
            "full_attn_layers": lin.get("full_attn_layers"),
            "kda_num_heads": lin.get("num_heads"),
            "kda_head_dim": lin.get("head_dim"),
            "short_conv_kernel_size": lin.get("short_conv_kernel_size"),
        },
        "inference_guardrail": (
            "Absolute latency/tokens-per-second from this 48B surrogate MUST NOT be "
            "scaled to Kimi K3 by parameter count. Only runtime mechanisms, trends, "
            "regime changes, ratios under matched scenarios, and backend behavior "
            "are eligible for transfer."
        ),
    }
    Path(args.out).write_text(json.dumps(record, indent=2))
    print(json.dumps(record["surrogate_architecture_fields"], indent=2))
    print(f"Wrote {args.out}")

if __name__ == "__main__":
    main()
