import json
from types import SimpleNamespace
from pathlib import Path

def dict_to_sns(d):
    if isinstance(d, dict):
        return SimpleNamespace(**{k: dict_to_sns(v) for k, v in d.items()})
    elif isinstance(d, list):
        return [dict_to_sns(v) for v in d]
    return d

with open("/data/models/deepseek-v4.1-flash/config.json") as f:
    raw_cfg = json.load(f)

cfg = dict_to_sns(raw_cfg)

keys=['model_type','architectures','hidden_size','num_hidden_layers','num_attention_heads','num_key_value_heads',
      'max_position_embeddings','model_max_length','torch_dtype','dtype','n_routed_experts','num_experts','num_local_experts',
      'num_experts_per_tok','num_experts_per_token','moe_intermediate_size','index_n_heads','index_head_dim','index_topk',
      'q_lora_rank','o_lora_rank','head_dim','sliding_window','expert_dtype','kv_lora_rank','qk_nope_head_dim','qk_rope_head_dim','v_head_dim']

out={}
def add_from(obj,prefix=None):
    if obj is None: return
    for k in keys:
        v=getattr(obj,k,None)
        if v is None: continue
        key=k if prefix is None or k not in out else f'{prefix}.{k}'
        try: json.dumps(v); out[key]=v
        except Exception: out[key]=str(v)

add_from(cfg)
text_cfg=getattr(cfg,'text_config',None)
if text_cfg is not None:
    for k in keys:
        if k in out: continue
        v=getattr(text_cfg,k,None)
        if v is None: continue
        try: json.dumps(v); out[k]=v
        except Exception: out[k]=str(v)
    out['has_text_config']=True

qc=getattr(cfg,'quantization_config',None)
if qc is not None:
    try: qcd=qc.__dict__ if hasattr(qc, '__dict__') else qc
    except Exception: qcd={'raw':str(qc)}
    out['quantization_config']=qcd
    if isinstance(qcd,dict) and qcd.get('expert_dtype') is not None and out.get('expert_dtype') is None:
        out['expert_dtype']=qcd['expert_dtype']

print("FLATTENED CONFIG:")
print(json.dumps(out, indent=2))

with open("/home/ayu23/V9_FULL/configs/models/deepseek_v41_flash.json") as f:
    profile = json.load(f)

failures = []
for k, v in (profile.get('expected_config') or {}).items():
    av = out.get(k)
    if av != v:
        failures.append(f"{k}: expected {v!r}, got {av!r}")

print("FAILURES:", failures)
if not failures:
    print("ALL EXPECTED CONFIG VALUES MATCH 100% PERFECTLY!")
