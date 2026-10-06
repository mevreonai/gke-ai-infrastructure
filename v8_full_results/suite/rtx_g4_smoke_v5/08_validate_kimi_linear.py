#!/usr/bin/env python3
"""Resolve and freeze Kimi-Linear surrogate provenance at an exact HF revision."""
import argparse, json, sys, time
from pathlib import Path

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--model",default="moonshotai/Kimi-Linear-48B-A3B-Instruct")
    ap.add_argument("--revision",default=None,help="Expected revision. If set and different from resolved SHA, fail.")
    ap.add_argument("--out",default="kimi_linear_provenance_resolved.json")
    args=ap.parse_args()
    from huggingface_hub import HfApi, hf_hub_download
    api=HfApi(); info=api.model_info(args.model,revision=args.revision)
    sha=info.sha
    if args.revision and sha!=args.revision:
        raise SystemExit(f"Revision mismatch: requested {args.revision}, resolved {sha}")
    cfgp=hf_hub_download(args.model,"config.json",revision=sha); cfg=json.loads(Path(cfgp).read_text())
    lin=cfg.get("linear_attn_config",{})
    rec={
      "timestamp":time.time(),"model":args.model,"resolved_revision":sha,"config_path":cfgp,"config":cfg,
      "checkpoint_logical_dtype":cfg.get("dtype"),
      "surrogate_architecture_fields":{
        "hidden_size":cfg.get("hidden_size"),"num_hidden_layers":cfg.get("num_hidden_layers"),
        "num_experts":cfg.get("num_experts"),"num_experts_per_token":cfg.get("num_experts_per_token"),
        "moe_intermediate_size":cfg.get("moe_intermediate_size"),"model_max_length":cfg.get("model_max_length"),
        "kv_lora_rank":cfg.get("kv_lora_rank"),"q_lora_rank":cfg.get("q_lora_rank"),
        "qk_nope_head_dim":cfg.get("qk_nope_head_dim"),"qk_rope_head_dim":cfg.get("qk_rope_head_dim"),"v_head_dim":cfg.get("v_head_dim"),
        "kda_layers":lin.get("kda_layers"),"full_attn_layers":lin.get("full_attn_layers"),"kda_num_heads":lin.get("num_heads"),
        "kda_head_dim":lin.get("head_dim"),"short_conv_kernel_size":lin.get("short_conv_kernel_size")},
      "evidence_class":"MODEL-PROVENANCE",
      "guardrail":"This is Kimi-Linear-48B surrogate provenance, not Kimi K3 architecture provenance. Absolute performance must not be scaled to K3."
    }
    Path(args.out).write_text(json.dumps(rec,indent=2)); print(json.dumps(rec["surrogate_architecture_fields"],indent=2)); print(f"Wrote {args.out}")
if __name__=="__main__": main()
